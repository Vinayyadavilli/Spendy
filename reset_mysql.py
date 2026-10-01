import subprocess
import time
import os
import pymysql

def reset_homebrew_mysql_password():
    print("Step 1: Starting Homebrew MySQL on port 3307 with --skip-grant-tables...")
    proc = subprocess.Popen([
        "/opt/homebrew/bin/mysqld",
        "--skip-grant-tables",
        "--port=3307",
        "--datadir=/opt/homebrew/var/mysql",
        "--socket=/tmp/mysql_reset.sock"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(3)

    print("Step 2: Connecting to reset password to Admin@123...")
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3307,
            user="root",
            password="",
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute("FLUSH PRIVILEGES;")
            try:
                cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY 'Admin@123';")
            except Exception as e:
                print(f"ALTER USER localhost: {e}")
            try:
                cursor.execute("ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'Admin@123';")
            except Exception as e:
                print(f"ALTER USER 127.0.0.1: {e}")
            cursor.execute("FLUSH PRIVILEGES;")
        conn.close()
        print("✅ Password successfully set to 'Admin@123'!")
    except Exception as e:
        print(f"❌ Failed to set password: {e}")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    reset_homebrew_mysql_password()
