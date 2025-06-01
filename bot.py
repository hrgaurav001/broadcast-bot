import os
import asyncio
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Bot is running.")

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
