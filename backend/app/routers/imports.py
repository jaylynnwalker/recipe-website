from io import BytesIO
import json
from pathlib import Path
import uuid
from urllib.parse import urlparse
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..ai import AIUnavailable, BudgetExceeded, RECIPE_SCHEMA, recipe_draft, run_structured
from ..importer import ImportFailure, empty_draft, extract_url, fetch_public_html, social_source_type, validate_external_url
from ..ingredient_parser import normalize_imported_draft
from ..models import ImportAsset, ImportJob, Recipe
from ..schemas import InboxUrlCreate, RecipeRead, RecipeWrite
from ..serializers import recipe_to_dict
from .recipes import ALLOWED_IMAGES, apply_recipe_payload, get_household_recipe

router = APIRouter(prefix='/inbox', tags=['recipe inbox'])


def job_options():
    return (selectinload(ImportJob.assets),)


def get_job(job_id: str, household_id: str, db: Session) -> ImportJob:
    job = db.scalar(select(ImportJob).options(*job_options()).where(ImportJob.id == job_id, ImportJob.household_id == household_id))
    if not job: raise HTTPException(status_code=404, detail='Inbox item not found')
    return job


def serialize(job: ImportJob) -> dict:
    return {
        'id': job.id, 'source_type': job.source_type, 'source_url': job.source_url, 'status': job.status, 'title': job.title,
        'draft': json.loads(job.draft_payload or '{}'), 'error_message': job.error_message, 'duplicate_recipe_id': job.duplicate_recipe_id,
        'saved_recipe_id': job.saved_recipe_id, 'created_at': job.created_at, 'updated_at': job.updated_at,
        'assets': [{'id': asset.id, 'url': f'/media/{asset.storage_name}', 'name': asset.original_name, 'media_type': asset.media_type, 'position': asset.position} for asset in job.assets],
    }


def find_duplicate(job: ImportJob, draft: dict, db: Session) -> str | None:
    conditions = []
    if job.source_url: conditions.append(Recipe.source_url == job.source_url)
    title = str(draft.get('title') or '').strip()
    if title and title not in {'Untitled import', 'Photo recipe'}: conditions.append(Recipe.title.ilike(title))
    if not conditions: return None
    recipe = db.scalar(select(Recipe).where(Recipe.household_id == job.household_id, or_(*conditions)).limit(1))
    return recipe.id if recipe else None


async def process_job(job: ImportJob, db: Session):
    if not job.source_url: return
    job.status = 'Processing'; job.error_message = None; db.commit()
    try:
        draft, complete, _final_url = await extract_url(job.source_url)
        draft = normalize_imported_draft(draft)
        job.source_type = draft.get('source', {}).get('type') or job.source_type
        job.title = draft['title']; job.draft_payload = json.dumps(draft)
        job.duplicate_recipe_id = find_duplicate(job, draft, db)
        job.status = 'Ready for Review'
        if not complete:
            if job.source_type in {'youtube', 'instagram', 'facebook'}:
                missing_title = ' The source did not expose a title; add it before saving.' if 'title needed' in draft['title'].casefold() else ''
                job.error_message = f'Only publicly accessible title and description metadata were available.{missing_title} Review the source and complete missing recipe details manually, or try AI extraction.'
            else:
                missing_title = ' Add the correct recipe title.' if 'title needed' in draft['title'].casefold() else ''
                job.error_message = f'Some recipe fields were unavailable and require manual completion.{missing_title}'
    except ImportFailure as error:
        job.status = 'Failed'; job.error_message = str(error)
    except Exception:
        job.status = 'Failed'; job.error_message = 'The recipe could not be imported. You can retry or enter it manually.'
    db.commit(); db.refresh(job)


@router.get('')
async def list_jobs(workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    jobs = db.scalars(select(ImportJob).options(*job_options()).where(ImportJob.household_id == workspace.household_id, ImportJob.status != 'Saved').order_by(ImportJob.created_at.desc())).all()
    return [serialize(job) for job in jobs]


@router.post('/url', status_code=status.HTTP_201_CREATED)
async def create_url_import(payload: InboxUrlCreate, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    try: url = validate_external_url(payload.url.strip())
    except ImportFailure as error: raise HTTPException(status_code=422, detail=str(error))
    host = (urlparse(url).hostname or '').casefold()
    source_type = social_source_type(host) or 'web'
    draft = empty_draft('Pending recipe import', '', url, source_type, host)
    job = ImportJob(household_id=workspace.household_id, source_type=source_type, source_url=url, status='Pending', title='Pending recipe import', draft_payload=json.dumps(draft))
    db.add(job); db.commit(); db.refresh(job)
    await process_job(job, db)
    return serialize(get_job(job.id, workspace.household_id, db))


@router.post('/photos', status_code=status.HTTP_201_CREATED)
async def create_photo_import(files: list[UploadFile] = File(...), workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    if not files or len(files) > 12: raise HTTPException(status_code=422, detail='Upload between 1 and 12 recipe photos')
    settings = get_settings(); validated = []
    for upload in files:
        if upload.content_type not in ALLOWED_IMAGES: raise HTTPException(status_code=415, detail='Only JPEG, PNG, and WebP images are allowed')
        content = await upload.read(settings.max_upload_bytes + 1)
        if len(content) > settings.max_upload_bytes: raise HTTPException(status_code=413, detail='Each image must fit within the upload size limit')
        try:
            with Image.open(BytesIO(content)) as image: image.verify()
        except (UnidentifiedImageError, OSError): raise HTTPException(status_code=422, detail='One or more uploaded images are invalid')
        validated.append((upload, content))
    draft = empty_draft('Photo recipe', '', None, 'photo', 'Cookbook or handwritten recipe')
    job = ImportJob(household_id=workspace.household_id, source_type='photo', status='Ready for Review', title='Photo recipe', draft_payload=json.dumps(draft), error_message='Original photos are preserved. Use AI extraction or transcribe them manually before saving.')
    db.add(job); db.flush()
    import_dir = settings.media_root / 'imports'; import_dir.mkdir(parents=True, exist_ok=True)
    written = []
    try:
        for position, (upload, content) in enumerate(validated):
            storage_name = f'imports/{uuid.uuid4()}{ALLOWED_IMAGES[upload.content_type]}'
            (settings.media_root / storage_name).write_bytes(content); written.append(settings.media_root / storage_name)
            db.add(ImportAsset(import_job_id=job.id, storage_name=storage_name, original_name=Path(upload.filename or 'recipe-photo').name[:255], media_type=upload.content_type, position=position))
        db.commit()
    except Exception:
        db.rollback()
        for path in written: path.unlink(missing_ok=True)
        raise
    return serialize(get_job(job.id, workspace.household_id, db))


@router.post('/{job_id}/retry')
async def retry_import(job_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    if job.status != 'Failed' or not job.source_url: raise HTTPException(status_code=409, detail='Only failed URL imports can be retried')
    job.status = 'Pending'; db.commit(); await process_job(job, db)
    return serialize(get_job(job.id, workspace.household_id, db))


@router.post('/{job_id}/ai-extract')
async def ai_extract_import(job_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    if job.status == 'Saved': raise HTTPException(status_code=409, detail='Saved imports cannot be extracted again')
    source = {'type': job.source_type, 'label': urlparse(job.source_url).hostname if job.source_url else 'Cookbook or handwritten recipe', 'url': job.source_url, 'page': None}
    images = []; prompt = 'Extract this recipe from the supplied images. Preserve page order.'
    if job.assets:
        settings = get_settings()
        images = [((settings.media_root / asset.storage_name).read_bytes(), asset.media_type) for asset in job.assets]
    elif job.source_url:
        try:
            html, final_url = await fetch_public_html(job.source_url)
            source['url'] = final_url
            visible_text = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))[:60_000]
            current = json.loads(job.draft_payload or '{}')
            prompt = f"Extract a recipe from this accessible page text or video description. If information is absent, return empty strings, null quantities, or empty lists. Existing metadata: {json.dumps(current)}\nPage text: {visible_text}"
        except ImportFailure:
            current = json.loads(job.draft_payload or '{}')
            prompt = f"Improve this incomplete recipe draft using only the available public description. Do not infer missing recipe facts: {json.dumps(current)}"
    else:
        raise HTTPException(status_code=409, detail='Inbox item has no source to extract')
    job.status = 'Processing'; job.error_message = None; db.commit()
    try:
        parsed = await run_structured(db, workspace.household_id, 'image_extraction' if images else 'import_fallback', 'You transcribe recipes faithfully. Never invent unreadable or missing ingredients, quantities, times, or instructions. Preserve uncertainty as null or empty.', prompt, RECIPE_SCHEMA, images)
        draft = recipe_draft(parsed, source)
        job = get_job(job_id, workspace.household_id, db); job.draft_payload = json.dumps(draft); job.title = draft['title'] or job.title; job.status = 'Ready for Review'; job.duplicate_recipe_id = find_duplicate(job, draft, db)
        if 'title needed' in draft['title'].casefold(): job.error_message = 'The source did not expose a recipe title. Add the correct title before saving.'
        db.commit()
    except Exception as error:
        job = get_job(job_id, workspace.household_id, db); job.status = 'Failed'; job.error_message = str(error) if str(error) else 'AI extraction failed. Retry or enter the recipe manually.'; db.commit()
        if isinstance(error, BudgetExceeded): raise HTTPException(status_code=429, detail=str(error))
        if isinstance(error, AIUnavailable): raise HTTPException(status_code=503, detail=str(error))
        raise HTTPException(status_code=502, detail='AI extraction failed. The original source is still available.')
    return serialize(get_job(job_id, workspace.household_id, db))


@router.post('/{job_id}/save', response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def save_import(job_id: str, payload: RecipeWrite, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    if job.status == 'Saved': raise HTTPException(status_code=409, detail='Inbox item has already been saved')
    recipe = Recipe(household_id=workspace.household_id, title=payload.title, status=payload.status)
    db.add(recipe); apply_recipe_payload(recipe, payload, db)
    try: db.flush()
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail='A recipe with this title already exists')
    job = get_job(job_id, workspace.household_id, db)
    job.status = 'Saved'; job.saved_recipe_id = recipe.id; job.title = recipe.title; job.draft_payload = payload.model_dump_json()
    db.commit()
    return recipe_to_dict(get_household_recipe(recipe.id, workspace.household_id, db))


@router.delete('/{job_id}', status_code=204)
async def delete_import(job_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    settings = get_settings()
    for asset in job.assets: (settings.media_root / asset.storage_name).unlink(missing_ok=True)
    db.delete(job); db.commit()
