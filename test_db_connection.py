import os
import sys
from dotenv import load_dotenv
import pymysql

load_dotenv()

def test_mysql_connection():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "root")
    db_name = os.getenv("DB_NAME", "spent_tracker_db")

    print("\n" + "=" * 60)
    print("🔍 TESTING MYSQL DATABASE CONNECTION")
    print("=" * 60)
    print(f"• Host:     {host}:{port}")
    print(f"• User:     {user}")
    print(f"• Password: {'*' * len(password) if password else '(empty)'}")
    print(f"• Database: {db_name}")
    print("-" * 60)

    # Step 1: Connect to MySQL server without database
    print("\n[Step 1/3] Connecting to MySQL Server...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=5,
            autocommit=True,
        )
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
        print(f"  ✅ SUCCESS: Connected to MySQL Server! (Version: {version})")
    except pymysql.err.OperationalError as e:
        err_code, err_msg = e.args
        print(f"  ❌ FAILED to connect to MySQL Server:")
        print(f"     Error Code {err_code}: {err_msg}")
        if err_code == 1045:
            print("\n💡 HOW TO FIX (Access Denied / Password Error):")
            print(f"   1. Open 'backend/.env'")
            print(f"   2. Update 'DB_PASSWORD=your_actual_mysql_password'")
            print(f"   3. If you don't have a password set, use 'DB_PASSWORD='")
        elif err_code == 2003:
            print("\n💡 HOW TO FIX (Can't connect to MySQL server):")
            print("   Ensure your MySQL server is running (e.g. 'brew services start mysql' or MySQL Workbench).")
        print("=" * 60 + "\n")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

    # Step 2: Ensure database exists
    print(f"\n[Step 2/3] Checking Database '{db_name}'...")
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            cursor.execute("SHOW DATABASES LIKE %s;", (db_name,))
            res = cursor.fetchone()
            if res:
                print(f"  ✅ SUCCESS: Database '{db_name}' is ready.")
        conn.close()
    except Exception as e:
        print(f"  ❌ Error creating database '{db_name}': {e}")
        return False

    # Step 3: Test SQLAlchemy Engine and Tables
    print("\n[Step 3/3] Initializing SQLAlchemy Tables...")
    try:
        from app.core.database import engine, Base
        from app.models.user import User
        from app.models.bank_account import BankAccount
        from app.models.transaction import Transaction

        Base.metadata.create_all(bind=engine)
        print("  ✅ SUCCESS: Tables ('users', 'bank_accounts', 'transactions') verified/created.")
    except Exception as e:
        print(f"  ❌ SQLAlchemy table creation error: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL DATABASE CHECKS PASSED! Database is fully connected.")
    print("=" * 60 + "\n")
    return True

if __name__ == "__main__":
    success = test_mysql_connection()
    sys.exit(0 if success else 1)
