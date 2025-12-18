# Este archivo centraliza configuración.
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_NAME = "SST Agent"
VERSION = "0.1"
DEBUG = True

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# PostgreSQL Database
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/sst_agent"
)

# Embeddings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimensión del modelo all-MiniLM-L6-v2
