from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routers import ai, deck, groceries, imports, pantry, recipes


settings = get_settings()
settings.media_root.mkdir(parents=True, exist_ok=True)

app = FastAPI(title='Our Kitchen API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.origin_list, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
app.include_router(recipes.router, prefix='/api')
app.include_router(pantry.router, prefix='/api')
app.include_router(deck.router, prefix='/api')
app.include_router(groceries.router, prefix='/api')
app.include_router(imports.router, prefix='/api')
app.include_router(ai.router, prefix='/api')
app.mount('/media', StaticFiles(directory=settings.media_root), name='media')


@app.get('/api/health')
async def health():
    return {'status': 'ok'}
