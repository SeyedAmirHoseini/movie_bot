import hmac
import hashlib
from config import ADMIN_HASH, BOT_TOKEN
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def is_admin(telegram_id: int) -> bool:
    """بررسی دسترسی ادمین با HMAC"""
    msg = str(telegram_id).encode()
    key = BOT_TOKEN.encode()
    hash_digest = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hash_digest == ADMIN_HASH


async def send_admin_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("اضافه کردن دسته", callback_data="add_category")],
        [InlineKeyboardButton("حذف دسته", callback_data="remove_category")],
        [InlineKeyboardButton("مشاهده پیام‌ها", callback_data="view_messages")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("خوش آمدید ادمین:", reply_markup=reply_markup)
