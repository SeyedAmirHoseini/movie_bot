import sqlite3
import os

# مسیر دیتابیس
DB_FILE = "data/bot.db"

# اطمینان از وجود پوشه data
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)


def init_db():
    """
    ایجاد دیتابیس و جدول‌ها در صورت عدم وجود
    این تابع فقط یک بار (در اولین اجرا) فراخوانی می‌شه
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # جدول تنظیمات ربات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL  -- 0 = False, 1 = True
        )
    ''')

    # تنظیمات پیش‌فرض
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('delete_after_2min', 0)")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('require_join', 0)")

    # جدول چنل‌های اجباری برای عضویت
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE NOT NULL
        )
    ''')

    # جدول ادمین‌ها (با سیستم دسترسی پیشرفته)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            hash TEXT NOT NULL,
            can_manage_videos INTEGER DEFAULT 1,
            can_access_settings INTEGER DEFAULT 1,
            can_manage_admins INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


# توابع مربوط به تنظیمات ربات
def get_setting(key: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False


def set_setting(key: str, value: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, int(value)))
    conn.commit()
    conn.close()


# توابع مربوط به چنل‌های اجباری
def add_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO required_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()
    conn.close()


def remove_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()


def get_required_channels() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM required_channels")
    channels = [row[0] for row in cursor.fetchall()]
    conn.close()
    return channels