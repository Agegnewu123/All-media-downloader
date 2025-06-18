import telebot
from telebot import types
import requests
import json
import os
from datetime import datetime, timedelta

# === CONFIGURATION ===
TOKEN = "8176357537:AAEysle8l3DbCzWHXJa2MCsAr0SVO0kirZE"
CHANNEL_USERNAME = "@Elabcode"        # Required channel to join
FORWARD_CHANNEL = "@ElabMedias"       # Where downloaded videos are forwarded
ADMIN_ID = 7418084318                 # Admin user ID

bot = telebot.TeleBot(TOKEN)

DB_FILE = "data.json"

# Create DB file if it does not exist
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": {}, "downloads": []}, f)

# Load data from JSON
def load_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)

# Save data to JSON
def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Check if user is premium and premium period not expired
def is_premium(user_id):
    data = load_data()
    user = data["users"].get(str(user_id), {})
    if "premium" in user:
        premium_until = datetime.fromisoformat(user["premium"])
        return datetime.now() < premium_until
    return False

# Log a download for the user
def add_download(user_id):
    data = load_data()
    data["downloads"].append({
        "user_id": str(user_id),
        "time": str(datetime.now())
    })
    save_data(data)

# Check if user can download (limits for non-premium users)
def can_download(user_id):
    if is_premium(user_id):
        return True
    now = datetime.now()
    data = load_data()
    today_downloads = [d for d in data["downloads"] if d["user_id"] == str(user_id) and datetime.fromisoformat(d["time"]).date() == now.date()]
    last_hour_downloads = [d for d in today_downloads if datetime.fromisoformat(d["time"]) > now - timedelta(hours=1)]
    return len(today_downloads) < 3 and len(last_hour_downloads) < 1

# Check if user joined the required channel
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# === Handlers ===

@bot.message_handler(commands=["start"])
def start(msg):
    user_id = str(msg.from_user.id)
    data = load_data()
    if user_id not in data["users"]:
        data["users"][user_id] = {"joined": str(datetime.now())}
        save_data(data)
    
    if not check_subscription(msg.from_user.id):
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("✅ Join @Elabcode", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(msg.chat.id, "🔒 Please join @Elabcode to use this bot.", reply_markup=btn)
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📥 Download Video", "💎 Premium")
    kb.add("💰 Donate", "📞 Contact Admin")
    bot.send_message(msg.chat.id, "👋 Welcome! Send a social media link to download.", reply_markup=kb)

@bot.message_handler(commands=["grant"])
def grant_premium(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, uid, months = msg.text.split()
        data = load_data()
        until = datetime.now() + timedelta(days=int(months)*30)
        if uid not in data["users"]:
            data["users"][uid] = {}
        data["users"][uid]["premium"] = until.isoformat()
        save_data(data)
        bot.send_message(int(uid), f"💎 You are now premium until {until.date()}!")
        bot.send_message(msg.chat.id, "✅ Granted premium successfully.")
    except Exception:
        bot.send_message(msg.chat.id, "❌ Usage: /grant user_id months")

@bot.message_handler(func=lambda m: m.text == "💰 Donate")
def donate(m):
    bot.send_message(m.chat.id, "💎 Donate via TON to: UQC3iPLHG6BkQg5Cxi9psMjkv8uK_2dDtiE9qDJyPUpnDO8N\n⭐ Or send to @Agegnewu0102 with message 'Donation'")

@bot.message_handler(func=lambda m: m.text == "📞 Contact Admin")
def contact_admin(m):
    bot.send_message(m.chat.id, "📞 Contact: @Agegnewu0102")

@bot.message_handler(func=lambda m: m.text == "💎 Premium")
def premium_info(m):
    text = (
        "💎 Premium Benefits:\n"
        "- Unlimited downloads\n"
        "- Access to Facebook, X, Threads, Pinterest, and more.\n\n"
        "🌍 Price: 25 Birr/month (Ethiopia) or $0.5/50⭐ other countries.\n"
        "📞 Contact admin to activate: @Agegnewu0102"
    )
    bot.send_message(m.chat.id, text)

@bot.message_handler(func=lambda m: True)
def download_handler(m):
    user_id = m.from_user.id
    url = m.text.strip()

    if not check_subscription(user_id):
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton("✅ Join @Elabcode", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(m.chat.id, "🔒 Please join @Elabcode to use this bot.", reply_markup=btn)
        return

    if not can_download(user_id):
        bot.send_message(m.chat.id, "🚫 Daily/hourly limit reached. Upgrade to premium for unlimited downloads.")
        return

    bot.send_message(m.chat.id, "⏳ Downloading...")

    # TikTok not supported here
    if "tiktok.com" in url:
        bot.send_message(m.chat.id, "✅ TikTok detected. Please use the dedicated TikTok downloader bot.")
        return

    # YouTube download info
    elif "youtube.com" in url or "youtu.be" in url:
        video_id = None
        if "youtube.com" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        elif "youtu.be" in url:
            video_id = url.split("/")[-1]
        download_link = f"https://api.vevioz.com/api/button/mp3/{video_id}"
        bot.send_message(m.chat.id, f"🎥 YouTube download link:\n{download_link}")

    # Instagram message placeholder (premium only)
    elif "instagram.com" in url:
        if not is_premium(user_id):
            bot.send_message(m.chat.id, "❌ Instagram downloads are for premium users only.")
            return
        # Placeholder for Instagram download logic here
        bot.send_message(m.chat.id, f"✅ Instagram premium download started for: {url}")

    # Other social media - premium only
    else:
        if not is_premium(user_id):
            bot.send_message(m.chat.id, "❌ Downloads from this platform are for premium users only.")
            return
        # Placeholder for other platforms download logic
        bot.send_message(m.chat.id, f"✅ Premium download started for: {url}")

    add_download(user_id)

    # Forward message to channel
    forward_text = f"📤 User @{m.from_user.username or user_id} downloaded:\n{url}"
    bot.send_message(FORWARD_CHANNEL, forward_text)

# Run bot
bot.infinity_polling()
