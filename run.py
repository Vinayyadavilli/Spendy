import uvicorn
import os
from dotenv import load_dotenv
from app.core.database import check_db_connection
from app.core.config import settings

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print("\n" + "=" * 60)
    print("🚀 SPEND TRACKER FASTAPI BACKEND STARTUP")
    print("=" * 60)
    print(f"• Server URL:     http://{host}:{port}")
    print(f"• Swagger Docs:   http://localhost:{port}/docs")
    print(f"• Health Check:   http://localhost:{port}/api/health")
    print("-" * 60)
    print(f"• MySQL Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"• DB User:        {settings.DB_USER}")

    is_connected, msg = check_db_connection()
    if is_connected:
        print(f"• DB Status:      ✅ {msg}")
    else:
        print(f"• DB Status:      ⚠️ {msg}")
        print("\n💡 NOTE: If you need to change your MySQL credentials, edit 'backend/.env'.")
        print("  You can also test the database directly by running:")
        print("  python3 test_db_connection.py")
    print("=" * 60 + "\n")

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
