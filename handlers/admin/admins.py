from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.admin_helper import (
    add_admin, remove_admin, get_admins, check_permission, generate_hash,
    get_admin_permissions, update_admin_permissions
)
from .utils import back_button
from .menu import show_admin_menu
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_HASH = os.getenv("ADMIN_HASH")

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
    [InlineKeyboardButton("✅ ذخیره تغییرات", callback_data="save_permissions")],
    back_button()
]

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    # چک دسترسی برای همه عملیات بخش ادمین‌ها
    if data.startswith(("admins_", "add_admin", "show_delete_admins", "list_admins", "edit_perm_", "toggle_", "save_permissions", "delete_admin_")):
        if not check_permission(uid, 'manage_admins'):
            await query.edit_message_text("⛔️ دسترسی غیرمجاز به مدیریت ادمین‌ها")
            return True

    if data == "admins_menu":
        # منوی اصلی با دکمه اضافی برای سوپر ادمین
        menu = ADMINS_MENU.copy()
        if generate_hash(uid) == ADMIN_HASH:
            menu.insert(-1, [InlineKeyboardButton("⚙️ تغییر سطح دسترسی", callback_data="edit_permissions_menu")])
        await query.edit_message_text("👥 مدیریت ادمین‌ها:", reply_markup=InlineKeyboardMarkup(menu))
        return True

    if data == "back_to_main":
        admins_session.pop(uid, None)
        await show_admin_menu(update, context)
        return True

    if data == "add_admin":
        await query.edit_message_text(
            "➕ برای اضافه کردن ادمین جدید:\n\n"
            "آیدی عددی کاربر رو بفرست (مثل 123456789)\n\n"
            "از /myprofile هم می‌تونی آیدی بگیری.",
            reply_markup=InlineKeyboardMarkup([back_button()])
        )
        admins_session[uid] = {
            "action": "waiting_for_id",
            "permissions": {"videos": True, "settings": True, "admins": False}
        }
        return True

    # منوی انتخاب ادمین برای ویرایش دسترسی
    if data == "edit_permissions_menu":
        admins = get_admins()
        keyboard = []
        for adm in admins:
            user_id, hashed, _, _, _ = adm
            if hashed != ADMIN_HASH:  # سوپر ادمین رو نشون نده
                keyboard.append([InlineKeyboardButton(f"✏️ ویرایش {user_id}", callback_data=f"edit_perm_{user_id}")])
        keyboard.append(back_button())
        if not keyboard[:-1]:
            await query.edit_message_text("هیچ ادمین معمولی برای ویرایش وجود ندارد.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("⚙️ انتخاب کنید کدام ادمین را ویرایش کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    # ویرایش دسترسی یک ادمین خاص
    if data.startswith("edit_perm_"):
        target_id = int(data[len("edit_perm_"):])
        perms = get_admin_permissions(target_id)
        admins_session[uid] = {
            "action": "editing_permissions",
            "target_id": target_id,
            "permissions": perms.copy()
        }
        menu = [
            [InlineKeyboardButton(f"🎥 مدیریت ویدیوها: {'✅' if perms['videos'] else '❌'}", callback_data="toggle_videos")],
            [InlineKeyboardButton(f"⚙️ دسترسی به تنظیمات: {'✅' if perms['settings'] else '❌'}", callback_data="toggle_settings")],
            [InlineKeyboardButton(f"👥 مدیریت ادمین‌ها: {'✅' if perms['admins'] else '❌'}", callback_data="toggle_admins")],
            [InlineKeyboardButton("✅ ذخیره تغییرات", callback_data="save_permissions")],
            back_button()
        ]
        await query.edit_message_text(f"✏️ ویرایش دسترسی‌های ادمین <code>{target_id}</code>:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(menu))
        return True

    if data.startswith("toggle_") and admins_session.get(uid, {}).get("action") == "editing_permissions":
        session = admins_session[uid]
        perm = data[7:]
        if perm == "videos":
            session["permissions"]["videos"] = not session["permissions"]["videos"]
        elif perm == "settings":
            session["permissions"]["settings"] = not session["permissions"]["settings"]
        elif perm == "admins":
            session["permissions"]["admins"] = not session["permissions"]["admins"]

        perms = session["permissions"]
        menu = [
            [InlineKeyboardButton(f"🎥 مدیریت ویدیوها: {'✅' if perms['videos'] else '❌'}", callback_data="toggle_videos")],
            [InlineKeyboardButton(f"⚙️ دسترسی به تنظیمات: {'✅' if perms['settings'] else '❌'}", callback_data="toggle_settings")],
            [InlineKeyboardButton(f"👥 مدیریت ادمین‌ها: {'✅' if perms['admins'] else '❌'}", callback_data="toggle_admins")],
            [InlineKeyboardButton("✅ ذخیره تغییرات", callback_data="save_permissions")],
            back_button()
        ]
        await query.edit_message_text(f"✏️ ویرایش دسترسی‌های ادمین <code>{session['target_id']}</code>:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(menu))
        return True

    if data == "save_permissions":
        session = admins_session.get(uid, {})
        if session.get("action") != "editing_permissions":
            return False
        target_id = session["target_id"]
        perms = session["permissions"]
        update_admin_permissions(target_id, perms["videos"], perms["settings"], perms["admins"])
        await query.edit_message_text(f"✅ دسترسی‌های ادمین <code>{target_id}</code> با موفقیت بروزرسانی شد!", parse_mode="HTML")
        admins_session.pop(uid, None)
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
        text = "📄 لیست ادمین‌ها:\n\n"
        for adm in admins:
            user_id, hashed, videos, settings, admins_perm = adm
            if hashed == ADMIN_HASH:
                text += f"👑 <b>سوپر ادمین</b>: <code>{user_id}</code>\n\n"
            else:
                v = '✅' if videos else '❌'
                s = '✅' if settings else '❌'
                a = '✅' if admins_perm else '❌'
                text += f"• آیدی: <code>{user_id}</code>\n"
                text += f"   ویدیوها: {v} | تنظیمات: {s} | ادمین‌ها: {a}\n\n"

        # دکمه اضافی فقط برای سوپر ادمین
        menu = [back_button()]
        if generate_hash(uid) == ADMIN_HASH:
            menu.insert(0, [InlineKeyboardButton("⚙️ تغییر سطح دسترسی", callback_data="edit_permissions_menu")])

        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(menu))
        return True

    if data == "show_delete_admins":
        admins = get_admins()
        keyboard = []
        for adm in admins:
            user_id, hashed, _, _, _ = adm
            if hashed != ADMIN_HASH:
                keyboard.append([InlineKeyboardButton(f"🗑 حذف {user_id}", callback_data=f"delete_admin_{user_id}")])
        keyboard.append(back_button())
        if len(keyboard) == 1:
            await query.edit_message_text("هیچ ادمینی برای حذف وجود ندارد.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("❌ روی ادمینی که قصد حذف دارید کلیک کنید:", reply_markup=InlineKeyboardMarkup(keyboard))
        return True

    if data.startswith("delete_admin_"):
        admin_id = int(data[len("delete_admin_"):])
        hashed = generate_hash(admin_id)
        if hashed == ADMIN_HASH:
            await query.edit_message_text("❌ سوپر ادمین حذف‌شدنی نیست!")
            return True
        if admin_id == uid:
            await query.edit_message_text("❌ نمی‌تونی خودت رو حذف کنی!")
            return True
        remove_admin(admin_id)
        await query.edit_message_text(f"🗑 ادمین {admin_id} با موفقیت حذف شد!", reply_markup=InlineKeyboardMarkup(ADMINS_MENU))
        return True

    return False


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