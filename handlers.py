from telegram.ext import CommandHandler, ContextTypes
from telegram import Update
from config import CATEGORY_CHANNELS
from admin import is_admin, show_admin_menu
import base64

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        param = context.args[0] if context.args else None

        if not param:
            await update.message.reply_text("سلام! چیزی برای نمایش وجود ندارد.")
            return

        # decode Base64
        decoded = base64.urlsafe_b64decode(param.encode()).decode()
        # format: "movie:123,124,125"
        category, msg_ids_str = decoded.split(":")
        msg_ids = [int(mid) for mid in msg_ids_str.split(",")]

        target_chat = CATEGORY_CHANNELS.get(category)
        if not target_chat:
            await update.message.reply_text("دسته‌بندی پیدا نشد")
            return

        # هر پیام رو جداگانه کپی می‌کنیم
        for msg_id in msg_ids:
            await context.bot.copy_message(
                chat_id=update.effective_user.id,
                from_chat_id=target_chat,
                message_id=msg_id
            )

    except Exception:
        await update.message.reply_text("لینک اشتباه است!")

async def admin_command(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دستور اشتباهی وارد کردید")
        return
    await show_admin_menu(update, context)
