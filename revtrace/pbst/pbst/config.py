import os
from dotenv import load_dotenv

REVTRACE_CORE_URL = os.getenv(
    "REVTRACE_CORE_URL",
    "http://127.0.0.1:8100",
)

load_dotenv()

HINDSIGHT_URL = os.getenv(
    "HINDSIGHT_URL",
    "http://localhost:8888"
)

HINDSIGHT_BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "proposal-agent"
)

HINDSIGHT_API_KEY = os.getenv(
    "HINDSIGHT_API_KEY",
    ""
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    ""
)

GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

DATA_DIR = "data"
OUTPUT_DIR = "outputs"
PROMPT_DIR = "prompts"
