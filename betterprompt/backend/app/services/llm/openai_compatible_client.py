import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from app.services.llm.exceptions import PromptLLMConfigurationError, PromptLLMRequestError


TRUE_VALUES = {'1', 'true', 'yes', 'on'}


def _read_bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in TRUE_VALUES


def is_template_fallback_enabled() -> bool:
    return _read_bool_env('BETTERPROMPT_ALLOW_TEMPLATE_FALLBACK', default=False)


@dataclass(frozen=True)
class OpenAICompatibleLLMConfig:
    api_key: str
    model: str
    base_url: str
    endpoint: str
    timeout_seconds: float
    temperature: float

    @classmethod
    def from_env(cls) -> 'OpenAICompatibleLLMConfig':
        api_key = os.getenv('BETTERPROMPT_LLM_API_KEY') or os.getenv('OPENAI_API_KEY')
        model = os.getenv('BETTERPROMPT_LLM_MODEL')
        base_url = os.getenv('BETTERPROMPT_LLM_BASE_URL') or os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1'
        endpoint = os.getenv('BETTERPROMPT_LLM_ENDPOINT', 'chat/completions')
        timeout_seconds = float(os.getenv('BETTERPROMPT_LLM_TIMEOUT_SECONDS', '120'))
        temperature = float(os.getenv('BETTERPROMPT_LLM_TEMPERATURE', '0.3'))

        missing_fields: list[str] = []
        if not api_key:
            missing_fields.append('BETTERPROMPT_LLM_API_KEY')
        if not model:
            missing_fields.append('BETTERPROMPT_LLM_MODEL')

        if missing_fields:
            joined_fields = ', '.join(missing_fields)
            raise PromptLLMConfigurationError(
                f'LLM generation is not configured. Missing required env vars: {joined_fields}.'
            )

        return cls(
            api_key=api_key,
            model=model,
            base_url=base_url.rstrip('/'),
            endpoint=endpoint.strip('/'),
            timeout_seconds=timeout_seconds,
            temperature=temperature,
        )

    @property
    def request_url(self) -> str:
        return f'{self.base_url}/{self.endpoint}'


class OpenAICompatibleLLMClient:
    def __init__(self, config: OpenAICompatibleLLMConfig):
        self.config = config

    @property
    def model_name(self) -> str:
        return self.config.model

    async def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        return await asyncio.to_thread(self._generate_text_sync, system_prompt, user_prompt)

    def _generate_text_sync(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            'model': self.config.model,
            'temperature': self.config.temperature,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
        }
        body = json.dumps(payload).encode('utf-8')
        req = request.Request(
            self.config.request_url,
            data=body,
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw_body = response.read().decode('utf-8')
        except error.HTTPError as exc:
            error_body = exc.read().decode('utf-8', errors='ignore')
            raise PromptLLMRequestError(
                f'Upstream LLM request failed with status {exc.code}: {error_body[:400]}'
            ) from exc
        except error.URLError as exc:
            raise PromptLLMRequestError(f'Upstream LLM request could not be completed: {exc.reason}') from exc

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise PromptLLMRequestError('Upstream LLM returned invalid JSON.') from exc

        content = self._extract_content(parsed)
        if not content:
            raise PromptLLMRequestError('Upstream LLM response did not include any text content.')
        return content

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get('choices')
        if isinstance(choices, list) and choices:
            message = choices[0].get('message', {})
            content = message.get('content')
            text = self._normalize_content(content)
            if text:
                return text

        output_text = payload.get('output_text')
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = payload.get('output')
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                for content_item in item.get('content', []):
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get('text')
                    if isinstance(text, str) and text.strip():
                        chunks.append(text.strip())
            if chunks:
                return '\n'.join(chunks)

        return ''

    def _normalize_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str) and item.strip():
                    parts.append(item.strip())
                    continue
                if not isinstance(item, dict):
                    continue
                text = item.get('text')
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            return '\n'.join(parts).strip()
        return ''


def get_default_llm_client() -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(OpenAICompatibleLLMConfig.from_env())
