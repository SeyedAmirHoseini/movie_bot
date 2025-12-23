from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.admin_helper import add_admin, remove_admin, get_admins, check_permission, generate_hash
from .utils import back_button
from .menu import show_admin_menu

admins_session = {}

ADMINS_MENU = [
    [InlineKeyboardButton("➕ اضافه کردن ادمین جدید", callback_data="add_admin")],
    [InlineKeyboardButton("➖ حذف ادمین", callback_data="show_delete_admins")],
    [InlineKeyboardButton("📄 نمایش لیست ادمین‌ها", callback_data="list_admins")],
    back_button()
]

PERMISSIONS_MENU = [
    [InlineKeyboardButton("🎥 مدیریت ویدیوها", callback_data="toggle_videos")],
    [InlineKeyboardButton("⚙️ دسترسی به تنظیمات", callback_data="toggle_settings")],
    [InlineKeyboardButton("👥 مدیریت ادمین‌ها", callback_data="toggle_admins")],
    [InlineKeyboardButton("✅ تأیید و اضافه کردن", callback_data="confirm_add_admin")],
    back_button()
]

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    # فقط برای عملیات داخل بخش ادمین‌ها چک می‌کنیم
    if data in ["admins_menu", "add_admin", "show_delete_admins", "list_admins",
                "toggle_videos", "toggle_settings", "toggle_admins", "confirm_add_admin"] \
       or data.startswith("delete_admin_"):
        if not check_permission(uid, 'manage_admins'):
            await query.edit_message_text("⛔️ دسترسی غیرمجاز به مدیریت ادمین‌ها")
            return True

    if data == "admins_menu":
        await query.edit_message_text("👥 مدیریت ادمین‌ها:", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
        return True

    if data == "back_to_main":
        admins_session.pop(uid, None)
        await show_admin_menu(update, context)
        return True

    if data == "add_admin":
        await query.edit_message_text(
            "➕ برای اضافه کردن ادمین جدید:\n\n"
            "از کاربر بخواه به ربات پیام بده و این دستور رو بزنه:\n\n"
            "<code>/myprofile</code>\n\n"
            "ربات آیدی عددی و اطلاعاتش رو نشون می‌ده.\n"
            "آیدی عددی رو کپی کن و اینجا بفرست.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([back_button()])
        )
        admins_session[uid] = {
            "action": "waiting_for_id",
            "permissions": {"videos": True, "settings": True, "admins": False}
        }
        return True

    if data.startswith("toggle_"):
        session = admins_session.get(uid, {})
        if session.get("action") != "set_permissions":
            return False
        perm = data[7:]
        if perm == "videos":
            session["permissions"]["videos"] = not session["permissions"]["videos"]
        elif perm == "settings":
            session["permissions"]["settings"] = not session["permissions"]["settings"]
        elif perm == "admins":
            session["permissions"]["admins"] = not session["permissions"]["admins"]

        menu = get_permissions_menu(session["permissions"])
        await query.edit_message_text("✅ دسترسی‌ها رو انتخاب کن:", reply_markup=InlineKeyboardMarkup(menu))
        return True

    if data == "confirm_add_admin":
        session = admins_session.get(uid, {})
        if session.get("action") != "set_permissions" or "new_uid" not in session:
            return False

        new_uid = session["new_uid"]
        perms = session["permissions"]
        hash_val = generate_hash(new_uid)
        add_admin(new_uid, hash_val, perms["videos"], perms["settings"], perms["admins"])

        await query.edit_message_text(f"✅ ادمین جدید با موفقیت اضافه شد!\n\nآیدی: <code>{new_uid}</code>", parse_mode="HTML")
        admins_session.pop(uid, None)
        await query.message.reply_text("👥 مدیریت ادمین‌ها:", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
        return True

    if data == "list_admins":
        admins = get_admins()
        if not admins:
            text = "هیچ ادمینی ثبت نشده."
        else:
            text = "📄 لیست ادمین‌ها:\n\n"
            for adm in admins:
                user_id, _, videos, settings, admins_perm = adm
                text += f"• ID: <code>{user_id}</code>\n"
                text += f"   ویدیوها: {'✅' if videos else '❌'} | تنظیمات: {'✅' if settings else '❌'} | ادمین‌ها: {'✅' if admins_perm else '❌'}\n\n"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
        return True

    if data == "show_delete_admins":
        admins = get_admins()
        if not admins:
            await query.edit_message_text("هیچ ادمینی برای حذف وجود ندارد.", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
            return True
        keyboard = []
        for adm in admins:
            user_id = adm[0]
            keyboard.append([InlineKeyboardButton(f"🗑 حذف {user_id}", callback_data=f"delete_admin_{user_id}")])
        keyboard.append(back_button())
        await query.edit_message_text("❌ روی ادمینی که قصد حذف دارید کلیک کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    if data.startswith("delete_admin_"):
        admin_id = int(data[len("delete_admin_"):])
        if admin_id == uid:
            await query.edit_message_text("❌ نمی‌تونی خودت رو حذف کنی!")
            return True
        remove_admin(admin_id)
        await query.edit_message_text(f"🗑 ادمین {admin_id} با موفقیت حذف شد!", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
        return True

    return False  # اگر هیچی نبود، بره به core یا settings


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    uid = user.id

    if not check_permission(uid, 'manage_admins'):
        return False

    session = admins_session.get(uid, {})
    if session.get("action") != "waiting_for_id":
        return False

    text = update.message.text.strip()

    if not text.isdigit():
        await update.message.reply_text("❌ لطفاً فقط آیدی عددی بفرست (مثل 123456789)")
        return True

    new_uid = int(text)

    if new_uid == uid:
        await update.message.reply_text("❌ نمی‌تونی خودت رو دوباره اضافه کنی!")
        return True

    session["new_uid"] = new_uid
    session["action"] = "set_permissions"

    menu = get_permissions_menu(session["permissions"])
    await update.message.reply_text(
        f"✅ کاربر با آیدی <code>{new_uid}</code> شناسایی شد!\n\nحالا دسترسی‌هاش رو انتخاب کن:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(menu)
    )
    return True


def get_permissions_menu(perms):
    return [
        [InlineKeyboardButton(f"🎥 مدیریت ویدیوها: {'✅' if perms['videos'] else '❌'}", callback_data="toggle_videos")],
        [InlineKeyboardButton(f"⚙️ دسترسی به تنظیمات: {'✅' if perms['settings'] else '❌'}", callback_data="toggle_settings")],
        [InlineKeyboardButton(f"👥 مدیریت ادمین‌ها: {'✅' if perms['admins'] else '❌'}", callback_data="toggle_admins")],
        [InlineKeyboardButton("✅ تأیید و اضافه کردن", callback_data="confirm_add_admin")],
        back_button()
    ]