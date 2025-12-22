from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN
from admin import register_admin_handlers
from handlers import *

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_command))
    register_admin_handlers(app)

    print("Bot running...")
    app.run_polling()



if __name__ == "__main__":
    main()
