"""Project configuration using Pydantic Settings."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use",
    )
    model: str = Field(
        default="gpt-4o",
        description="Model name",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens per response",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key (reads from env if not set)",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Custom base URL (for Ollama or proxies)",
    )

    def get_api_key(self) -> str:
        """Resolve API key from field or environment variable."""
        if self.api_key:
            return self.api_key
        env_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.OLLAMA: "",
        }
        env_var = env_map.get(self.provider, "")
        if env_var:
            key = os.environ.get(env_var, "")
            if not key:
                raise ValueError(
                    f"API key not found. Set {env_var} environment variable "
                    f"or pass api_key in config."
                )
            return key
        return ""


class ConcurrencyConfig(BaseModel):
    """Concurrency and parallelism settings."""

    max_parallel_mdus: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of MDUs to execute in parallel",
    )
    llm_retry_max_attempts: int = Field(
        default=3,
        ge=1,
        description="Max retry attempts for LLM API calls",
    )
    llm_retry_base_delay: float = Field(
        default=1.0,
        gt=0,
        description="Base delay in seconds for exponential backoff",
    )


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker limits for task decomposition."""

    max_depth: int = Field(
        default=4,
        ge=1,
        description="Maximum recursion depth for task decomposition",
    )
    max_mdu_count: int = Field(
        default=60,
        ge=1,
        description="Maximum total number of MDUs",
    )
    max_sub_items: int = Field(
        default=8,
        ge=1,
        description="Maximum sub-items per task",
    )


class ReviewConfig(BaseModel):
    """Code review settings."""

    max_review_rounds: int = Field(
        default=3,
        ge=1,
        description="Maximum review rounds before escalation",
    )


class HeartbeatConfig(BaseModel):
    """Progress heartbeat settings."""

    percent_interval: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Report progress every N percent completion",
    )


class Settings(BaseModel):
    """Root settings for the autopilot-agent system."""

    project_dir: Path = Field(
        default=Path("."),
        description="Root directory of the target project",
    )
    db_path: Path = Field(
        default=Path("autopilot.db"),
        description="Path to SQLite database file (relative to project_dir)",
    )
    llm: LLMConfig = Field(default_factory=LLMConfig)
    concurrency: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)

    def get_db_full_path(self) -> Path:
        """Return the absolute path to the SQLite database."""
        return self.project_dir.resolve() / self.db_path

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings with environment variable overrides."""
        overrides: dict = {}

        if env_model := os.environ.get("AUTOPILOT_MODEL"):
            overrides.setdefault("llm", {})["model"] = env_model

        if env_provider := os.environ.get("AUTOPILOT_LLM_PROVIDER"):
            overrides.setdefault("llm", {})["provider"] = env_provider

        if env_parallel := os.environ.get("AUTOPILOT_MAX_PARALLEL"):
            overrides.setdefault("concurrency", {})["max_parallel_mdus"] = int(
                env_parallel
            )

        if env_project_dir := os.environ.get("AUTOPILOT_PROJECT_DIR"):
            overrides["project_dir"] = env_project_dir

        return cls(**overrides)
