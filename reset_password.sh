#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TMP_SQL="/tmp/mysql_reset_init.sql"

echo "============================================================"
echo "🔧 RESETTING MYSQL ROOT PASSWORD TO 'Admin@123'"
echo "============================================================"

# 1. Create world-readable SQL file in /tmp so _mysql system user can read it
cat << 'EOF' > "$TMP_SQL"
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Admin@123';
ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'Admin@123';
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'Admin@123';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
chmod 777 "$TMP_SQL"

echo "1. Stopping existing macOS MySQL service..."
launchctl unload -w /Library/LaunchDaemons/com.oracle.oss.mysql.mysqld.plist 2>/dev/null || true
pkill -9 mysqld 2>/dev/null || true
sleep 2

echo "2. Applying password reset directly to MySQL data directory..."
/usr/local/mysql/bin/mysqld --user=_mysql --init-file="$TMP_SQL" &
INIT_PID=$!
sleep 6

echo "3. Stopping initialization daemon..."
kill -9 $INIT_PID 2>/dev/null || true
pkill -9 mysqld 2>/dev/null || true
rm -f "$TMP_SQL"
sleep 2

echo "4. Reloading macOS MySQL service..."
launchctl load -w /Library/LaunchDaemons/com.oracle.oss.mysql.mysqld.plist 2>/dev/null || true
sleep 4

echo "5. Testing connection with new password 'Admin@123'..."
"$DIR/venv/bin/python3" "$DIR/test_db_connection.py"
