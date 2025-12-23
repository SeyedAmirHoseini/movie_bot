import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CATEGORY_CHANNELS, BOT_ID
from .utils import is_admin, back_button
from .menu import show_admin_menu
core_session = {}
CATEGORY_MENU = [
    [InlineKeyboardButton("🎬 فیلم", callback_data="core_movie")],
    [InlineKeyboardButton("📺 سریال", callback_data="core_serie")],
    [InlineKeyboardButton("🧸 انیمیشن", callback_data="core_animation")],
    back_button()
]
YES_NO = [
    [InlineKeyboardButton("✅ بله", callback_data="core_yes")],
    [InlineKeyboardButton("❌ خیر", callback_data="core_no")],
    back_button()
]
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if not is_admin(uid):
        await query.edit_message_text("⛔️ دسترسی غیرمجاز")
        return
    session = core_session.setdefault(uid, {
        "action": None, "category": None, "large": False, "remain": 0, "msg_ids": []
    })
    data = query.data
    if data == "back_to_main":
        core_session.pop(uid, None)
        await show_admin_menu(update, context)
        return
    # حذف پیشوند core_
    if data.startswith("core_"):
        data = data[5:]
    if data in ("upload", "make_link", "delete"):
        session.update({"action": data, "category": None, "large": False, "remain": 0, "msg_ids": []})
        await query.edit_message_text("دسته‌بندی رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(CATEGORY_MENU))
        return
    if data in ("movie", "serie", "animation"):
        session["category"] = data
        if session["action"] == "upload":
            await query.edit_message_text("آیا حجم بیشتر از ۲ گیگ است؟", reply_markup=InlineKeyboardMarkup(YES_NO))
        else:
            await query.edit_message_text("پیام‌ها رو مستقیماً از چنل این دسته‌بندی فوروارد کن:", reply_markup=InlineKeyboardMarkup([back_button()]))
        return
    if data in ("yes", "no") and session["action"] == "upload":
        session["large"] = data == "yes"
        if session["large"]:
            await query.edit_message_text("تعداد فایل‌ها رو بفرست (عدد):", reply_markup=InlineKeyboardMarkup([back_button()]))
        else:
            await query.edit_message_text("حالا فایل رو بفرست (فوروارد یا آپلود مستقیم)", reply_markup=InlineKeyboardMarkup([back_button()]))
        return
    return False # اگر هیچی نخورد، بره به بخش بعدی
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id) or user.id not in core_session:
        return False
    session = core_session[user.id]
    msg = update.message
    action = session["action"]
    target_chat = CATEGORY_CHANNELS.get(session["category"])
    if not target_chat:
        return False
    if action == "upload" and session["large"] and session["remain"] == 0:
        if not msg.text or not msg.text.isdigit():
            await msg.reply_text("❌ عدد معتبر نیست")
            return True
        session["remain"] = int(msg.text)
        await msg.reply_text(f"حالا {session['remain']} تا فایل رو یکی یکی بفرست")
        return True
    sent_message = None
    if action == "upload":
        sent_message = await context.bot.copy_message(
            chat_id=target_chat,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
    else:
        if not msg.forward_origin:
            await msg.reply_text("❌ برای این عملیات باید پیام فوروارد شده باشه")
            return True
        if not hasattr(msg.forward_origin, 'chat') or msg.forward_origin.chat.id != target_chat:
            await msg.reply_text("❌ پیام باید مستقیماً از چنل این دسته‌بندی فوروارد شده باشه")
            return True
        session["msg_ids"].append(msg.forward_origin.message_id)
    if sent_message:
        session["msg_ids"].append(sent_message.message_id)
    if session.get("remain"):
        session["remain"] -= 1
        await msg.reply_text(f"✅ دریافت شد ({len(session['msg_ids'])} از {len(session['msg_ids']) + session['remain']})")
    if session.get("remain", 0) == 0:
        payload = f"{session['category']}:" + ",".join(map(str, session["msg_ids"]))
        encoded = base64.urlsafe_b64encode(payload.encode()).decode()
        link = f"https://t.me/{BOT_ID}?start={encoded}"
        if action == "delete":
            deleted = 0
            for msg_id in session["msg_ids"]:
                try:
                    await context.bot.delete_message(target_chat, msg_id)
                    deleted += 1
                except:
                    pass
            await msg.reply_text(f"🗑 {deleted} آیتم حذف شد")
        else:
            await msg.reply_text(
                f"✅ انجام شد!\n\n"
                f"تعداد پارت: {len(session['msg_ids'])}\n"
                f"لینک دائمی:\n{link}"
            )
        core_session.pop(user.id, None)
    return True     