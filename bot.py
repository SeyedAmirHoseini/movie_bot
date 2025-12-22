from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import BOT_TOKEN
from admin import is_admin
from content import forward_content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("لینک صحیح نیست! مثال: /start movie")
        return

    category = args[0].lower()
    await forward_content(update, context, category)

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        await update.message.reply_text("خوش آمدید ادمین! گزینه‌های مدیریتی...")
        # اینجا میتونی InlineKeyboard یا منو اضافه کنی
    else:
        await update.message.reply_text("دستور اشتباهی وارد کردید!")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("دستور اشتباهی وارد کردید!")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))  # برای دستورهای اشتباه با /

    print("Bot is running...")
    app.run_polling()
