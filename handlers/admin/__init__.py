from telegram.ext import CallbackQueryHandler, MessageHandler, filters
from .core import callback_handler as core_callback, message_handler as core_message
from .settings import callback_handler as settings_callback, message_handler as settings_message
from .admins import callback_handler as admins_callback, message_handler as admins_message  # جدید
def register_admin_handlers(app):
    async def combined_callback(update, context):
        # اول ادمین‌ها
        if await admins_callback(update, context):
            return
        # بعد تنظیمات
        if await settings_callback(update, context):
            return
        # بعد core
        await core_callback(update, context)
    async def combined_message(update, context):
        # اول ادمین‌ها
        if await admins_message(update, context):
            return
        # بعد تنظیمات
        if await settings_message(update, context):
            return
        # بعد core
        await core_message(update, context)
    app.add_handler(CallbackQueryHandler(combined_callback))
    app.add_handler(MessageHandler(filters.ALL, combined_message))