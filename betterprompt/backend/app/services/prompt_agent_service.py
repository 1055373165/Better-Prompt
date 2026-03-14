from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.prompt_agent import (
    ContinuePromptRequest,
    ContinuePromptResponse,
    DebugPromptRequest,
    DebugPromptResponse,
    EvaluatePromptRequest,
    EvaluatePromptResponse,
    GeneratePromptRequest,
    GeneratePromptResponse,
)
from app.services.prompt_agent.orchestrator import PromptAgentOrchestrator


class PromptAgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.orchestrator = PromptAgentOrchestrator(db)

    async def generate(self, request: GeneratePromptRequest) -> GeneratePromptResponse:
        return await self.orchestrator.generate(request)

    async def generate_stream(self, request: GeneratePromptRequest) -> AsyncGenerator[str, None]:
        async for chunk in self.orchestrator.generate_stream(request):
            yield chunk

    async def debug(self, request: DebugPromptRequest) -> DebugPromptResponse:
        return await self.orchestrator.debug(request)

    async def evaluate(self, request: EvaluatePromptRequest) -> EvaluatePromptResponse:
        return await self.orchestrator.evaluate(request)

    async def continue_optimization(self, request: ContinuePromptRequest) -> ContinuePromptResponse:
        return await self.orchestrator.continue_optimization(request)
