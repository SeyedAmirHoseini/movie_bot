from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.admin_helper import check_permission
from .utils import back_button

# منوی اصلی ادمین (بر اساس دسترسی فیلتر می‌شه)
MAIN_MENU = [
    [InlineKeyboardButton("🎥 ویدیوها", callback_data="videos_menu")],
    [InlineKeyboardButton("👥 ادمین‌ها", callback_data="admins_menu")],
    [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu")],
]

# زیرمنوی ویدیوها - اینجا تعریف شده تا همه جا قابل دسترسی باشه
VIDEOS_SUBMENU = [
    [InlineKeyboardButton("📤 آپلود آیتم", callback_data="core_upload")],
    [InlineKeyboardButton("🔗 ساخت لینک آیتم", callback_data="core_make_link")],
    [InlineKeyboardButton("❌ حذف آیتم", callback_data="core_delete")],
    back_button()
]

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    # چک کردن اینکه کاربر حداقل یک دسترسی داشته باشه
    if not check_permission(uid, 'any'):
        text = "⛔️ دسترسی غیرمجاز"
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(text)
        return

    # ساخت منوی پویا بر اساس دسترسی‌های کاربر
    menu_buttons = []
    if check_permission(uid, 'manage_videos'):
        menu_buttons.append([InlineKeyboardButton("🎥 ویدیوها", callback_data="videos_menu")])
    if check_permission(uid, 'manage_admins'):
        menu_buttons.append([InlineKeyboardButton("👥 ادمین‌ها", callback_data="admins_menu")])
    if check_permission(uid, 'access_settings'):
        menu_buttons.append([InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings_menu")])

    if not menu_buttons:
        text = "⚠️ شما هیچ دسترسی‌ای ندارید!"
    else:
        text = "👋 سلام ادمین!\nیکی از گزینه‌ها رو انتخاب کن:"

    markup = InlineKeyboardMarkup(menu_buttons)

    if update.message:
        await update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)