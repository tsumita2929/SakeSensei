"""
Sake Sensei - Configuration Management

Loads configuration from environment variables and provides app-wide settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """
    Application configuration.

    All environment-specific settings are loaded from environment variables.
    See .env.example for a complete list of available configuration options.

    IMPORTANT:
    - All region-specific settings default to us-west-2
    - Change AWS_REGION in .env to deploy to different regions
    - Ensure Bedrock Claude 4.5 Sonnet is available in your target region
    """

    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")

    # Cognito Configuration
    COGNITO_REGION = os.getenv("COGNITO_REGION", AWS_REGION)
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")  # Optional
    COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "")

    # AgentCore Configuration
    AGENTCORE_GATEWAY_URL = os.getenv("AGENTCORE_GATEWAY_URL", "")
    AGENTCORE_GATEWAY_ID = os.getenv("AGENTCORE_GATEWAY_ID")
    AGENTCORE_GATEWAY_ARN = os.getenv("AGENTCORE_GATEWAY_ARN")
    AGENTCORE_RUNTIME_URL = os.getenv("AGENTCORE_RUNTIME_URL", "")
    AGENTCORE_RUNTIME_ARN = os.getenv("AGENTCORE_RUNTIME_ARN", "")
    AGENTCORE_AGENT_ID = os.getenv("AGENTCORE_AGENT_ID", "")
    AGENTCORE_AGENT_ALIAS_ID = os.getenv("AGENTCORE_AGENT_ALIAS_ID", "")

    # Application Configuration
    APP_NAME = os.getenv("APP_NAME", "Sake Sensei")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

    # Streamlit Configuration
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        required_vars = [
            "AWS_REGION",
            "COGNITO_USER_POOL_ID",
            "COGNITO_CLIENT_ID",
        ]

        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            print(f"⚠️  Missing required configuration: {', '.join(missing)}")
            return False

        return True

    @classmethod
    def get_info(cls) -> dict:
        """Get configuration summary for debugging."""
        return {
            "AWS Region": cls.AWS_REGION,
            "Cognito User Pool": cls.COGNITO_USER_POOL_ID,
            "AgentCore Gateway": cls.AGENTCORE_GATEWAY_ID,
            "Environment": cls.APP_ENV,
            "Debug Mode": cls.APP_DEBUG,
        }


# Create config instance
config = Config()

# Validate on import
if not config.validate():
    print("⚠️  Warning: Some required configuration is missing. App may not function correctly.")
    print("Please check your .env file and ensure all required variables are set.")
