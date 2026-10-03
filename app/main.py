import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from .core.config import settings
from .core.database import Base, engine, get_db, check_db_connection
from .routers import auth, bank_accounts, transactions, sms_parser

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
except Exception as e:
    logger.warning(f"Could not initialize tables on start: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for Flutter Web / Mobile / Desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(bank_accounts.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(sms_parser.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    is_ok, msg = check_db_connection()
    return {
        "message": "Spend Tracker & SMS Extractor API is running!",
        "database_connected": is_ok,
        "database_status": msg,
        "docs": "/docs",
        "mysql_database": settings.DB_NAME,
    }

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    is_ok, msg = check_db_connection()
    table_count = 0
    try:
        table_count = len(inspect(engine).get_table_names())
    except Exception:
        pass

    return {
        "status": "healthy" if is_ok else "database_disconnected",
        "mysql_connected": is_ok,
        "details": msg,
        "host": settings.DB_HOST,
        "port": settings.DB_PORT,
        "database": settings.DB_NAME,
        "tables_count": table_count,
    }
