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

    # CDK Configuration (defaults to AWS_REGION)
    CDK_DEFAULT_REGION = os.getenv("CDK_DEFAULT_REGION", AWS_REGION)
    CDK_DEFAULT_ACCOUNT = os.getenv("CDK_DEFAULT_ACCOUNT", AWS_ACCOUNT_ID)

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
    AGENTCORE_MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID")
    AGENTCORE_MEMORY_TTL = int(os.getenv("AGENTCORE_MEMORY_TTL", "86400"))

    # Lambda Function ARNs
    LAMBDA_RECOMMENDATION_ARN = os.getenv("LAMBDA_RECOMMENDATION_ARN")
    LAMBDA_PREFERENCE_ARN = os.getenv("LAMBDA_PREFERENCE_ARN")
    LAMBDA_TASTING_ARN = os.getenv("LAMBDA_TASTING_ARN")
    LAMBDA_BREWERY_ARN = os.getenv("LAMBDA_BREWERY_ARN")
    LAMBDA_IMAGE_RECOGNITION_ARN = os.getenv("LAMBDA_IMAGE_RECOGNITION_ARN")

    # DynamoDB Configuration
    DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "")  # For local dev
    DYNAMODB_USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "SakeSensei-Users")
    DYNAMODB_SAKE_TABLE = os.getenv("DYNAMODB_SAKE_TABLE", "SakeSensei-SakeMaster")
    DYNAMODB_BREWERY_TABLE = os.getenv("DYNAMODB_BREWERY_TABLE", "SakeSensei-BreweryMaster")
    DYNAMODB_TASTING_TABLE = os.getenv("DYNAMODB_TASTING_TABLE", "SakeSensei-TastingRecords")

    # S3 Configuration
    S3_BUCKET_IMAGES = os.getenv("S3_BUCKET_IMAGES", f"sakesensei-images-{AWS_ACCOUNT_ID or 'dev'}")
    S3_BUCKET_REGION = os.getenv("S3_BUCKET_REGION", AWS_REGION)

    # Application Configuration
    APP_NAME = os.getenv("APP_NAME", "Sake Sensei")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")

    # Bedrock Model Configuration
    # Using inference profile for Sonnet 4.5
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
    BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.7"))
    BEDROCK_STREAMING = os.getenv("BEDROCK_STREAMING", "true").lower() == "true"

    # Vision Model Configuration
    VISION_MODEL_ID = os.getenv("VISION_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    IMAGE_MAX_SIZE_MB = int(os.getenv("IMAGE_MAX_SIZE_MB", "5"))
    IMAGE_ALLOWED_TYPES = os.getenv("IMAGE_ALLOWED_TYPES", "image/jpeg,image/png,image/webp")

    # Recommendation Algorithm Settings
    RECOMMENDATION_MAX_RESULTS = int(os.getenv("RECOMMENDATION_MAX_RESULTS", "5"))
    RECOMMENDATION_DIVERSITY_WEIGHT = float(os.getenv("RECOMMENDATION_DIVERSITY_WEIGHT", "0.3"))
    RECOMMENDATION_COLLABORATIVE_WEIGHT = float(
        os.getenv("RECOMMENDATION_COLLABORATIVE_WEIGHT", "0.3")
    )
    RECOMMENDATION_CONTENT_WEIGHT = float(os.getenv("RECOMMENDATION_CONTENT_WEIGHT", "0.4"))

    # Streamlit Configuration
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    # Feature Flags
    FEATURE_IMAGE_RECOGNITION = os.getenv("FEATURE_IMAGE_RECOGNITION", "true").lower() == "true"
    FEATURE_FOOD_PAIRING = os.getenv("FEATURE_FOOD_PAIRING", "true").lower() == "true"
    FEATURE_SOCIAL_SHARING = os.getenv("FEATURE_SOCIAL_SHARING", "false").lower() == "true"
    FEATURE_EXPORT_HISTORY = os.getenv("FEATURE_EXPORT_HISTORY", "true").lower() == "true"

    # Development/Testing Flags
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
    DEBUG_SQL_QUERIES = os.getenv("DEBUG_SQL_QUERIES", "false").lower() == "true"
    DEBUG_API_REQUESTS = os.getenv("DEBUG_API_REQUESTS", "false").lower() == "true"

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
            "AgentCore Memory": cls.AGENTCORE_MEMORY_ID,
            "Environment": cls.APP_ENV,
            "Debug Mode": cls.APP_DEBUG,
        }


# Create config instance
config = Config()

# Validate on import
if not config.validate():
    print("⚠️  Warning: Some required configuration is missing. App may not function correctly.")
    print("Please check your .env file and ensure all required variables are set.")
