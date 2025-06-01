import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = AsyncIOMotorClient(MONGO_URI)
db = client.broadcast_db
users_collection = db.users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await users_collection.find_one({"user_id": user_id}) is None:
        await users_collection.insert_one({"user_id": user_id})
    await update.message.reply_text("Welcome! You will receive broadcasts from this bot.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only bot owner can broadcast - owner ID set via env
    OWNER_ID = int(os.getenv("OWNER_ID"))
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to send broadcasts.")
        return
    text = update.message.text.partition(' ')[2]
    if not text:
        await update.message.reply_text("Please provide a message to broadcast. Usage:\n/broadcast Your message here")
        return
    users = users_collection.find({})
    count = 0
    async for user in users:
        try:
            await context.bot.send_message(user["user_id"], text)
            count += 1
            await asyncio.sleep(0.05)  # avoid flooding
        except Exception:
            pass
    await update.message.reply_text(f"Broadcast sent to {count} users.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.run_polling()