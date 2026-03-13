# BetterPrompt

This directory extracts the Prompt Agent feature from the main project into a dedicated workspace scaffold.

## Scope

- Frontend Prompt Agent UI
- Backend Prompt Agent API and service layer
- Prompt Agent planning and milestone documents

## Status

This scaffold is being extracted from the main application. It is intended to become a standalone subproject under the repository root.

## Notes

- Source of truth remains the main project files until extraction is fully completed.
- Service startup is not included in this extraction step.

## LLM Generate Setup

`/api/v1/prompt-agent/generate` now supports real upstream LLM calls instead of only returning the local template instruction.

Required backend environment variables:

- `BETTERPROMPT_LLM_API_KEY`: upstream provider API key
- `BETTERPROMPT_LLM_MODEL`: model id to use for generation

Optional backend environment variables:

- `BETTERPROMPT_LLM_BASE_URL`: defaults to `https://api.openai.com/v1`
- `BETTERPROMPT_LLM_ENDPOINT`: defaults to `chat/completions`
- `BETTERPROMPT_LLM_TIMEOUT_SECONDS`: defaults to `120`
- `BETTERPROMPT_LLM_TEMPERATURE`: defaults to `0.3`
- `BETTERPROMPT_ALLOW_TEMPLATE_FALLBACK`: if set to `1`, missing LLM config falls back to the old local template output

You can also reuse:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`

If no model client is configured and fallback is disabled, `generate` returns HTTP `503` with a clear configuration error.
