from dotenv import load_dotenv
import os
from pathlib import Path

# load .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

OPENROUTER_API_KEY =os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
if OPENROUTER_MODEL.endswith(":free"):
	OPENROUTER_MODEL = "openai/gpt-4o-mini"
OPENROUTER_URL =os.getenv("OPENROUTER_URL","https://openrouter.ai/api/v1/chat/completions")


MONGO_URL = os.getenv("MONGO_URL") or os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME","education_ai")