import os
from quart import Quart, request, render_template
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Quart(__name__)

bot = Bot(token=BOT_TOKEN)
application = ApplicationBuilder().token(BOT_TOKEN).build()

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
