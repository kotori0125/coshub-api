
import sqlite3
from database import engine
from sqlalchemy import inspect

db_path = "coshub.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("正在检查和更新数据库...")

# 检查 users 表
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns('users')]
print(f"现有 users 表列: {columns}")

if 'points' not in columns:
    print("添加 users.points 列...")
    cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    conn.commit()

# 检查 follows 表是否存在
tables = inspector.get_table_names()
print(f"现有表: {tables}")

if 'follows' not in tables:
    print("创建 follows 表...")
    cursor.execute("""
        CREATE TABLE follows (
            id INTEGER PRIMARY KEY,
            follower_id INTEGER,
            following_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

if 'point_logs' not in tables:
    print("创建 point_logs 表...")
    cursor.execute("""
        CREATE TABLE point_logs (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            action TEXT,
            points INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

if 'comments' in tables:
    comment_cols = [col['name'] for col in inspector.get_columns('comments')]
    if 'author_id' not in comment_cols:
        print("添加 comments.author_id 列...")
        cursor.execute("ALTER TABLE comments ADD COLUMN author_id INTEGER")
        conn.commit()

print("✅ 数据库更新完成！")
conn.close()
