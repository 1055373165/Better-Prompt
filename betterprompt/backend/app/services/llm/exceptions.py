class PromptLLMError(RuntimeError):
    """Base exception for BetterPrompt LLM integration."""


class PromptLLMConfigurationError(PromptLLMError):
    """Raised when required LLM configuration is missing or invalid."""


class PromptLLMRequestError(PromptLLMError):
    """Raised when the upstream LLM request fails."""
