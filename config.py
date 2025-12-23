import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = "MoviesssBot_bot"
CATEGORY_CHANNELS = {
    "movie" : -1003656057056, # ID چنل فیلم
    "serie" : -1003489513570, # ID چنل سریال
    "animation": -1003544455672 # ID چنل انیمیشن
}
# مدت زمان حذف پیام
DELETE_DELAY = 120