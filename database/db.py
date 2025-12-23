import sqlite3

DB_FILE = "data/bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
   
    # جدول تنظیمات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL -- 0 = False, 1 = True
        )
    ''')
   
    # تنظیمات پیش‌فرض
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('delete_after_2min', 0)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('require_join', 0)")
   
    # جدول چنل‌های اجباری
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL
        )
    ''')
   
    conn.commit()
    conn.close()
# خواندن تنظیم
def get_setting(key: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False
# تغییر تنظیم (توگل)
def set_setting(key: str, value: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, int(value)))
    conn.commit()
    conn.close()
# اضافه کردن چنل اجباری
def add_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO required_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()
# حذف چنل اجباری
def remove_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
# لیست چنل‌های اجباری
def get_required_channels() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM required_channels")
    channels = [row[0] for row in cursor.fetchall()]
    conn.close()
    return channels
