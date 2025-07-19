from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup
from datetime import datetime
from pytz import timezone
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# Bot Config (from you)
BOT_TOKEN = "8025384223:AAEjuUYE5Gk_p5pjkQb1qODbFu8jtj2oibI"
CHANNEL_ID = "@bot1_test_1234"
ADMIN_ID = 1878312179  # ← Replace if your own Telegram ID is different

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
pst = timezone('Asia/Karachi')

# Default placeholder
POSTS = ["❗️Please run /updatefromsheet first."] * 16

# Load Google credentials from credentials.txt
def load_credentials():
    with open("credentials.txt", "r") as f:
        creds_data = json.load(f)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    return ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)

# Fetch posts from Google Sheet
def fetch_posts_from_sheet():
    try:
        creds = load_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1TKhMUVzdGDb2yJ0RpXJWxoEKaQL9I_xEwgWQHRedfvU/edit").sheet1
        posts = sheet.col_values(1)
        cleaned = [p.strip() for p in posts if p.strip()]
        if len(cleaned) == 16:
            print("✅ Posts fetched successfully.")
            return cleaned
        else:
            print(f"⚠️ Found {len(cleaned)} posts (expected: 16).")
            return None
    except Exception as e:
        print(f"❌ Google Sheet Error: {e}")
        return None

# Empty keyboard
def get_post_keyboard():
    return InlineKeyboardMarkup()

# Auto-post hourly
async def send_hourly_post():
    post_count = 0
    while post_count < 16:
        try:
            current_hour = datetime.now(pst).hour
            if 6 <= current_hour <= 22:
                post_index = current_hour - 6
                if 0 <= post_index < len(POSTS):
                    await bot.send_message(CHANNEL_ID, POSTS[post_index], reply_markup=get_post_keyboard())
                    print(f"✅ Posted hour {current_hour} PST")
                    post_count += 1
            else:
                print(f"⏳ Not posting: {current_hour} PST")
        except Exception as e:
            print(f"❌ Post error: {e}")
        await asyncio.sleep(3600)

# Command handler
@dp.message_handler()
async def handle_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ You are not authorized.")
        return

    if message.text.startswith("/updatefromsheet"):
        new_posts = fetch_posts_from_sheet()
        if new_posts:
            global POSTS
            POSTS = new_posts
            await message.reply("✅ Posts updated from Google Sheet.")
        else:
            await message.reply("❌ Failed to load posts from sheet.")

    elif message.text.startswith("/post"):
        try:
            num = int(message.text.replace("/post", "").strip())
            if 1 <= num <= 16:
                await bot.send_message(CHANNEL_ID, POSTS[num - 1], reply_markup=get_post_keyboard())
                await message.reply(f"✅ Post {num} sent.")
            else:
                await message.reply("⚠️ Use /post 1 to 16 only.")
        except:
            await message.reply("⚠️ Invalid /post command.")

    elif message.text.startswith("/testpost"):
        await bot.send_message(CHANNEL_ID, "🧪 Test Post\n\nThis is a test.")
        await message.reply("✅ Test post sent.")

    else:
        await message.reply("🤖 Commands:\n/updatefromsheet\n/post 1-16\n/testpost")

# Main bot loop
async def main():
    await asyncio.gather(
        dp.start_polling(),
        send_hourly_post()
    )

if __name__ == "__main__":
    asyncio.run(main())
