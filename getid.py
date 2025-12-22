from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN

async def get_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    print("✅ CHANNEL FOUND")
    print("Title:", chat.title)
    print("ID:", chat.id)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # handler برای پیام‌های کانال
    channel_handler = MessageHandler(filters.ChatType.CHANNEL, get_channel_id)
    app.add_handler(channel_handler)

    print("Bot is listening for channel posts...")
    app.run_polling()

if __name__ == "__main__":
    main()
