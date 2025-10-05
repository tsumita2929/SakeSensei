"""
Sake Sensei - Session State Management

Manages Streamlit session state for authentication, user preferences, and app state.
"""

from typing import Any

import streamlit as st


class SessionManager:
    """Manages Streamlit session state."""

    # Session keys
    KEY_AUTHENTICATED = "authenticated"
    KEY_USER_ID = "user_id"
    KEY_USER_EMAIL = "user_email"
    KEY_USER_NAME = "user_name"
    KEY_ACCESS_TOKEN = "access_token"
    KEY_ID_TOKEN = "id_token"
    KEY_REFRESH_TOKEN = "refresh_token"
    KEY_USER_PREFERENCES = "user_preferences"
    KEY_CHAT_HISTORY = "chat_history"
    KEY_AGENT_SESSION_ID = "agent_session_id"

    @staticmethod
    def init():
        """Initialize session state with default values."""
        defaults = {
            SessionManager.KEY_AUTHENTICATED: False,
            SessionManager.KEY_USER_ID: None,
            SessionManager.KEY_USER_EMAIL: None,
            SessionManager.KEY_USER_NAME: None,
            SessionManager.KEY_ACCESS_TOKEN: None,
            SessionManager.KEY_ID_TOKEN: None,
            SessionManager.KEY_REFRESH_TOKEN: None,
            SessionManager.KEY_USER_PREFERENCES: {},
            SessionManager.KEY_CHAT_HISTORY: [],
            SessionManager.KEY_AGENT_SESSION_ID: None,
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from session state."""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        """Set value in session state."""
        st.session_state[key] = value

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        return st.session_state.get(SessionManager.KEY_AUTHENTICATED, False)

    @staticmethod
    def login(
        user_id: str,
        email: str,
        name: str | None = None,
        access_token: str | None = None,
        id_token: str | None = None,
        refresh_token: str | None = None,
    ):
        """Set user as authenticated."""
        st.session_state[SessionManager.KEY_AUTHENTICATED] = True
        st.session_state[SessionManager.KEY_USER_ID] = user_id
        st.session_state[SessionManager.KEY_USER_EMAIL] = email
        st.session_state[SessionManager.KEY_USER_NAME] = name
        st.session_state[SessionManager.KEY_ACCESS_TOKEN] = access_token
        st.session_state[SessionManager.KEY_ID_TOKEN] = id_token
        st.session_state[SessionManager.KEY_REFRESH_TOKEN] = refresh_token

    @staticmethod
    def logout():
        """Clear authentication and reset session."""
        st.session_state[SessionManager.KEY_AUTHENTICATED] = False
        st.session_state[SessionManager.KEY_USER_ID] = None
        st.session_state[SessionManager.KEY_USER_EMAIL] = None
        st.session_state[SessionManager.KEY_USER_NAME] = None
        st.session_state[SessionManager.KEY_ACCESS_TOKEN] = None
        st.session_state[SessionManager.KEY_ID_TOKEN] = None
        st.session_state[SessionManager.KEY_REFRESH_TOKEN] = None
        st.session_state[SessionManager.KEY_USER_PREFERENCES] = {}
        st.session_state[SessionManager.KEY_CHAT_HISTORY] = []
        st.session_state[SessionManager.KEY_AGENT_SESSION_ID] = None

    @staticmethod
    def get_user_id() -> str | None:
        """Get current user ID."""
        return st.session_state.get(SessionManager.KEY_USER_ID)

    @staticmethod
    def get_user_email() -> str | None:
        """Get current user email."""
        return st.session_state.get(SessionManager.KEY_USER_EMAIL)

    @staticmethod
    def get_user_name() -> str | None:
        """Get current user name."""
        return st.session_state.get(SessionManager.KEY_USER_NAME)

    @staticmethod
    def get_access_token() -> str | None:
        """Get access token."""
        return st.session_state.get(SessionManager.KEY_ACCESS_TOKEN)

    @staticmethod
    def get_id_token() -> str | None:
        """Get ID token."""
        return st.session_state.get(SessionManager.KEY_ID_TOKEN)

    @staticmethod
    def set_preferences(preferences: dict):
        """Set user preferences."""
        st.session_state[SessionManager.KEY_USER_PREFERENCES] = preferences

    @staticmethod
    def get_preferences() -> dict:
        """Get user preferences."""
        return st.session_state.get(SessionManager.KEY_USER_PREFERENCES, {})

    @staticmethod
    def add_chat_message(role: str, content: str):
        """Add message to chat history."""
        if SessionManager.KEY_CHAT_HISTORY not in st.session_state:
            st.session_state[SessionManager.KEY_CHAT_HISTORY] = []

        st.session_state[SessionManager.KEY_CHAT_HISTORY].append({"role": role, "content": content})

    @staticmethod
    def get_chat_history() -> list:
        """Get chat history."""
        return st.session_state.get(SessionManager.KEY_CHAT_HISTORY, [])

    @staticmethod
    def clear_chat_history():
        """Clear chat history."""
        st.session_state[SessionManager.KEY_CHAT_HISTORY] = []

    @staticmethod
    def set_agent_session_id(session_id: str):
        """Set AgentCore session ID."""
        st.session_state[SessionManager.KEY_AGENT_SESSION_ID] = session_id

    @staticmethod
    def get_agent_session_id() -> str | None:
        """Get AgentCore session ID."""
        return st.session_state.get(SessionManager.KEY_AGENT_SESSION_ID)

    @staticmethod
    def get_user_info() -> dict:
        """Get current user information."""
        return {
            "user_id": SessionManager.get_user_id(),
            "email": SessionManager.get_user_email(),
            "name": SessionManager.get_user_name(),
        }


# Initialize session on module import
SessionManager.init()
