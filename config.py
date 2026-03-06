import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data.db")))
TMP_DIR = Path(os.getenv("TMP_DIR", "/tmp/data_tool_downloads"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")

LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB
JOB_TTL_SECONDS = 300  # 5 minutes
