"""
Sake Sensei - Cognito Authentication Component

Provides UI and logic for user authentication via AWS Cognito.
"""

import base64

import boto3
import streamlit as st
from botocore.exceptions import ClientError
from utils.config import config
from utils.session import SessionManager


class CognitoAuth:
    """AWS Cognito authentication handler."""

    def __init__(self):
        """Initialize Cognito client."""
        self.client = boto3.client("cognito-idp", region_name=config.COGNITO_REGION)
        self.user_pool_id = config.COGNITO_USER_POOL_ID
        self.client_id = config.COGNITO_CLIENT_ID

    def _get_secret_hash(self, username: str) -> str | None:
        """
        Calculate SECRET_HASH if client secret is configured.
        Note: Our Streamlit client is configured as a public client (no secret).

        Args:
            username: Username for secret hash (not used for public clients)
        """
        # Mark username as intentionally unused
        _ = username
        # For public clients, return None
        return None

    def sign_up(self, email: str, password: str, name: str) -> tuple[bool, str]:
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            name: User display name

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            params = {
                "ClientId": self.client_id,
                "Username": email,
                "Password": password,
                "UserAttributes": [
                    {"Name": "email", "Value": email},
                    {"Name": "name", "Value": name},
                ],
            }

            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params["SecretHash"] = secret_hash

            # Execute sign_up (response not used but call is necessary)
            _response = self.client.sign_up(**params)

            return True, "登録成功！確認コードがメールに送信されました。"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            if error_code == "UsernameExistsException":
                return False, "このメールアドレスは既に登録されています。"
            elif error_code == "InvalidPasswordException":
                return False, "パスワードが要件を満たしていません。"
            elif error_code == "InvalidParameterException":
                return False, f"入力パラメータが無効です: {error_msg}"
            else:
                return False, f"登録エラー: {error_msg}"

        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"

    def resend_confirmation_code(self, email: str) -> tuple[bool, str]:
        """
        Resend confirmation code to user email.

        Args:
            email: User email

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            params = {"ClientId": self.client_id, "Username": email}

            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params["SecretHash"] = secret_hash

            self.client.resend_confirmation_code(**params)

            return True, "確認コードを再送信しました。メールをご確認ください。"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            if error_code == "UserNotFoundException":
                return False, "ユーザーが見つかりません。"
            elif error_code == "InvalidParameterException":
                return False, "ユーザーは既に確認済みです。"
            elif error_code == "LimitExceededException":
                return False, "再送信の上限に達しました。しばらく待ってから再度お試しください。"
            else:
                return False, f"再送信エラー: {error_msg}"

        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"

    def confirm_sign_up(self, email: str, confirmation_code: str) -> tuple[bool, str]:
        """
        Confirm user registration with code.

        Args:
            email: User email
            confirmation_code: Confirmation code from email

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            params = {
                "ClientId": self.client_id,
                "Username": email,
                "ConfirmationCode": confirmation_code,
            }

            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params["SecretHash"] = secret_hash

            self.client.confirm_sign_up(**params)

            return True, "メール確認完了！ログインできます。"

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            if error_code == "CodeMismatchException":
                return False, "確認コードが正しくありません。"
            elif error_code == "ExpiredCodeException":
                return False, "確認コードの有効期限が切れています。"
            else:
                return False, f"確認エラー: {error_msg}"

        except Exception as e:
            return False, f"予期しないエラー: {str(e)}"

    def sign_in(self, email: str, password: str) -> tuple[bool, str, dict | None]:
        """
        Authenticate user.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (success: bool, message: str, tokens: Optional[dict])
        """
        try:
            params = {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "ClientId": self.client_id,
                "AuthParameters": {"USERNAME": email, "PASSWORD": password},
            }

            secret_hash = self._get_secret_hash(email)
            if secret_hash:
                params["AuthParameters"]["SECRET_HASH"] = secret_hash

            response = self.client.initiate_auth(**params)

            if "AuthenticationResult" in response:
                tokens = {
                    "access_token": response["AuthenticationResult"]["AccessToken"],
                    "id_token": response["AuthenticationResult"]["IdToken"],
                    "refresh_token": response["AuthenticationResult"].get("RefreshToken"),
                }

                # Get user attributes from ID token
                user_info = self._decode_token(tokens["id_token"])

                return True, "ログイン成功！", {**tokens, "user_info": user_info}

            elif "ChallengeName" in response:
                # Handle MFA or other challenges
                return False, f"追加認証が必要です: {response['ChallengeName']}", None

            else:
                return False, "認証に失敗しました。", None

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]

            if error_code == "NotAuthorizedException":
                return False, "メールアドレスまたはパスワードが正しくありません。", None
            elif error_code == "UserNotConfirmedException":
                return (
                    False,
                    "メールアドレスが確認されていません。確認コードを入力してください。",
                    None,
                )
            elif error_code == "UserNotFoundException":
                return False, "ユーザーが見つかりません。", None
            else:
                return False, f"ログインエラー: {error_msg}", None

        except Exception as e:
            return False, f"予期しないエラー: {str(e)}", None

    def _decode_token(self, id_token: str) -> dict:
        """
        Decode ID token to extract user info.
        Note: This is a simple implementation. For production, verify the signature.

        Args:
            id_token: JWT ID token

        Returns:
            Dictionary of user attributes
        """
        try:
            # Split token and decode payload (middle part)
            parts = id_token.split(".")
            if len(parts) != 3:
                return {}

            # Add padding if needed
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            # Decode base64
            decoded = base64.urlsafe_b64decode(payload)
            import json

            user_info = json.loads(decoded)

            return user_info

        except Exception as e:
            st.error(f"トークンのデコードに失敗: {e}")
            return {}

    def sign_out(self, access_token: str) -> tuple[bool, str]:
        """
        Sign out user (revoke tokens).

        Args:
            access_token: User's access token

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.client.global_sign_out(AccessToken=access_token)
            return True, "ログアウトしました。"

        except ClientError:
            # Even if global sign out fails, we clear local session
            return True, "ローカルセッションをクリアしました。"

        except Exception:
            return True, "ローカルセッションをクリアしました。"


def show_login_dialog():
    """Display login dialog."""
    auth = CognitoAuth()

    with st.form("login_form"):
        st.markdown("### 🔐 ログイン")

        email = st.text_input(
            "メールアドレス", placeholder="your.email@example.com", key="login_email"
        )
        password = st.text_input("パスワード", type="password", key="login_password")

        col1, col2 = st.columns([3, 1])
        with col2:
            submit = st.form_submit_button("ログイン", use_container_width=True)

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

                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("⚠️ メールアドレスとパスワードを入力してください")


def show_signup_dialog():
    """Display signup dialog."""
    auth = CognitoAuth()

    with st.form("signup_form"):
        st.markdown("### ✨ 新規登録")

        name = st.text_input("お名前", placeholder="山田 太郎", key="signup_name")
        email = st.text_input(
            "メールアドレス", placeholder="your.email@example.com", key="signup_email"
        )
        password = st.text_input("パスワード (8文字以上)", type="password", key="signup_password")
        password_confirm = st.text_input(
            "パスワード（確認）", type="password", key="signup_password_confirm"
        )

        st.info("パスワードは大文字、小文字、数字を含む8文字以上が必要です。")

        col1, col2 = st.columns([3, 1])
        with col2:
            submit = st.form_submit_button("登録", use_container_width=True)

        if submit:
            if name and email and password and password_confirm:
                if password != password_confirm:
                    st.error("❌ パスワードが一致しません")
                elif len(password) < 8:
                    st.error("❌ パスワードは8文字以上である必要があります")
                else:
                    with st.spinner("登録中..."):
                        success, message = auth.sign_up(email, password, name)

                        if success:
                            st.success(message)
                            st.session_state["pending_confirmation_email"] = email
                        else:
                            st.error(message)
            else:
                st.warning("⚠️ すべての項目を入力してください")


def show_confirmation_dialog():
    """Display confirmation code input dialog."""
    auth = CognitoAuth()
    email = st.session_state.get("pending_confirmation_email", "")

    with st.form("confirmation_form"):
        st.markdown("### 📧 メール確認")
        st.info(f"{email} に送信された確認コードを入力してください")

        confirmation_code = st.text_input(
            "確認コード", placeholder="123456", key="confirmation_code"
        )

        col1, col2 = st.columns([3, 1])
        with col2:
            submit = st.form_submit_button("確認", use_container_width=True)

        if submit:
            if confirmation_code:
                with st.spinner("確認中..."):
                    success, message = auth.confirm_sign_up(email, confirmation_code)

                    if success:
                        st.success(message)
                        del st.session_state["pending_confirmation_email"]
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("⚠️ 確認コードを入力してください")
