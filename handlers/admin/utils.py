import hmac
import hashlib
from telegram import InlineKeyboardButton
from config import ADMIN_HASH, BOT_TOKEN
def is_admin(user_id: int) -> bool:
    user_bytes = str(user_id).encode()
    token_bytes = BOT_TOKEN.encode()
    hashed = hmac.new(token_bytes, user_bytes, hashlib.sha256).hexdigest()
    return hashed == ADMIN_HASH
def back_button():
    return [InlineKeyboardButton("🔙 برگشت به منو", callback_data="back_to_main")]