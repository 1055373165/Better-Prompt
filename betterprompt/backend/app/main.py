from app.core import load_runtime_env
load_runtime_env()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.agent_runtime import router as agent_runtime_router
from app.api.v1.context_packs import router as context_packs_router
from app.api.v1.domain_workspaces import router as domain_workspaces_router
from app.api.v1.evaluation_profiles import router as evaluation_profiles_router
from app.api.v1.prompt_agent import router as prompt_agent_router
from app.api.v1.prompt_assets import router as prompt_assets_router
from app.api.v1.prompt_sessions import router as prompt_sessions_router
from app.api.v1.run_presets import router as run_presets_router
from app.api.v1.workflow_recipes import router as workflow_recipes_router
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
app.include_router(prompt_assets_router, prefix='/api/v1')
app.include_router(prompt_sessions_router, prefix='/api/v1')
app.include_router(context_packs_router, prefix='/api/v1')
app.include_router(evaluation_profiles_router, prefix='/api/v1')
app.include_router(workflow_recipes_router, prefix='/api/v1')
app.include_router(run_presets_router, prefix='/api/v1')
app.include_router(domain_workspaces_router, prefix='/api/v1')
app.include_router(agent_runtime_router, prefix='/api/v1')
