import asyncio
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import CATEGORY_CHANNELS
from handlers.admin.utils import is_admin
from handlers.admin.menu import show_admin_menu
from database.db import get_setting, get_required_channels
import base64
# سشن برای ذخیره param لینک
join_check_session = {}
# تابع جدا برای حذف background
async def schedule_deletion(context: ContextTypes.DEFAULT_TYPE, user_id: int, message_ids: list):
    await asyncio.sleep(120) # ۲ دقیقه صبر
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
        except:
            pass # اگر پیام حذف شده یا دسترسی نباشه، ارور نده
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    try:
        param = context.args[0] if context.args else None
        if not param:
            await message.reply_text("سلام! چیزی برای نمایش وجود ندارد.")
            return
        join_check_session[user_id] = param
        decoded = base64.urlsafe_b64decode(param.encode()).decode()
        category, msg_ids_str = decoded.split(":")
        msg_ids = [int(mid) for mid in msg_ids_str.split(",")]
        target_chat = CATEGORY_CHANNELS.get(category)
        if not target_chat:
            await message.reply_text("دسته‌بندی پیدا نشد")
            return
        # چک عضویت اجباری
        if get_setting('require_join'):
            channels = get_required_channels()
            if channels:
                not_joined = []
                for ch_id in channels:
                    try:
                        member = await context.bot.get_chat_member(ch_id, user_id)
                        if member.status in ('left', 'kicked'):
                            not_joined.append(ch_id)
                    except:
                        not_joined.append(ch_id)
                if not_joined:
                    keyboard = []
                    for ch_id in not_joined:
                        try:
                            chat = await context.bot.get_chat(ch_id)
                            title = chat.title or "چنل"
                            url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(ch_id)[4:]}"
                            keyboard.append([InlineKeyboardButton(f"عضویت در {title}", url=url)])
                        except:
                            keyboard.append([InlineKeyboardButton(f"عضویت در چنل {ch_id}", url=f"https://t.me/joinchat/{ch_id}")])
                    keyboard.append([InlineKeyboardButton("✅ تأیید عضویت", callback_data="confirm_join")])
                    await message.reply_text(
                        "⚠️ برای مشاهده محتوا، ابتدا در چنل‌های زیر عضو شوید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return
        # ارسال محتوا
        sent_messages = []
        for msg_id in msg_ids:
            sent = await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=target_chat,
                message_id=msg_id
            )
            sent_messages.append(sent.message_id)
        # پیام اطلاع‌رسانی (اختیاری)
        notice = None
        if get_setting('delete_after_2min'):
            notice = await message.reply_text("📌 این محتوا بعد از ۲ دقیقه حذف می‌شود.")
        # اجرای حذف در پس‌زمینه (بدون بلاک کردن هندلر)
        if get_setting('delete_after_2min'):
            # ایجاد تسک background
            context.application.create_task(schedule_deletion(context, user_id, sent_messages + ([notice.message_id] if notice else [])))
        # پاک کردن سشن
        join_check_session.pop(user_id, None)
    except Exception:
        await message.reply_text("لینک اشتباه است یا مشکلی پیش آمد!")
async def confirm_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in join_check_session:
        await query.edit_message_text("❌ جلسه منقضی شده. دوباره لینک رو بزنید.")
        return
    param = join_check_session[user_id]
    try:
        decoded = base64.urlsafe_b64decode(param.encode()).decode()
        category = decoded.split(":")[0]
        if get_setting('require_join'):
            channels = get_required_channels()
            if channels:
                not_joined = []
                for ch_id in channels:
                    try:
                        member = await context.bot.get_chat_member(ch_id, user_id)
                        if member.status in ('left', 'kicked'):
                            not_joined.append(ch_id)
                    except:
                        not_joined.append(ch_id)
                if not_joined:
                    keyboard = []
                    for ch_id in not_joined:
                        try:
                            chat = await context.bot.get_chat(ch_id)
                            title = chat.title or "چنل"
                            url = f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(ch_id)[4:]}"
                            keyboard.append([InlineKeyboardButton(f"عضویت در {title}", url=url)])
                        except:
                            keyboard.append([InlineKeyboardButton(f"عضویت در چنل {ch_id}", url=f"https://t.me/joinchat/{ch_id}")])
                    keyboard.append([InlineKeyboardButton("✅ تأیید مجدد عضویت", callback_data="confirm_join")])
                    await query.edit_message_text(
                        "⚠️ هنوز در همه چنل‌ها عضو نشده‌اید. لطفاً جوین کنید و دوباره تأیید کنید:",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    return
        await query.edit_message_text("✅ عضویت تأیید شد! در حال ارسال محتوا...")
        await send_content(query.message, context, param, user_id)
    except Exception:
        await query.edit_message_text("❌ مشکلی پیش آمد. دوباره روی لینک کلیک کنید.")
async def send_content(message, context: ContextTypes.DEFAULT_TYPE, param: str, user_id: int):
    decoded = base64.urlsafe_b64decode(param.encode()).decode()
    category, msg_ids_str = decoded.split(":")
    msg_ids = [int(mid) for mid in msg_ids_str.split(",")]
    target_chat = CATEGORY_CHANNELS.get(category)
    if not target_chat:
        await message.reply_text("دسته‌بندی پیدا نشد")
        return
    sent_messages = []
    for msg_id in msg_ids:
        sent = await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=target_chat,
            message_id=msg_id
        )
        sent_messages.append(sent.message_id)
    notice = None
    if get_setting('delete_after_2min'):
        notice = await message.reply_text("📌 این محتوا بعد از ۲ دقیقه حذف می‌شود.")
    if get_setting('delete_after_2min'):
        context.application.create_task(schedule_deletion(context, user_id, sent_messages + ([notice.message_id] if notice else [])))
    join_check_session.pop(user_id, None)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("دستور اشتباهی وارد کردید")
        return
    await show_admin_menu(update, context)
def register_user_handlers(app):
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(confirm_join_callback, pattern="^confirm_join$"))