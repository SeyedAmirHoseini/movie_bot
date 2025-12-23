from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .utils import is_admin
MAIN_MENU = [
    [InlineKeyboardButton("📤 آپلود آیتم", callback_data="core_upload")],
    [InlineKeyboardButton("🔗 ساخت لینک آیتم", callback_data="core_make_link")],
    [InlineKeyboardButton("❌ حذف آیتم", callback_data="core_delete")],
    [InlineKeyboardButton("⚙️ تنظیمات ربات", callback_data="settings_menu")],
]
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        if update.message:
            await update.message.reply_text("⛔️ دسترسی غیرمجاز")
        elif update.callback_query:
            await update.callback_query.edit_message_text("⛔️ دسترسی غیرمجاز")
        return
    text = "👋 سلام ادمین!\nیکی از گزینه‌ها رو انتخاب کن:"
    markup = InlineKeyboardMarkup(MAIN_MENU)
    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)