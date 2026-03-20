"""Base agent class — LLM call wrapper with retry, logging, and structured output."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel

from src.config.settings import LLMConfig, LLMProvider, ConcurrencyConfig

logger = logging.getLogger(__name__)


def create_llm(config: LLMConfig) -> BaseChatModel:
    """Create a LangChain chat model from config."""
    if config.provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.get_api_key(),
            base_url=config.base_url,
        )
    elif config.provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.get_api_key(),
            base_url=config.base_url,
        )
    elif config.provider == LLMProvider.OLLAMA:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url=config.base_url or "http://localhost:11434/v1",
            api_key="ollama",
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


class BaseAgent:
    """Base class for all agents in the autopilot system.

    Provides:
    - LLM invocation with retry + exponential backoff
    - Structured JSON output parsing
    - Logging of all LLM calls
    """

    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        concurrency_config: Optional[ConcurrencyConfig] = None,
    ):
        self.name = name
        self.llm = llm
        self._concurrency = concurrency_config or ConcurrencyConfig()
        self._parser = StrOutputParser()

    async def invoke_llm(
        self,
        system_prompt: str,
        user_message: str = "",
        temperature: Optional[float] = None,
    ) -> str:
        """Invoke LLM with retry and exponential backoff. Returns raw string."""
        messages = [SystemMessage(content=system_prompt)]
        if user_message:
            messages.append(HumanMessage(content=user_message))

        last_error = None
        for attempt in range(1, self._concurrency.llm_retry_max_attempts + 1):
            try:
                logger.info(
                    f"[{self.name}] LLM call attempt {attempt}/{self._concurrency.llm_retry_max_attempts}"
                )
                response = await self.llm.ainvoke(messages)
                result = self._parser.invoke(response)
                logger.debug(f"[{self.name}] LLM response length: {len(result)} chars")
                return result
            except Exception as e:
                last_error = e
                if attempt < self._concurrency.llm_retry_max_attempts:
                    delay = self._concurrency.llm_retry_base_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[{self.name}] LLM call failed (attempt {attempt}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{self.name}] LLM call failed after {attempt} attempts: {e}"
                    )

        raise RuntimeError(
            f"[{self.name}] LLM call failed after "
            f"{self._concurrency.llm_retry_max_attempts} attempts: {last_error}"
        )

    async def invoke_llm_json(
        self,
        system_prompt: str,
        user_message: str = "",
    ) -> Any:
        """Invoke LLM and parse response as JSON."""
        raw = await self.invoke_llm(system_prompt, user_message)
        return self._parse_json(raw)

    def _parse_json(self, text: str) -> Any:
        """Extract and parse JSON from LLM response (handles markdown fences)."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            start = 1
            end = len(lines)
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "```":
                    end = i
                    break
            cleaned = "\n".join(lines[start:end])

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.name}] JSON parse failed, attempting repair: {e}")
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start == -1:
                start = cleaned.find("[")
                end = cleaned.rfind("]") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"[{self.name}] Failed to parse JSON from LLM response: {text[:200]}...")
