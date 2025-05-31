from quart import Quart, render_template

app = Quart(__name__)

@app.route("/")
async def admin():
    return await render_template("admin.html")

if __name__ == "__main__":
    app.run()
