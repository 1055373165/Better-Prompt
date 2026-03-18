from app.core import load_runtime_env
load_runtime_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.prompt_agent import router as prompt_agent_router
from app.api.v1.prompt_sessions import router as prompt_sessions_router
from app.db.init_db import init_db

app = FastAPI(title='BetterPrompt Backend', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def on_startup() -> None:
    await init_db()


@app.get('/api/v1/health')
async def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'betterprompt-backend', 'version': '0.1.0'}


app.include_router(prompt_agent_router, prefix='/api/v1')
app.include_router(prompt_sessions_router, prefix='/api/v1')
