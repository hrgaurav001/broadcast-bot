import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
from bson.objectid import ObjectId

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
OWNER_ID = int(os.getenv("OWNER_ID"))

client = AsyncIOMotorClient(MONGO_URI)
db = client.broadcast_db
users_collection = db.users
scheduled_collection = db.scheduled

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await users_collection.find_one({"user_id": user_id}) is None:
        await users_collection.insert_one({"user_id": user_id})
    await update.message.reply_text("Welcome! You are now subscribed to broadcasts.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized to send broadcasts.")
        return
    text = update.message.text.partition(' ')[2]
    if not text:
        await update.message.reply_text("Usage: /broadcast Your message here")
        return
    users = users_collection.find({})
    count = 0
    async for user in users:
        try:
            await context.bot.send_message(user["user_id"], text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"Broadcast sent to {count} users.")

async def scheduled_job(application):
    while True:
        now = datetime.utcnow()
        messages = scheduled_collection.find({"send_time": {"$lte": now}, "sent": False})
        async for msg in messages:
            users = users_collection.find({})
            async for user in users:
                try:
                    await application.bot.send_message(user["user_id"], msg["text"])
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
            await scheduled_collection.update_one({"_id": ObjectId(msg["_id"])}, {"$set": {"sent": True}})
        await asyncio.sleep(60)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.job_queue.run_repeating(lambda _: asyncio.create_task(scheduled_job(app)), interval=60)
    app.run_polling()