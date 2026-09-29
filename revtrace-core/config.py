import os
from dotenv import load_dotenv

load_dotenv()

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io",
)

HINDSIGHT_API_KEY = os.getenv(
    "HINDSIGHT_API_KEY",
    "",
)

HINDSIGHT_SHARED_BANK_ID = os.getenv(
    "HINDSIGHT_SHARED_BANK_ID",
    "revtrace-shared-memory",
)