import hmac
import hashlib
from telegram import InlineKeyboardButton
from config import BOT_TOKEN
from database.admin_helper import is_admin  # حالا از helper استفاده می‌کنه
def back_button():
    return [InlineKeyboardButton("🔙 برگشت به منو", callback_data="back_to_main")]