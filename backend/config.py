# Configuration file for the application
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Application Configuration
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File upload settings
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx'}

# Embedding settings
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L12-v2"
EMBEDDING_DIMENSION = 384

# RAG settings
DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 40
DEFAULT_K = 4
