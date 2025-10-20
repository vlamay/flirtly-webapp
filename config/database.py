# config/database.py - Database configuration

import os
from dotenv import load_dotenv

load_dotenv()

# Database URLs
SQLITE_URL = "sqlite+aiosqlite:///./flirtly.db"
POSTGRES_URL = "postgresql+asyncpg://flirtly_user:your_password@localhost/flirtly"

# Environment variable to choose database
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"

# Current database URL
DATABASE_URL = POSTGRES_URL if USE_POSTGRES else SQLITE_URL

# Database settings
DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

print(f"🗄️ Database: {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")
print(f"📍 URL: {DATABASE_URL}")
print(f"📊 Echo: {DB_ECHO}")
