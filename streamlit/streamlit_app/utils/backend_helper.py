"""
Sake Sensei - Backend API Helper

directly (fallback when Gateway is not configured).

IMPORTANT: Per CLAUDE.md, all AI services should use AgentCore.
"""

from typing import Any

from utils.config import config
from utils.preference_converter import convert_to_backend_format
from utils.session import SessionManager


class BackendError(Exception):
    """Custom exception for backend API errors."""

    pass


class BackendClient:
    def __init__(self):
        """Initialize backend client."""
        self.gateway_url = config.AGENTCORE_GATEWAY_URL
        self.timeout = 30
        self.use_gateway = bool(self.gateway_url)

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
            # Send empty preferences
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
