import hmac, hashlib, base64
from config import ADMIN_HASH, CATEGORY_CHANNELS, BOT_TOKEN, BOT_ID, ADMIN_ID
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters

# -----------------------
# admin check
# -----------------------
def is_admin(user_id: int) -> bool:
     user_bytes = str(user_id).encode() 
     token_bytes = BOT_TOKEN.encode() 
     hashed = hmac.new(token_bytes, user_bytes, hashlib.sha256).hexdigest() 
     return hashed == ADMIN_HASH

# -----------------------
# session
# -----------------------
admin_session = {}

# -----------------------
# buttons
# -----------------------
def back_button():
    return [InlineKeyboardButton("🔙 برگشت به منو", callback_data="back")]

MAIN_MENU = [
    [InlineKeyboardButton("📤 آپلود آیتم", callback_data="upload")],
    [InlineKeyboardButton("🔗 ساخت لینک آیتم", callback_data="make_link")],
    [InlineKeyboardButton("❌ حذف آیتم", callback_data="delete")]
]

CATEGORY_MENU = [
    [InlineKeyboardButton("🎬 فیلم", callback_data="movie")],
    [InlineKeyboardButton("📺 سریال", callback_data="serie")],
    [InlineKeyboardButton("🧸 انیمیشن", callback_data="animation")],
    back_button()
]

YES_NO = [
    [InlineKeyboardButton("✅ بله", callback_data="yes")],
    [InlineKeyboardButton("❌ خیر", callback_data="no")],
    back_button()
]

# -----------------------
# show admin menu
# -----------------------
async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id):
        await update.message.reply_text("⛔️ دسترسی غیرمجاز")
        return
    
    await update.message.reply_text(
        "👋 سلام ادمین!\nیکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(MAIN_MENU)
    )

# -----------------------
# callback handler
# -----------------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    uid = user.id

    if not is_admin(uid):
        await query.edit_message_text("⛔️ دسترسی غیرمجاز")
        return

    session = admin_session.setdefault(uid, {
        "action": None,
        "category": None,
        "large": False,
        "remain": 0,
        "msg_ids": []
    })

    data = query.data

    if data == "back":
        session.clear()
        await query.edit_message_text(
            "👋 سلام ادمین!\nیکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(MAIN_MENU)
        )
        return

    if data in ("upload", "make_link", "delete"):
        session.update({
            "action": data,
            "category": None,
            "large": False,
            "remain": 0,
            "msg_ids": []
        })
        await query.edit_message_text(
            "دسته‌بندی رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(CATEGORY_MENU)
        )
        return

    if data in ("movie", "serie", "animation"):
        session["category"] = data
        if session["action"] == "upload":
            await query.edit_message_text(
                "آیا حجم بیشتر از ۲ گیگ است؟",
                reply_markup=InlineKeyboardMarkup(YES_NO)
            )
        else:
            await query.edit_message_text(
                "پیام‌ها رو مستقیماً از چنل این دسته‌بندی فوروارد کن:",
                reply_markup=InlineKeyboardMarkup([back_button()])
            )
        return

    if data in ("yes", "no") and session["action"] == "upload":
        session["large"] = data == "yes"
        if session["large"]:
            await query.edit_message_text(
                "تعداد فایل‌ها رو بفرست (عدد):",
                reply_markup=InlineKeyboardMarkup([back_button()])
            )
        else:
            await query.edit_message_text(
                "حالا فایل رو بفرست (فوروارد یا آپلود مستقیم)",
                reply_markup=InlineKeyboardMarkup([back_button()])
            )

# -----------------------
# message handler
# -----------------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not is_admin(user.id) or user.id not in admin_session:
        return

    session = admin_session[user.id]
    msg: Message = update.message
    action = session["action"]
    target_chat = CATEGORY_CHANNELS[session["category"]]

    # گرفتن تعداد فایل برای آپلود بزرگ
    if action == "upload" and session["large"] and session["remain"] == 0:
        if not msg.text or not msg.text.isdigit():
            await msg.reply_text("❌ عدد معتبر نیست")
            return
        session["remain"] = int(msg.text)
        await msg.reply_text(f"حالا {session['remain']} تا فایل رو یکی یکی بفرست")
        return

    sent_message = None

    # UPLOAD
    if action == "upload":
        sent_message = await context.bot.copy_message(
            chat_id=target_chat,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )

    # MAKE LINK / DELETE
    else:
        if not msg.forward_origin:
            await msg.reply_text("❌ برای این عملیات باید پیام فوروارد شده باشه")
            return

        if not hasattr(msg.forward_origin, 'chat') or msg.forward_origin.chat.id != target_chat:
            await msg.reply_text("❌ پیام باید مستقیماً از چنل این دسته‌بندی فوروارد شده باشه")
            return

        original_msg_id = msg.forward_origin.message_id
        session["msg_ids"].append(original_msg_id)

    if sent_message:
        session["msg_ids"].append(sent_message.message_id)

    if session.get("remain"):
        session["remain"] -= 1
        await msg.reply_text(f"✅ دریافت شد ({len(session['msg_ids'])} از {len(session['msg_ids']) + session['remain']})")

    # پایان عملیات
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

        admin_session.pop(user.id, None)

# -----------------------
# register handlers
# -----------------------
def register_admin_handlers(app):
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL, message_handler))