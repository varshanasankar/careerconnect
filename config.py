import os
from pathlib import Path

# Load .env when available (optional dependency: python-dotenv)
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except Exception:
    # dotenv not installed or .env not present — fall back to environment
    pass


class Config:
    """Configuration read from environment variables with sensible defaults."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "1234567890")

    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "varshana")
    MYSQL_DB = os.environ.get("MYSQL_DB", "careerconnect")

    MYSQL_CURSORCLASS = os.environ.get("MYSQL_CURSORCLASS", "DictCursor")

    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join("static", "uploads", "resumes")
    )

    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

    # Optional external API keys
    GSK_API_KEY = os.environ.get("GSK_API_KEY", "")