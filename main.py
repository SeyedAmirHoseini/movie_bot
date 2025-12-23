from telegram.ext import Application
from config import BOT_TOKEN
from database.db import init_db
# هندلرها
from handlers.user import register_user_handlers
from handlers.admin import register_admin_handlers
def main():
    # ساخت دیتابیس در اولین اجرا
    init_db()
   
    app = Application.builder().token(BOT_TOKEN).build()
    register_user_handlers(app)
    register_admin_handlers(app)
    print("Bot running...")
    app.run_polling()
if __name__ == "__main__":
    main()