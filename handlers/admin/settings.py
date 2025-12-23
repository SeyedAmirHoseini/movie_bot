from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.db import (
    get_setting, set_setting,
    add_required_channel, remove_required_channel, get_required_channels
)
from .utils import is_admin, back_button
from .menu import show_admin_menu
settings_session = {}
def get_settings_menu():
    delete_status = "✅ فعال" if get_setting('delete_after_2min') else "❌ غیرفعال"
    join_status = "✅ فعال" if get_setting('require_join') else "❌ غیرفعال"
    count = len(get_required_channels())
    return [
        [InlineKeyboardButton(f"🗑 حذف خودکار پیام بعد ۲ دقیقه: {delete_status}", callback_data="toggle_delete")],
        [InlineKeyboardButton(f"🔐 عضویت اجباری در چنل‌ها: {join_status}", callback_data="toggle_join")],
        [InlineKeyboardButton(f"📋 مدیریت چنل‌های اجباری ({count})", callback_data="manage_channels")],
        back_button()
    ]
def get_channels_menu():
    return [
        [InlineKeyboardButton("➕ اضافه کردن چنل جدید", callback_data="add_channel")],
        [InlineKeyboardButton("➖ حذف چنل موجود", callback_data="show_delete_channels")],
        [InlineKeyboardButton("📄 نمایش لیست چنل‌ها", callback_data="list_channels")],
        back_button()
    ]
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if not is_admin(uid):
        return False
    data = query.data
    if data == "back_to_main":
        await show_admin_menu(update, context)
        return True
    if data == "settings_menu":
        await query.edit_message_text("⚙️ تنظیمات ربات:", reply_markup=InlineKeyboardMarkup(get_settings_menu()))
        return True
    if data == "toggle_delete":
        set_setting('delete_after_2min', not get_setting('delete_after_2min'))
        await query.edit_message_text("✅ تنظیم بروز شد!", reply_markup=InlineKeyboardMarkup(get_settings_menu()))
        return True
    if data == "toggle_join":
        set_setting('require_join', not get_setting('require_join'))
        await query.edit_message_text("✅ تنظیم بروز شد!", reply_markup=InlineKeyboardMarkup(get_settings_menu()))
        return True
    if data == "manage_channels":
        await query.edit_message_text("📋 مدیریت چنل‌های اجباری:", reply_markup=InlineKeyboardMarkup(get_channels_menu()))
        return True
    # اضافه کردن چنل (با متن)
    if data == "add_channel":
        context = (
            """
➕ لطفاً آیدی یا @username چنل رو بفرست (مثل @mychannel یا -1001234567890):
مهم: به یاد داشته باشید که ربات شما باید در چنل های عضویت اجباری ادمین باشند تا بتوانند عضویت را چک کنند پس اول ربات را ادمین کنید سپس در این بخش اضافه کنید.
            """
        )
        await query.edit_message_text(
            context,
            reply_markup=InlineKeyboardMarkup([back_button()])
        )
        settings_session[uid] = {"action": "add_channel"}
        return True
    # نمایش لیست ساده (فقط متن)
    if data == "list_channels":
        channels = get_required_channels()
        text = "📄 لیست چنل‌های اجباری:\n\n" + ("\n".join(channels) if channels else "هیچ چنلی ثبت نشده.")
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(get_channels_menu()))
        return True
    # نمایش منوی حذف با دکمه‌های چنل
    if data == "show_delete_channels":
        channels = get_required_channels()
        if not channels:
            await query.edit_message_text("هیچ چنلی برای حذف وجود ندارد.", reply_markup=InlineKeyboardMarkup(get_channels_menu()))
            return True
        keyboard = []
        for ch_id in channels:
            keyboard.append([InlineKeyboardButton(f"🗑 حذف {ch_id}", callback_data=f"delete_channel_{ch_id}")])
        keyboard.append(back_button())
        await query.edit_message_text(
            "❌ روی چنلی که قصد حذف دارید کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return True
    # حذف چنل با کلیک
    if data.startswith("delete_channel_"):
        channel_id = data[len("delete_channel_"):]
        remove_required_channel(channel_id)
        await query.edit_message_text(
            f"🗑 چنل {channel_id} با موفقیت حذف شد!",
            reply_markup=InlineKeyboardMarkup(get_channels_menu())
        )
        return True
    return False
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if not user or not is_admin(user.id):
        return False
    uid = user.id
    if uid not in settings_session or settings_session[uid].get("action") != "add_channel":
        return False
    channel_id = update.message.text.strip()
    add_required_channel(channel_id)
    await update.message.reply_text(f"✅ چنل {channel_id} با موفقیت اضافه شد!")
    del settings_session[uid]
    await update.message.reply_text("⚙️ تنظیمات ربات:", reply_markup=InlineKeyboardMarkup(get_settings_menu()))
    return True