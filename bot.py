import os
import logging
import asyncio
from quart import Quart, request, jsonify
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from motor.motor_asyncio import AsyncIOMotorClient

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Set your owner ID in env

if not BOT_TOKEN or not MONGO_URI or OWNER_ID == 0:
    raise Exception("BOT_TOKEN, MONGO_URI and OWNER_ID environment variables are required!")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Quart app initialization
app = Quart(__name__)

# MongoDB client will be initialized before serving
mongo_client = None
db = None
users_collection = None

# Telegram Bot and Application (will be initialized later)
bot = None
application = None

# Start command handler - user registration
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await users_collection.find_one({"user_id": user_id}) is None:
        await users_collection.insert_one({"user_id": user_id})
        logger.info(f"New user added: {user_id}")
    await update.message.reply_text("Welcome! You will receive broadcasts from this bot.")

# Broadcast command - only owner can use
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You are not authorized to send broadcasts.")
        return

    text = update.message.text.partition(' ')[2].strip()
    if not text:
        await update.message.reply_text(
            "Please provide a message to broadcast.\nUsage:\n/broadcast Your message here"
        )
        return

    users_cursor = users_collection.find({})
    count = 0

    async for user in users_cursor:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=text)
            count += 1
            await asyncio.sleep(0.05)  # avoid flooding Telegram API
        except Exception as e:
            logger.warning(f"Failed to send message to {user['user_id']}: {e}")

    await update.message.reply_text(f"Broadcast sent to {count} users.")

# Before serving, setup MongoDB and Telegram Application
@app.before_serving
async def startup():
    global mongo_client, db, users_collection, bot, application
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client.broadcast_db  # or any db name you want
    users_collection = db.users

    bot = Bot(token=BOT_TOKEN)
    application = ApplicationBuilder().bot(bot).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()  # Use polling or setup webhook below as needed

    logger.info("Bot and MongoDB connected, ready to serve!")

# Quart route for health check
@app.route("/")
async def index():
    return jsonify({"status": "Bot is running"})

# Webhook endpoint to receive Telegram updates
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    try:
        data = await request.get_json()
        update = Update.de_json(data, bot)
        await application.update_queue.put(update)  # Process update async
        return "OK"
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return "Error", 500

# Cleanup on shutdown
@app.before_serving
async def shutdown():
    if application:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
    if mongo_client:
        mongo_client.close()
    logger.info("Bot and MongoDB connections closed cleanly.")

# Run Quart app (only if running locally; on Render use .render.yaml startCommand)
if __name__ == "__main__":
    import hypercorn.asyncio
    import asyncio

    asyncio.run(hypercorn.asyncio.serve(app, hypercorn.Config()))
