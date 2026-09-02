import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
BANK_API_URL = os.getenv("BANK_API_URL", "http://127.0.0.1:5001").rstrip("/")
PORT = int(os.getenv("PORT", "5000"))
