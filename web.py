import os
from quart import Quart, render_template, request, redirect, url_for
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.broadcast_db
scheduled_collection = db.scheduled

app = Quart(__name__)

@app.route("/admin", methods=["GET", "POST"])
async def admin():
    if request.method == "POST":
        form = await request.form
        text = form.get("text")
        send_time = form.get("send_time")
        send_dt = datetime.strptime(send_time, "%Y-%m-%dT%H:%M")
        await scheduled_collection.insert_one({"text": text, "send_time": send_dt, "sent": False})
        return redirect(url_for("admin"))
    return await render_template("admin.html")

@app.route("/")
async def home():
    return "Bot is live."

if __name__ == "__main__":
    app.run()