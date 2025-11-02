import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load .env from the same directory as config.py
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
