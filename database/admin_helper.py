import hmac
import hashlib
import sqlite3
import os
from dotenv import load_dotenv
from database.db import DB_FILE
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_HASH = os.getenv("ADMIN_HASH")  # هش سوپر ادمین
def generate_hash(user_id: int) -> str:
    user_bytes = str(user_id).encode()
    token_bytes = BOT_TOKEN.encode()
    return hmac.new(token_bytes, user_bytes, hashlib.sha256).hexdigest()
def add_admin(user_id: int, hash_val: str, can_videos: bool, can_settings: bool, can_admins: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO admins (user_id, hash, can_manage_videos, can_access_settings, can_manage_admins)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, hash_val, int(can_videos), int(can_settings), int(can_admins)))
    conn.commit()
    conn.close()
def remove_admin(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
def get_admins() -> list:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, hash, can_manage_videos, can_access_settings, can_manage_admins FROM admins")
    admins = cursor.fetchall()
    conn.close()
    return admins
def is_admin(user_id: int) -> bool:
    hashed = generate_hash(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ? AND hash = ?", (user_id, hashed))
    exists = cursor.fetchone()
    conn.close()
    if exists:
        return True
    # اگر نبود و هش برابر ADMIN_HASH بود (سوپر ادمین)، اضافه کن
    if hashed == ADMIN_HASH:
        add_admin(user_id, hashed, True, True, True)
        return True
    return False
def check_permission(user_id: int, permission: str) -> bool:
    if not is_admin(user_id):  # اول چک ادمین بودن
        return False
    # برای 'any' فقط ادمین بودن کافیه
    if permission == 'any':
        return True
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if permission == 'manage_videos':
        cursor.execute("SELECT can_manage_videos FROM admins WHERE user_id = ?", (user_id,))
    elif permission == 'access_settings':
        cursor.execute("SELECT can_access_settings FROM admins WHERE user_id = ?", (user_id,))
    elif permission == 'manage_admins':
        cursor.execute("SELECT can_manage_admins FROM admins WHERE user_id = ?", (user_id,))
    else:
        conn.close()
        return False
    row = cursor.fetchone()
    conn.close()
    return bool(row[0]) if row else False