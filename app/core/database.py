import logging
import os
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def check_db_connection() -> tuple[bool, str]:
    """Tests server connectivity and database readiness."""
    if os.getenv("DATABASE_URL"):
        return True, f"Using cloud database URL ({settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'})"

    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=4,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()
        return True, f"Connected to MySQL {version}, database '{settings.DB_NAME}' ready."
    except pymysql.err.OperationalError as e:
        err_code, err_msg = e.args
        if err_code == 1045:
            return False, f"Access denied for user '{settings.DB_USER}'. Please check DB_PASSWORD in backend/.env."
        elif err_code == 2003:
            return False, f"Cannot connect to MySQL server at {settings.DB_HOST}:{settings.DB_PORT}. Is MySQL running?"
        return False, f"MySQL Operational Error ({err_code}): {err_msg}"
    except Exception as e:
        return False, f"Database connection error: {str(e)}"

# Run check
is_connected, db_message = check_db_connection()
if is_connected:
    logger.info(f"✅ {db_message}")
else:
    logger.warning(f"⚠️ {db_message}")

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
except Exception as e:
    logger.error(f"Failed to create MySQL engine with URL {settings.DATABASE_URL}: {e}")
    # Fallback to local SQLite if MySQL isn't reachable
    engine = create_engine("sqlite:///./fallback_spent_tracker.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
