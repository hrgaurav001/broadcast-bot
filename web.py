import os
from quart import Quart, request, render_template
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI")

app = Quart(__name__)

# Initialize bot and application
bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Global flag to track initialization
initialized = False

# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! This is your bot running with Quart and MongoDB.")

application.add_handler(CommandHandler("start", start))

@app.before_serving
async def init_telegram():
    global initialized
    if not initialized:
        await application.initialize()
        initialized = True

@app.route("/")
async def admin():
    return await render_template("admin.html")

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = await request.get_json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return "OK"

if __name__ == "__main__":
    app.run()
