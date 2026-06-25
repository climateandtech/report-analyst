"""LlamaIndex-compatible LLM adapter routing .achat() to platform via NATS."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, List, Optional, Union

import nats
from llama_index.core.llms import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("PLATFORM_CHAT_MODEL", "gemma3-4b")
REQUEST_TIMEOUT = float(os.getenv("NATS_LLM_TIMEOUT", "120"))


@dataclass
class _ChatResponseMessage:
    content: str


@dataclass
class _ChatResponseWrapper:
    message: _ChatResponseMessage


class NATSLLMChatAdapter:
    """
    Implements the subset of LlamaIndex LLM interface used by DocumentAnalyzer:
    await self.llm.achat(prompt=...) and await self.llm.achat(messages).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        nats_url: Optional[str] = None,
        nats_token: Optional[str] = None,
    ):
        self.model = model or DEFAULT_MODEL
        self._nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self._nats_token = nats_token or os.getenv("NATS_TOKEN")
        self._nc: Optional[nats.NATS] = None
        self._lock = asyncio.Lock()
        self._allowed_models: Optional[List[str]] = None

    def _connection_url(self) -> str:
        url = self._nats_url
        if self._nats_token and "@" not in url:
            protocol, rest = url.split("://", 1)
            url = f"{protocol}://{self._nats_token}@{rest}"
        return url

    async def _ensure_connected(self):
        if self._nc and self._nc.is_connected:
            return
        async with self._lock:
            if self._nc and self._nc.is_connected:
                return
            self._nc = await nats.connect(self._connection_url(), connect_timeout=15)

    async def close(self):
        if self._nc:
            await self._nc.close()
            self._nc = None

    async def list_allowed_models(self) -> List[str]:
        if self._allowed_models is not None:
            return self._allowed_models
        text = await self._request_llm(
            prompt="",
            system_prompt=None,
            request_type="list_models",
        )
        try:
            parsed = json.loads(text)
            self._allowed_models = parsed.get("models", [DEFAULT_MODEL])
        except json.JSONDecodeError:
            self._allowed_models = [DEFAULT_MODEL]
        return self._allowed_models

    def _messages_to_prompt(self, messages: Union[str, List[ChatMessage], List[Any]]) -> tuple[str, Optional[str]]:
        if isinstance(messages, str):
            return messages, None
        system_parts = []
        user_parts = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                role, content = msg.role, msg.content
            elif isinstance(msg, dict):
                role = msg.get("role", MessageRole.USER)
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", MessageRole.USER)
                content = getattr(msg, "content", str(msg))
            if role == MessageRole.SYSTEM or str(role).lower() == "system":
                system_parts.append(content)
            else:
                user_parts.append(content)
        system_prompt = "\n".join(system_parts) if system_parts else None
        prompt = "\n".join(user_parts) if user_parts else ""
        return prompt, system_prompt

    async def achat(
        self,
        messages: Union[str, List[ChatMessage], List[Any]] | None = None,
        prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> _ChatResponseWrapper:
        if prompt is not None and messages is None:
            user_prompt, system_prompt = prompt, kwargs.get("system_prompt")
        else:
            user_prompt, system_prompt = self._messages_to_prompt(messages or prompt or "")
        model = kwargs.get("model", self.model)
        text = await self._request_llm(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=model,
        )
        return _ChatResponseWrapper(message=_ChatResponseMessage(content=text))

    async def _request_llm(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: Optional[str] = None,
        request_type: str = "custom",
    ) -> str:
        await self._ensure_connected()
        request_id = str(uuid.uuid4())
        reply_subject = f"llm.response.{request_id}"
        payload = {
            "request_id": request_id,
            "request_type": request_type,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model or self.model,
            "reply_subject": reply_subject,
            "metadata": {"source": "report_analyst"},
        }

        future: asyncio.Future = asyncio.get_event_loop().create_future()

        async def on_reply(msg):
            try:
                data = json.loads(msg.data.decode())
                if data.get("request_id") != request_id:
                    return
                if data.get("error"):
                    if not future.done():
                        future.set_exception(RuntimeError(data["error"]))
                elif not future.done():
                    future.set_result(data.get("response", ""))
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)

        sub = await self._nc.subscribe(reply_subject, cb=on_reply)
        try:
            js = self._nc.jetstream()
            try:
                await js.publish("llm.request", json.dumps(payload).encode())
            except Exception:
                await self._nc.publish("llm.request", json.dumps(payload).encode())
            return await asyncio.wait_for(future, timeout=REQUEST_TIMEOUT)
        finally:
            await sub.unsubscribe()
