import os
import logging
from quart import Quart, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load env vars
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Quart app and Telegram bot
app = Quart(__name__)
bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

initialized = False  # Initialization flag

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! This is your bot running with Quart and MongoDB.")

application.add_handler(CommandHandler("start", start))

# Init before webhook handling starts
@app.before_serving
async def before_serving():
    global initialized
    if not initialized:
        await bot.initialize()
        await application.initialize()
        initialized = True

@app.route("/")
async def home():
    return "Bot is live and using Quart webhook."

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return "OK"
