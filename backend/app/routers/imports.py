from io import BytesIO
import json
from pathlib import Path
import uuid
from urllib.parse import urljoin, urlparse
import re

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..dependencies import Workspace, current_workspace
from ..ai import AIInvalidResponse, AIUnavailable, BudgetExceeded, RECIPE_SCHEMA, recipe_draft, run_structured
from ..importer import ImportFailure, YouTubeTranscriptFailure, clean_pasted_youtube_transcript, empty_draft, ensure_public_dns, extract_url, fetch_public_html, fetch_youtube_transcript, image_url_from_page, public_text_from_html, social_source_type, validate_external_url
from ..ingredient_parser import normalize_imported_draft
from ..models import ImportAsset, ImportJob, Recipe, RecipePhoto
from ..schemas import AIExtractRequest, InboxUrlCreate, RecipeRead, RecipeWrite
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
        'assets': [{'id': asset.id, 'url': f'/media/{asset.storage_name}', 'name': asset.original_name, 'media_type': asset.media_type, 'position': asset.position, 'role': asset.role} for asset in job.assets],
    }


def find_duplicate(job: ImportJob, draft: dict, db: Session) -> str | None:
    conditions = []
    if job.source_url: conditions.append(Recipe.source_url == job.source_url)
    title = str(draft.get('title') or '').strip()
    has_recipe_content = bool(draft.get('ingredients') and draft.get('steps'))
    placeholder = not title or 'title needed' in title.casefold() or title in {'Untitled import', 'Photo recipe', 'Pending recipe import'}
    if has_recipe_content and not placeholder: conditions.append(Recipe.title.ilike(title))
    if not conditions: return None
    recipe = db.scalar(select(Recipe).where(Recipe.household_id == job.household_id, or_(*conditions)).limit(1))
    return recipe.id if recipe else None


async def download_import_image(job: ImportJob, image_url: str | None, db: Session) -> bool:
    """Persist a guarded external image; image failure never fails recipe import."""
    if not image_url or any(asset.role == 'cover' for asset in job.assets): return False
    settings = get_settings(); current = image_url
    try:
        async with httpx.AsyncClient(timeout=12, headers={'User-Agent': 'OurKitchenRecipeImporter/1.0', 'Accept': 'image/jpeg,image/png,image/webp'}) as client:
            for _ in range(4):
                current = validate_external_url(current); await ensure_public_dns(current)
                response = await client.get(current, follow_redirects=False)
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get('location')
                    if not location: return False
                    current = urljoin(current, location); continue
                if response.status_code >= 400: return False
                media_type = response.headers.get('content-type', '').split(';')[0].casefold()
                if media_type not in ALLOWED_IMAGES or len(response.content) > settings.max_upload_bytes: return False
                with Image.open(BytesIO(response.content)) as image: image.verify()
                settings.media_root.joinpath('imports').mkdir(parents=True, exist_ok=True)
                storage_name = f'imports/{uuid.uuid4()}{ALLOWED_IMAGES[media_type]}'
                (settings.media_root / storage_name).write_bytes(response.content)
                db.add(ImportAsset(import_job_id=job.id, storage_name=storage_name, original_name=f'imported-cover{ALLOWED_IMAGES[media_type]}', media_type=media_type, position=0, role='cover'))
                db.commit(); return True
    except (ImportFailure, httpx.HTTPError, UnidentifiedImageError, OSError, ValueError):
        return False
    return False


async def process_job(job: ImportJob, db: Session):
    if not job.source_url: return
    image_url = None
    job.status = 'Processing'; job.error_message = None; db.commit()
    try:
        draft, complete, _final_url, image_url = await extract_url(job.source_url)
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
    if job.status == 'Ready for Review': await download_import_image(job, image_url, db)


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
    job = ImportJob(household_id=workspace.household_id, source_type='photo', status='Ready for Review', title='Photo recipe', draft_payload=json.dumps(draft), error_message='Original photos are preserved for automatic AI extraction, review, and retry.')
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
async def ai_extract_import(job_id: str, payload: AIExtractRequest | None = None, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    if job.status == 'Saved': raise HTTPException(status_code=409, detail='Saved imports cannot be extracted again')
    source = {'type': job.source_type, 'label': urlparse(job.source_url).hostname if job.source_url else 'Cookbook or handwritten recipe', 'url': job.source_url, 'page': None}
    images = []; prompt = 'Extract this recipe from the supplied images. Preserve page order.'; extraction_note = None
    if job.assets and job.source_type == 'photo':
        settings = get_settings()
        images = [((settings.media_root / asset.storage_name).read_bytes(), asset.media_type) for asset in job.assets]
    elif job.source_url:
        try:
            html, final_url = await fetch_public_html(job.source_url)
            source['url'] = final_url
            await download_import_image(job, image_url_from_page(html, final_url), db)
            visible_text = public_text_from_html(html)[:60_000]
            current = json.loads(job.draft_payload or '{}')
            if job.source_type == 'youtube':
                manual_transcript = (payload.manual_transcript if payload else None) or ''
                if manual_transcript.strip():
                    transcript = clean_pasted_youtube_transcript(manual_transcript)
                    transcript_label = 'pasted transcript'
                else:
                    try:
                        transcript, transcript_label = await fetch_youtube_transcript(html)
                    except YouTubeTranscriptFailure as error:
                        job.error_message = str(error); job.status = 'Ready for Review'; db.commit()
                        raise HTTPException(status_code=422, detail=str(error))
                description = str(current.get('description') or '').strip()
                prompt = f"Extract a recipe from this YouTube description and chronological transcript. Ignore greetings, promotions, engagement requests, and unrelated commentary. Combine supported ingredient details and preparation steps even when they occur in different transcript sections. Preserve chronological preparation order. Never invent measurements or steps absent from the source. Existing metadata: {json.dumps(current)}\nDescription: {description}\nTranscript ({transcript_label}): {transcript}"
                extraction_note = f'YouTube transcript retrieved and processed ({transcript_label}).'
            if job.source_type == 'facebook':
                recipe_signals = len(re.findall(r'\b(?:cup|tsp|tbsp|ounce|ingredient|instructions?|mix|bake|cook|simmer|chop)\b', visible_text, re.IGNORECASE))
                if len(visible_text) < 150 or recipe_signals < 2:
                    job.error_message = 'Facebook exposed only limited public metadata; the video, caption, and transcript could not be accessed. Paste recipe text or upload screenshots for extraction.'; job.status = 'Ready for Review'; db.commit()
                    raise HTTPException(status_code=422, detail=job.error_message)
            if job.source_type != 'youtube':
                prompt = f"Extract a recipe from this accessible page text or video description. If information is absent, return empty strings, null quantities, or empty lists. Existing metadata: {json.dumps(current)}\nPage text: {visible_text}"
        except ImportFailure:
            if job.source_type == 'facebook':
                job.error_message = 'Facebook did not expose accessible recipe text, a caption, or a transcript. Paste recipe text or upload screenshots for extraction.'
                job.status = 'Ready for Review'
                db.commit()
                raise HTTPException(status_code=422, detail=job.error_message)
            current = json.loads(job.draft_payload or '{}')
            prompt = f"Improve this incomplete recipe draft using only the available public description. Do not infer missing recipe facts: {json.dumps(current)}"
    else:
        raise HTTPException(status_code=409, detail='Inbox item has no source to extract')
    job.status = 'Processing'; job.error_message = None; db.commit()
    try:
        parsed = await run_structured(db, workspace.household_id, 'image_extraction' if images else 'import_fallback', 'You transcribe recipes faithfully. Never invent unreadable or missing ingredients, quantities, times, instructions, or component sections. Preserve uncertainty as null or empty. Preserve explicit ingredient and instruction component headings such as Crust, Filling, Sauce, Frosting, Topping, Marinade, Dressing, Dough, or Assembly in their original order; use section_index to associate items, and leave section lists empty for a simple unsectioned recipe. Write a concise one- or two-sentence description with no quotation marks, website commentary, or promotional language. Suggest one cuisine and all applicable recipe categories from the recipe content. Deduplicate tags and categories case-insensitively. Preserve an explicit yield unit such as rotis, slices, or servings. Put resting, chilling, rising, or other time outside prep and cook in additional_time_minutes with a short label, and never double-count a stated total time.', prompt, RECIPE_SCHEMA, images)
        draft = recipe_draft(parsed, source)
        job = get_job(job_id, workspace.household_id, db); job.draft_payload = json.dumps(draft); job.title = draft['title'] or job.title; job.status = 'Ready for Review'; job.duplicate_recipe_id = find_duplicate(job, draft, db)
        if job.source_type == 'youtube' and (not draft.get('ingredients') or not draft.get('steps')):
            job.error_message = 'The transcript was retrieved but did not contain enough supported recipe information. Review the available details, paste a fuller transcript, or complete the recipe manually.'
        elif 'title needed' in draft['title'].casefold(): job.error_message = 'The source did not expose a recipe title. Add the correct title before saving.'
        elif extraction_note: job.error_message = extraction_note
        db.commit()
    except Exception as error:
        job = get_job(job_id, workspace.household_id, db); job.status = 'Failed'; job.error_message = str(error) if str(error) else 'AI extraction failed. Retry or enter the recipe manually.'; db.commit()
        if isinstance(error, BudgetExceeded): raise HTTPException(status_code=429, detail=str(error))
        if isinstance(error, AIUnavailable): raise HTTPException(status_code=503, detail=str(error))
        if isinstance(error, AIInvalidResponse): raise HTTPException(status_code=502, detail=str(error))
        job.error_message = 'AI extraction failed. The original source and any previously extracted details are still available.'; db.commit()
        raise HTTPException(status_code=502, detail=job.error_message)
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
    cover = next((asset for asset in job.assets if asset.role == 'cover'), None)
    if cover:
        db.add(RecipePhoto(recipe_id=recipe.id, storage_name=cover.storage_name, original_name=cover.original_name, media_type=cover.media_type, alt_text=f'{recipe.title} recipe', position=0, is_cover=True))
    job.status = 'Saved'; job.saved_recipe_id = recipe.id; job.title = recipe.title; job.draft_payload = payload.model_dump_json()
    db.commit()
    return recipe_to_dict(get_household_recipe(recipe.id, workspace.household_id, db))


@router.delete('/{job_id}/image')
async def remove_import_image(job_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    if job.status == 'Saved': raise HTTPException(status_code=409, detail='Saved recipe images must be managed from the recipe')
    cover = next((asset for asset in job.assets if asset.role == 'cover'), None)
    if not cover: raise HTTPException(status_code=404, detail='Imported recipe image not found')
    (get_settings().media_root / cover.storage_name).unlink(missing_ok=True)
    db.delete(cover); db.commit()
    return serialize(get_job(job_id, workspace.household_id, db))


@router.delete('/{job_id}', status_code=204)
async def delete_import(job_id: str, workspace: Workspace = Depends(current_workspace), db: Session = Depends(get_db)):
    job = get_job(job_id, workspace.household_id, db)
    settings = get_settings()
    for asset in job.assets: (settings.media_root / asset.storage_name).unlink(missing_ok=True)
    db.delete(job); db.commit()
