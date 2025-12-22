import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_HASH = os.getenv("ADMIN_HASH")

CATEGORY_CHANNELS = {
    "movie": -1001234567890,   # ID چنل فیلم
    "series": -1009876543210,  # ID چنل سریال
    "anime": -1001122334455    # ID چنل انیمیشن
}

# مدت زمان حذف پیام
DELETE_DELAY = 120
