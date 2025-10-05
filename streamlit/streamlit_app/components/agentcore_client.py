"""
Sake Sensei - AgentCore Runtime Client

HTTP client for invoking AgentCore deployed agents.
"""

import json
import os
import uuid
from collections.abc import AsyncGenerator

import httpx


class AgentCoreClient:
    """Client for AgentCore Runtime API."""

    def __init__(
        self,
        runtime_url: str | None = None,
        id_token: str | None = None,
        timeout: float = 60.0,
    ):
        """
        Initialize AgentCore client.

        Args:
            runtime_url: AgentCore runtime URL (defaults to env var AGENTCORE_RUNTIME_URL)
            id_token: Cognito ID token for authentication
            timeout: Request timeout in seconds
        """
        self.runtime_url = runtime_url or os.getenv("AGENTCORE_RUNTIME_URL")
        if not self.runtime_url:
            raise ValueError("AGENTCORE_RUNTIME_URL is not configured")

        # Remove trailing slash if present
        self.runtime_url = self.runtime_url.rstrip("/")

        self.id_token = id_token
        self.timeout = timeout

    def _get_headers(self, session_id: str | None = None) -> dict[str, str]:
        """
        Build request headers for AgentCore.

        Args:
            session_id: Optional session ID for conversation continuity

        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid.uuid4()),
        }

        # Add session header if provided
        if session_id:
            headers["X-Session-Id"] = session_id

        # Add authorization header if ID token is available
        if self.id_token:
            headers["Authorization"] = f"Bearer {self.id_token}"

        return headers

    async def invoke(
        self,
        message: str,
        session_id: str | None = None,
        additional_context: dict | None = None,
    ) -> dict:
        """
        Invoke agent with a message (non-streaming).

        Args:
            message: User message to send to the agent
            session_id: Optional session ID for conversation continuity
            additional_context: Optional additional context to include in payload

        Returns:
            Agent response as dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = self._get_headers(session_id)

        payload = {"message": message}
        if additional_context:
            payload.update(additional_context)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.runtime_url}/invocations",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def invoke_stream(
        self,
        message: str,
        session_id: str | None = None,
        additional_context: dict | None = None,
    ) -> AsyncGenerator[dict]:
        """
        Invoke agent with streaming response.

        Args:
            message: User message to send to the agent
            session_id: Optional session ID for conversation continuity
            additional_context: Optional additional context to include in payload

        Yields:
            Chunks of agent response as dictionaries

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = self._get_headers(session_id)

        payload = {"message": message}
        if additional_context:
            payload.update(additional_context)

        async with httpx.AsyncClient(timeout=self.timeout) as client, client.stream(
            "POST",
            f"{self.runtime_url}/invocations",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()

            # Process Server-Sent Events (SSE)
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    try:
                        data = json.loads(data_str)
                        yield data
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        continue

    async def check_health(self) -> dict:
        """
        Check agent runtime health status.

        Returns:
            Health status dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.runtime_url}/ping")
            response.raise_for_status()
            return response.json()
