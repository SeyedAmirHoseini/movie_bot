import hmac
import hashlib
import sqlite3
from dotenv import load_dotenv
from database.db import DB_FILE
from config import BOT_TOKEN, ADMIN_HASH


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

# تابع جدید: بروزرسانی دسترسی‌های یک ادمین موجود
def update_admin_permissions(user_id: int, can_videos: bool, can_settings: bool, can_admins: bool):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE admins 
        SET can_manage_videos = ?, can_access_settings = ?, can_manage_admins = ?
        WHERE user_id = ?
    ''', (int(can_videos), int(can_settings), int(can_admins), user_id))
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

# تابع جدید: گرفتن دسترسی‌های یک ادمین خاص
def get_admin_permissions(user_id: int) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT can_manage_videos, can_access_settings, can_manage_admins FROM admins WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "videos": bool(row[0]),
            "settings": bool(row[1]),
            "admins": bool(row[2])
        }
    return {"videos": False, "settings": False, "admins": False}

def is_admin(user_id: int) -> bool:
    hashed = generate_hash(user_id)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ? AND hash = ?", (user_id, hashed))
    exists = cursor.fetchone()
    conn.close()
    if exists:
        return True
    if hashed == ADMIN_HASH:
        add_admin(user_id, hashed, True, True, True)
        return True
    return False

def check_permission(user_id: int, permission: str) -> bool:
    hashed = generate_hash(user_id)
    if hashed == ADMIN_HASH:  # سوپر ادمین همیشه همه دسترسی‌ها رو داره
        return True

    if not is_admin(user_id):
        return False

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