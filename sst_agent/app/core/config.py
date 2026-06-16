"""Centralized application settings."""

from dotenv import load_dotenv
import os


load_dotenv()

PROJECT_NAME = "SST Agent"
VERSION = "0.1"
DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# PostgreSQL Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Embeddings
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3002,http://127.0.0.1:3002",
    ).split(",")
    if origin.strip()
]
