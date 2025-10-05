"""
Sake Sensei - Main Streamlit Application

AI-powered sake recommendation system powered by Amazon Bedrock AgentCore.
"""

import codecs
import json
import re
import uuid
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

import boto3
import streamlit as st
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from components.auth import CognitoAuth
from utils.config import config
from utils.session import SessionManager
from utils.ui_components import load_custom_css


@lru_cache(maxsize=1)
def get_bedrock_runtime_client() -> BaseClient:
    """Create and cache a Bedrock AgentCore runtime client."""

    return boto3.client("bedrock-agentcore", region_name=config.AWS_REGION)


def _extract_text_from_agent_response(payload: Any) -> str:
    """Extract user-visible text content from an AgentCore response payload."""

    texts: list[str] = []

    def _collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if isinstance(nested, str) and key.lower() in {
                    "text",
                    "content",
                    "outputtext",
                    "message",
                    "delta",
                }:
                    texts.append(nested)
                else:
                    _collect(nested)
        elif isinstance(value, list):
            for item in value:
                _collect(item)

    _collect(payload)

    merged = "\n".join(text.strip() for text in texts if text.strip())
    if merged:
        return merged

    return json.dumps(payload, ensure_ascii=False)


def _extract_text_from_agent_event(payload: Any) -> str:
    """Extract displayable text from a streaming event, ignoring non-text payloads."""

    text = _extract_text_from_agent_response(payload)

    if isinstance(payload, (dict, list)):
        try:
            payload_json = json.dumps(payload, ensure_ascii=False)
        except TypeError:
            payload_json = None
        else:
            if payload_json == text:
                return ""

    return text


def _invoke_agent_runtime(session_id: str, request_payload: str) -> dict[str, Any]:
    """Invoke the Bedrock AgentCore runtime with alias fallback logic."""

    client = get_bedrock_runtime_client()

    alias_candidates: list[str | None] = []

    configured_alias = (config.AGENTCORE_AGENT_ALIAS_ID or "").strip() or None
    if configured_alias:
        alias_candidates.append(configured_alias)

    if "DEFAULT" not in alias_candidates:
        alias_candidates.append("DEFAULT")

    alias_candidates.append(None)

    last_error: ClientError | None = None

    for qualifier in alias_candidates:
        request_kwargs: dict[str, Any] = {
            "agentRuntimeArn": config.AGENTCORE_RUNTIME_ARN,
            "runtimeSessionId": session_id,
            "payload": request_payload,
        }

        if qualifier:
            request_kwargs["qualifier"] = qualifier

        try:
            return client.invoke_agent_runtime(**request_kwargs)
        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")
            if error_code == "ResourceNotFoundException" and qualifier is not None:
                last_error = error
                continue
            raise

    raise last_error or RuntimeError("Failed to invoke Bedrock agent runtime.")


def _parse_sse_event(raw_event: str) -> Any | None:
    """Parse a raw SSE event block into a JSON-compatible payload."""

    if not raw_event or not raw_event.strip():
        return None

    data_lines: list[str] = []
    for line in raw_event.splitlines():
        event_line = line.strip("\r")
        if not event_line or event_line.startswith(":"):
            continue
        if event_line.startswith("data:"):
            data_lines.append(event_line[5:].lstrip())

    data_str = "".join(data_lines).strip() if data_lines else raw_event.strip()

    if not data_str:
        return None

    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        return data_str


def _extract_delta_from_payload(payload: Any) -> str:
    """Extract incremental text from an AgentCore streaming payload."""

    if payload is None:
        return ""

    if isinstance(payload, dict):
        event_type = payload.get("type") or payload.get("eventType")
        if isinstance(event_type, str) and event_type.lower() in {
            "end",
            "done",
            "responsecompleted",
            "responsecomplete",
        }:
            return ""

        # Only process text-delta events to avoid duplication
        # AgentCore sends both contentBlockDelta and text-delta with same content
        if event_type == "text-delta" and isinstance(payload.get("delta"), str):
            return payload["delta"]

    return ""


def stream_bedrock_agent(message: str, session_id: str) -> Iterator[str]:
    """Stream AgentCore response chunks for real-time rendering."""

    if not config.AGENTCORE_RUNTIME_ARN:
        raise RuntimeError("AGENTCORE_RUNTIME_ARN is not configured in the environment.")

    actor_id = SessionManager.get_user_id() or SessionManager.get_user_email()

    payload: dict[str, Any] = {"prompt": message}
    if actor_id:
        payload["actor_id"] = actor_id

    request_payload = json.dumps(payload)
    response = _invoke_agent_runtime(session_id, request_payload)

    response_stream = response.get("response")
    if response_stream is None:
        raise RuntimeError("Agent runtime did not return a response stream.")

    buffer = ""
    raw_bytes = bytearray()
    accumulated = ""
    decoder = codecs.getincrementaldecoder("utf-8")("ignore")
    delimiter = re.compile(r"\r?\n\r?\n")

    for chunk in response_stream.iter_chunks(chunk_size=512):
        if not chunk:
            continue

        raw_bytes.extend(chunk)
        buffer += decoder.decode(chunk)

        while True:
            match = delimiter.search(buffer)
            if not match:
                break
            raw_event = buffer[: match.start()]
            buffer = buffer[match.end() :]
            payload = _parse_sse_event(raw_event)
            delta = _extract_delta_from_payload(payload)

            if delta:
                accumulated += delta
                yield delta

    buffer += decoder.decode(b"", final=True)

    while True:
        match = delimiter.search(buffer)
        if not match:
            break
        raw_event = buffer[: match.start()]
        buffer = buffer[match.end() :]
        payload = _parse_sse_event(raw_event)
        delta = _extract_delta_from_payload(payload)
        if delta:
            accumulated += delta
            yield delta

    if buffer.strip():
        payload = _parse_sse_event(buffer)
        delta = _extract_delta_from_payload(payload)
        if delta:
            accumulated += delta
            yield delta

    if not accumulated and raw_bytes:
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            fallback_text = raw_bytes.decode("utf-8", errors="ignore")
            if fallback_text:
                yield fallback_text
        else:
            text = _extract_text_from_agent_response(payload)
            if text:
                yield text


def invoke_bedrock_agent(message: str, session_id: str) -> str:
    """Invoke the configured Bedrock AgentCore runtime and return the response text."""

    if not config.AGENTCORE_RUNTIME_ARN:
        raise RuntimeError("AGENTCORE_RUNTIME_ARN is not configured in the environment.")

    actor_id = SessionManager.get_user_id() or SessionManager.get_user_email()

    payload: dict[str, Any] = {"prompt": message}
    if actor_id:
        payload["actor_id"] = actor_id

    request_payload = json.dumps(payload)
    response = _invoke_agent_runtime(session_id, request_payload)
    response_stream = response.get("response")
    if response_stream is None:
        raise RuntimeError("Agent runtime did not return a response stream.")

    raw_response = response_stream.read()
    if not raw_response:
        raise RuntimeError("Agent runtime returned an empty response.")

    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        if isinstance(raw_response, (bytes, bytearray)):
            return raw_response.decode("utf-8", errors="ignore")
        return str(raw_response)

    return _extract_text_from_agent_response(payload)


# Configure page
st.set_page_config(
    page_title="Sake Sensei 🍶",
    page_icon="🍶",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "# Sake Sensei\nAI-powered sake recommendation system"},
)

# Load custom CSS
load_custom_css()


def main():
    """Main application entry point."""

    # Header
    st.markdown('<div class="main-header">🍶 Sake Sensei</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">あなたにぴったりの日本酒を AI がご提案します</div>',
        unsafe_allow_html=True,
    )

    # Check authentication status using SessionManager
    if not SessionManager.is_authenticated():
        show_welcome_page()
    else:
        show_main_app()


def show_welcome_page():
    """Display welcome page for unauthenticated users."""

    # Hide sidebar for unauthenticated users
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        ### 🎯 Sake Sensei でできること

        **1. パーソナライズされた日本酒推薦**
        - あなたの好みに合わせた日本酒を AI が提案
        - 味わい、香り、価格帯から最適な一本を発見

        **2. テイスティング記録**
        - 飲んだ日本酒の評価を記録
        - 自分だけの酒ノートを作成

        **3. ラベル認識**
        - 写真を撮るだけで日本酒の情報を取得
        - 銘柄、蔵元、特徴を即座に確認

        """)

        # Check if we need to show confirmation form
        if st.session_state.get("pending_confirmation_email"):
            show_confirmation_form()
            return

        # Show login/signup/confirmation forms if requested
        if st.session_state.get("show_login", True):
            show_login_form()

        col_login, col_signup = st.columns(2)

        with col_signup:
            if st.button("✨ 新規登録", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()

        if st.session_state.get("show_signup", False):
            show_signup_form()


def show_login_form():
    """Display login form."""
    auth = CognitoAuth()

    st.markdown("---")
    st.markdown("### 🔐 ログイン")

    # Show error message if exists
    if "login_error" in st.session_state:
        st.error(st.session_state["login_error"])
        del st.session_state["login_error"]

    with st.form("login_form"):
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード", type="password")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("ログイン", use_container_width=True, type="primary")

        if cancel:
            st.session_state.show_login = False
            st.rerun()

        if submit:
            if email and password:
                with st.spinner("認証中..."):
                    success, message, tokens = auth.sign_in(email, password)

                    if success and tokens:
                        # Extract user info
                        user_info = tokens.get("user_info", {})
                        user_id = user_info.get("sub", email)
                        user_name = user_info.get("name", "")

                        # Store in session
                        SessionManager.login(
                            user_id=user_id,
                            email=email,
                            name=user_name,
                            access_token=tokens["access_token"],
                            id_token=tokens["id_token"],
                            refresh_token=tokens.get("refresh_token"),
                        )

                        # Load user preferences from backend
                        try:
                            from utils.backend_helper import backend_client
                            from utils.preference_converter import convert_to_display_format

                            preferences_backend = backend_client.get_user_preferences(user_id)
                            if preferences_backend:
                                # Convert backend format to display format
                                preferences_display = convert_to_display_format(preferences_backend)
                                SessionManager.set_preferences(preferences_display)
                        except Exception:
                            # If preferences fetch fails, continue without them
                            pass

                        # Clear login form state
                        st.session_state.show_login = False

                        # Rerun immediately without showing success message
                        st.rerun()
                    else:
                        st.session_state["login_error"] = message
                        st.rerun()
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")


def show_signup_form():
    """Display signup form."""
    auth = CognitoAuth()

    st.markdown("---")
    st.markdown("### ✨ 新規登録")

    with st.form("signup_form"):
        name = st.text_input("お名前", placeholder="山田 太郎")
        email = st.text_input("メールアドレス", placeholder="your.email@example.com")
        password = st.text_input("パスワード (12文字以上)", type="password")
        password_confirm = st.text_input("パスワード（確認）", type="password")

        st.info("💡 パスワード要件: 12文字以上、大文字・小文字・数字・記号を含む")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("登録", use_container_width=True, type="primary")

        if cancel:
            st.session_state.show_signup = False
            st.rerun()

        if submit:
            if name and email and password and password_confirm:
                if password != password_confirm:
                    st.error("❌ パスワードが一致しません")
                elif len(password) < 12:
                    st.error("❌ パスワードは12文字以上である必要があります")
                else:
                    with st.spinner("登録中..."):
                        success, message = auth.sign_up(email, password, name)

                        if success:
                            st.success(message)
                            st.session_state["pending_confirmation_email"] = email
                            st.session_state.show_signup = False
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.warning("⚠️ すべての項目を入力してください")


def show_confirmation_form():
    """Display confirmation code input form."""
    auth = CognitoAuth()
    email = st.session_state.get("pending_confirmation_email", "")

    st.markdown("---")
    st.markdown("### 📧 メール確認")

    # Show resend confirmation message if exists
    if "resend_message" in st.session_state:
        if st.session_state["resend_message"]["success"]:
            st.success(st.session_state["resend_message"]["text"])
        else:
            st.error(st.session_state["resend_message"]["text"])
        del st.session_state["resend_message"]

    with st.form("confirmation_form"):
        st.info(f"📨 {email} に送信された確認コードを入力してください")

        confirmation_code = st.text_input("確認コード (6桁)", placeholder="123456", max_chars=6)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col2:
            cancel = st.form_submit_button("キャンセル", use_container_width=True)
        with col3:
            submit = st.form_submit_button("確認", use_container_width=True, type="primary")

        if cancel:
            del st.session_state["pending_confirmation_email"]
            st.rerun()

        if submit:
            if confirmation_code:
                with st.spinner("確認中..."):
                    success, message = auth.confirm_sign_up(email, confirmation_code)

                    if success:
                        st.success(message)
                        del st.session_state["pending_confirmation_email"]
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("⚠️ 確認コードを入力してください")

    # Resend button outside the form
    if st.button("🔄 確認コードを再送信", use_container_width=False):
        with st.spinner("再送信中..."):
            success, message = auth.resend_confirmation_code(email)
            st.session_state["resend_message"] = {"success": success, "text": message}
            st.rerun()


def render_agent_chat():
    """Render AI chat interface with AgentCore integration."""

    # Chat header with clear button
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown("### 💬 Sake Sensei AI Chat")
    with col2:
        if st.button("🗑️ 履歴をクリア", use_container_width=True):
            SessionManager.clear_chat_history()
            SessionManager.set_agent_session_id(f"session-{uuid.uuid4().hex}")
            st.rerun()

    st.markdown("日本酒に関する質問をしてください。AI がお答えします。")

    # Initialize session state for chat
    SessionManager.init()

    # Create session ID if not exists
    if not SessionManager.get_agent_session_id():
        SessionManager.set_agent_session_id(f"session-{uuid.uuid4().hex}")

    # Chat container for messages
    chat_container = st.container(height=400, border=True)

    # Display chat history
    with chat_container:
        chat_history = SessionManager.get_chat_history()
        if not chat_history:
            st.info("👋 こんにちは！日本酒についてお気軽にご質問ください。")

        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("日本酒について質問してください..."):
        # Add user message to history
        SessionManager.add_chat_message("user", prompt)

        session_id = SessionManager.get_agent_session_id() or f"session-{uuid.uuid4().hex}"
        SessionManager.set_agent_session_id(session_id)

        try:
            with chat_container:
                st.chat_message("user").markdown(prompt)

                with st.chat_message("assistant"):
                    response_text = st.write_stream(stream_bedrock_agent(prompt, session_id))

            if not response_text:
                response_text = "エージェントからの応答がありませんでした。"

            SessionManager.add_chat_message("assistant", response_text)

        except (BotoCoreError, ClientError, RuntimeError) as error:
            error_msg = f"エラーが発生しました: {str(error)}"
            with chat_container, st.chat_message("assistant"):
                st.markdown(error_msg)
            SessionManager.add_chat_message("assistant", error_msg)
        except Exception as error:  # noqa: BLE001
            error_msg = f"予期しないエラー: {str(error)}"
            with chat_container, st.chat_message("assistant"):
                st.markdown(error_msg)
            SessionManager.add_chat_message("assistant", error_msg)

        # Rerun to display new messages
        st.rerun()


def show_ai_chat_section():
    """Display AI chat section for asking questions to Sake Sensei."""
    try:
        st.markdown("---")

        # Use agent_client component for AI chat
        render_agent_chat()

    except Exception as e:
        st.error(f"AI Chatセクションの表示中にエラーが発生しました: {str(e)}")


def show_main_app():
    """Display main application for authenticated users."""
    auth = CognitoAuth()

    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 ユーザー情報")
        user_info = SessionManager.get_user_info()
        st.write(f"**名前**: {user_info.get('name', '未設定')}")
        st.write(f"**Email**: {user_info.get('email', 'Unknown')}")

        st.markdown("---")

        if st.button("🚪 ログアウト", use_container_width=True):
            access_token = st.session_state.get("access_token")
            if access_token:
                auth.sign_out(access_token)
            SessionManager.logout()
            st.rerun()

    st.markdown("""
    ### ようこそ、Sake Sensei へ！
    """)

    # Feature cards
    st.markdown("### ✨ 機能紹介")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div class="sake-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎯</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">好み調査</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">あなたの好みを詳しく教えてください。AI がより精度の高いおすすめを提案します。</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="sake-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">AI おすすめ</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">最先端の AI があなたにぴったりの日本酒を提案します。</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="sake-card" style="text-align: center;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">⭐</div>
            <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">テイスティング記録</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">飲んだ日本酒を記録して、あなただけの酒ノートを作成。</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # AI Chat Section
    show_ai_chat_section()


if __name__ == "__main__":
    main()
