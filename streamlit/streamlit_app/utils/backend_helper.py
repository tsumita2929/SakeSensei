"""
Sake Sensei - Backend API Helper

Helper functions for calling Lambda functions via AgentCore Gateway (recommended)
or directly (fallback when Gateway is not configured).

IMPORTANT: Per CLAUDE.md, all AI services should use AgentCore.
Direct Lambda invocation is a temporary fallback until Gateway is properly set up.
"""

import contextlib
import json
from typing import Any

import boto3
import requests
from utils.config import config
from utils.preference_converter import convert_to_backend_format
from utils.session import SessionManager


class BackendError(Exception):
    """Custom exception for backend API errors."""

    pass


class BackendClient:
    """
    Client for backend Lambda function calls.

    Prefers AgentCore Gateway (MCP) but falls back to direct Lambda invocation
    if Gateway URL is not configured.
    """

    def __init__(self):
        """Initialize backend client."""
        self.gateway_url = config.AGENTCORE_GATEWAY_URL
        self.timeout = 30
        self.use_gateway = bool(self.gateway_url)

        # Initialize Lambda client for fallback
        if not self.use_gateway:
            self.lambda_client = boto3.client("lambda", region_name=config.AWS_REGION)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }

        # Add ID token for authentication
        id_token = SessionManager.get_id_token()
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"

        return headers

    def _invoke_lambda_direct(self, function_arn: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Invoke Lambda function directly (fallback mode).

        Args:
            function_arn: Lambda function ARN
            payload: Function payload (will be wrapped in API Gateway format)

        Returns:
            Lambda response

        Raises:
            BackendError: On Lambda errors
        """
        try:
            # Wrap payload in API Gateway format (Lambda expects event.body)
            event = {
                "body": json.dumps(payload),
                "requestContext": {
                    "authorizer": {"user_id": SessionManager.get_user_id() or "anonymous"}
                },
            }

            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType="RequestResponse",
                Payload=json.dumps(event),
            )

            # Parse response
            response_payload = json.loads(response["Payload"].read())

            # Check for Lambda errors
            if "errorMessage" in response_payload:
                raise BackendError(f"Lambda error: {response_payload['errorMessage']}")

            # Handle API Gateway-style response
            if "statusCode" in response_payload:
                if response_payload["statusCode"] != 200:
                    error_body = response_payload.get("body", "Unknown error")
                    if isinstance(error_body, str):
                        # Try to parse JSON error body, keep string if fails
                        with contextlib.suppress(json.JSONDecodeError):
                            error_body = json.loads(error_body)  # noqa: PLW2901
                    raise BackendError(f"Lambda returned error: {error_body}")

                body = response_payload.get("body", "{}")
                if isinstance(body, str):
                    return json.loads(body)
                return body

            # Direct response
            return response_payload

        except json.JSONDecodeError as e:
            raise BackendError(f"Failed to parse Lambda response: {str(e)}")

        except Exception as e:
            if isinstance(e, BackendError):
                raise
            raise BackendError(f"Lambda invocation failed: {str(e)}")

    def _make_request(
        self, tool_name: str, parameters: dict[str, Any], timeout: int | None = None
    ) -> dict[str, Any]:
        """
        Make request to Gateway tool or invoke Lambda directly (fallback).

        Args:
            tool_name: MCP tool name / Lambda function identifier
            parameters: Tool parameters
            timeout: Request timeout in seconds

        Returns:
            Tool response data

        Raises:
            BackendError: On API errors
        """
        # Use AgentCore Gateway if configured (recommended)
        if self.use_gateway:
            try:
                response = requests.post(
                    f"{self.gateway_url}/invoke-tool",
                    json={"tool": tool_name, "arguments": parameters},
                    headers=self._get_headers(),
                    timeout=timeout or self.timeout,
                )

                if response.status_code != 200:
                    raise BackendError(
                        f"Gateway request failed: {response.status_code} {response.text}"
                    )

                result = response.json()

                # Check for tool execution errors
                if result.get("isError"):
                    raise BackendError(
                        f"Tool execution failed: {result.get('content', 'Unknown error')}"
                    )

                return result.get("content", {})

            except requests.exceptions.Timeout:
                raise BackendError("Request timeout. Please try again.")

            except requests.exceptions.RequestException as e:
                raise BackendError(f"Network error: {str(e)}")

            except json.JSONDecodeError:
                raise BackendError("Invalid response from Gateway")

        # Fallback: Direct Lambda invocation
        else:
            # Map tool names to Lambda ARNs
            lambda_arn_map = {
                "get_sake_recommendations": config.LAMBDA_RECOMMENDATION_ARN,
                "manage_user_preferences": config.LAMBDA_PREFERENCE_ARN,
                "get_brewery_info": config.LAMBDA_BREWERY_ARN,
                "recognize_sake_label": config.LAMBDA_IMAGE_RECOGNITION_ARN,
            }

            lambda_arn = lambda_arn_map.get(tool_name)
            if not lambda_arn:
                raise BackendError(f"Unknown tool: {tool_name}")

            return self._invoke_lambda_direct(lambda_arn, parameters)

    # Preference Management

    def get_user_preferences(self, user_id: str | None = None) -> dict[str, Any] | None:
        """
        Get user preferences.

        Args:
            user_id: User ID (defaults to current user)

        Returns:
            User preferences or None if not found
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        try:
            result = self._make_request(
                "manage_user_preferences", {"action": "get", "user_id": uid}
            )
            return result.get("preferences")

        except BackendError as e:
            if "not found" in str(e).lower():
                return None
            raise

    def save_user_preferences(
        self, preferences: dict[str, Any], user_id: str | None = None
    ) -> bool:
        """
        Save user preferences.

        Args:
            preferences: User preference data
            user_id: User ID (defaults to current user)

        Returns:
            True if successful
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        result = self._make_request(
            "manage_user_preferences",
            {"action": "update", "user_id": uid, "preferences": preferences},
        )

        return result.get("success", False)

    # Sake Recommendations

    def get_recommendations(
        self, preferences: dict[str, Any] | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get sake recommendations.

        Args:
            preferences: User preferences (Japanese UI format or backend format)
            limit: Number of recommendations

        Returns:
            List of recommended sake
        """
        user_id = SessionManager.get_user_id()
        if not user_id:
            raise BackendError("User ID not available")

        params: dict[str, Any] = {"user_id": user_id, "limit": limit}

        if preferences:
            # Convert Japanese UI format to backend format if needed
            # Check if it's already in backend format (has 'categories', 'sweetness' as int, etc.)
            if "sake_types" in preferences or isinstance(preferences.get("sweetness"), str):
                # Japanese UI format, need to convert
                params["preferences"] = convert_to_backend_format(preferences)
            else:
                # Already in backend format
                params["preferences"] = preferences
        else:
            # Send empty preferences (Lambda will use defaults)
            params["preferences"] = {}

        result = self._make_request("get_sake_recommendations", params)
        return result.get("recommendations", [])

    # Brewery Information

    def get_brewery_info(self, brewery_id: str) -> dict[str, Any] | None:
        """
        Get brewery information.

        Args:
            brewery_id: Brewery ID

        Returns:
            Brewery information or None if not found
        """
        try:
            result = self._make_request("get_brewery_info", {"brewery_id": brewery_id})
            return result.get("brewery")

        except BackendError as e:
            if "not found" in str(e).lower():
                return None
            raise

    def search_breweries(
        self, prefecture: str | None = None, name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search breweries.

        Args:
            prefecture: Filter by prefecture
            name: Search by name

        Returns:
            List of matching breweries
        """
        params: dict[str, Any] = {"action": "search"}

        if prefecture:
            params["prefecture"] = prefecture

        if name:
            params["name"] = name

        result = self._make_request("get_brewery_info", params)
        return result.get("breweries", [])

    # Image Recognition

    def recognize_sake_label(
        self, image_data: str, media_type: str = "image/jpeg"
    ) -> dict[str, Any]:
        """
        Recognize sake from label image.

        Args:
            image_data: Base64-encoded image data
            media_type: Image media type (image/jpeg, image/png, etc.)

        Returns:
            Recognition result with sake information
        """
        result = self._make_request(
            "recognize_sake_label",
            {"image_base64": image_data, "media_type": media_type},
            timeout=60,  # Image recognition may take longer
        )

        return result


# Global client instance
backend_client = BackendClient()
