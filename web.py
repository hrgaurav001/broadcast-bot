import os
import logging
from quart import Quart, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Quart app and Telegram bot application
app = Quart(__name__)
bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# MongoDB client and database placeholder
mongo_client = None
db = None

# Telegram command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! This is your bot running with Quart and MongoDB.")

application.add_handler(CommandHandler("start", start))

# Initialize before serving
@app.before_serving
async def before_serving():
    global mongo_client, db
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.get_default_database()
    logger.info("Connected to MongoDB")
    await bot.initialize()
    await application.initialize()
    await application.post_init()
    logger.info("Telegram bot initialized and ready")

# Basic route to test server
@app.route("/")
async def home():
    return "Bot is live and using Quart webhook."

# Webhook route to receive Telegram updates
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return "OK"
