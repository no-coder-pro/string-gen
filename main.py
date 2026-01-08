import asyncio
from flask import Flask, request, jsonify, render_template
from pyrogram import Client
import os

app = Flask(__name__)

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/send_code", methods=["POST"])
def send_code():
    data = request.json
    api_id = int(data.get("api_id"))
    api_hash = data.get("api_hash")
    phone = data.get("phone")

    async def _logic():
        client = Client(
            "session_gen",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True
        )
        await client.connect()
        sent_code = await client.send_code(phone)
        await client.disconnect()
        return {"phone_code_hash": sent_code.phone_code_hash}

    try:
        result = run_async(_logic())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    api_id = int(data.get("api_id"))
    api_hash = data.get("api_hash")
    bot_token = data.get("bot_token")
    phone = data.get("phone")
    phone_code = data.get("phone_code")
    phone_code_hash = data.get("phone_code_hash")

    async def _logic():
        client = Client(
            "session_gen",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True
        )
        await client.connect()
        if bot_token:
            await client.sign_in_bot(bot_token)
        elif phone and phone_code and phone_code_hash:
            await client.sign_in(phone, phone_code_hash, phone_code)
        else:
            raise Exception("Missing login details")
        
        session_string = await client.export_session_string()
        await client.disconnect()
        return {"session_string": session_string}

    try:
        result = run_async(_logic())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=8000)
