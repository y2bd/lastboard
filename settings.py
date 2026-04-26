import os

from dotenv import load_dotenv

load_dotenv()

REC_BASE_URL: str = os.getenv("REC_BASE_URL", "")
REC_API_BASE_URL: str = os.getenv("REC_API_BASE_URL", "")
DEFAULT_REC_USER: str = os.getenv("DEFAULT_REC_USER", "")
LAST_FM_API_KEY: str = os.getenv("LAST_FM_API_KEY", "")
DEFAULT_LAST_FM_USER: str = os.getenv("DEFAULT_LAST_FM_USER", "")
