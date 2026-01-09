import asyncio
from flask import Flask, request, jsonify, render_template
from pyrogram import Client
import os
import uuid
import threading

app = Flask(__name__)

clients = {}
loop = asyncio.new_event_loop()

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=start_loop, args=(loop,), daemon=True).start()

def run_async(coro):
    """Run a coroutine in the background event loop and wait for the result."""
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return future.result(timeout=60) 
    except Exception as e:
        raise e

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/send_code", methods=["POST"])
def send_code():
    data = request.json
    api_id = int(data.get("api_id"))
    api_hash = data.get("api_hash")
    phone = data.get("phone", "").replace(" ", "")

    session_id = str(uuid.uuid4())

    async def _logic():
        client = Client(
            f"session_{session_id}",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True
        )
        await client.connect()
        sent_code = await client.send_code(phone)
        clients[session_id] = client
        return {"phone_code_hash": sent_code.phone_code_hash, "session_id": session_id}

    try:
        result = run_async(_logic())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    session_id = data.get("session_id")
    bot_token = data.get("bot_token")
    phone = data.get("phone", "").replace(" ", "")
    phone_code = data.get("phone_code", "").replace(" ", "")
    phone_code_hash = data.get("phone_code_hash")

    if not session_id and not bot_token:
        return jsonify({"error": "Missing session_id or bot_token"}), 400

    async def _logic():
        if bot_token:
            api_id = int(data.get("api_id"))
            api_hash = data.get("api_hash")
            client = Client(
                f"session_bot_{uuid.uuid4()}",
                api_id=api_id,
                api_hash=api_hash,
                in_memory=True
            )
            await client.connect()
            try:
                await client.sign_in_bot(bot_token)
                session_string = await client.export_session_string()
                return {"session_string": session_string}
            finally:
                await client.disconnect()
        
        client = clients.get(session_id)
        if not client:
            raise Exception("Session not found or expired. Please try again.")

        try:
            if phone and phone_code and phone_code_hash:
                await client.sign_in(phone, phone_code_hash, phone_code)
            else:
                raise Exception("Missing login details")
            
            session_string = await client.export_session_string()
            return {"session_string": session_string}
        finally:
            await client.disconnect()
            if session_id in clients:
                del clients[session_id]

    try:
        result = run_async(_logic())
        return jsonify(result)
    except Exception as e:
        if session_id in clients:
            try:
                run_async(clients[session_id].disconnect())
            except:
                pass
            del clients[session_id]
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=8000)
