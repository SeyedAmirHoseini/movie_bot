from config import CATEGORY_CHANNELS, DELETE_DELAY
from telegram import Update
from telegram.ext import ContextTypes, JobQueue

async def forward_content(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """فوروارد پیام از چنل به کاربر و زمان‌بندی حذف پیام"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if category not in CATEGORY_CHANNELS:
        await update.message.reply_text("دسته‌بندی یافت نشد!")
        return

    channel_id = CATEGORY_CHANNELS[category]

    # فوروارد آخرین پیام (می‌تونی Message ID مشخص بذاری)
    forwarded = await context.bot.forward_message(chat_id=chat_id,
                                                  from_chat_id=channel_id,
                                                  message_id=(await context.bot.get_chat_history(channel_id, limit=1))[0].message_id)

    # زمان‌بندی حذف پیام بعد DELETE_DELAY ثانیه
    context.job_queue.run_once(delete_message, DELETE_DELAY, chat_id=chat_id, data=forwarded.message_id)

async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    """حذف پیام"""
    chat_id = context.job.chat_id
    message_id = context.job.data
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass
