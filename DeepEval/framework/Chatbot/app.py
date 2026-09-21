"""Local web UI for the support chatbot.

Run:  python app.py      then open http://127.0.0.1:8000
"""
import os
import sys
from collections import OrderedDict
from pathlib import Path

import uvicorn
from openai import OpenAIError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from chatbot import SupportChatbot

HERE = Path(__file__).parent
MAX_SESSIONS = 100  # oldest chats are dropped beyond this
MAX_MESSAGE_CHARS = 2000

try:
    template = SupportChatbot()  # fail fast if the API key or knowledge base is missing
except (RuntimeError, FileNotFoundError) as e:
    sys.exit(f"Error: {e}")

# One SupportChatbot (= one conversation history) per browser tab, keyed by session_id
sessions = OrderedDict()


def get_bot(session_id):
    # New chats build a fresh bot, so edits to detals.md are picked up without a restart.
    bot = sessions.pop(session_id, None) or SupportChatbot(
        client=template.client, model=template.model
    )
    sessions[session_id] = bot  # re-insert at the end = most recently used
    while len(sessions) > MAX_SESSIONS:
        sessions.popitem(last=False)
    return bot


def error(message, status):
    return JSONResponse({"error": message}, status_code=status)


async def read_json(request):
    """Return the JSON body as a dict, or None if the request isn't a valid JSON object."""
    # Requiring this header forces browsers to CORS-preflight cross-site requests (which
    # we don't allow), so other websites can't make your browser call this API.
    if not request.headers.get("content-type", "").startswith("application/json"):
        return None
    try:
        data = await request.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def valid_session_id(value):
    return isinstance(value, str) and 0 < len(value) <= 64


async def index(request):
    return FileResponse(HERE / "static" / "index.html")


async def chat(request):
    data = await read_json(request)
    if data is None or not valid_session_id(data.get("session_id")):
        return error("Invalid request.", 400)

    message = data.get("message")
    if not isinstance(message, str) or not message.strip():
        return error("Message is empty.", 400)
    if len(message) > MAX_MESSAGE_CHARS:
        return error(f"Message is too long (max {MAX_MESSAGE_CHARS} characters).", 400)

    bot = get_bot(data["session_id"])
    try:
        # bot.ask is a blocking network call, so keep it off the event loop
        reply = await run_in_threadpool(bot.ask, message.strip())
    except OpenAIError as e:
        return error(f"Could not reach the LLM: {e}", 502)
    return JSONResponse({"reply": reply})


async def reset(request):
    data = await read_json(request)
    if data is None or not valid_session_id(data.get("session_id")):
        return error("Invalid request.", 400)

    bot = sessions.get(data["session_id"])
    if bot:
        bot.reset()
    return JSONResponse({"ok": True})


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/chat", chat, methods=["POST"]),
        Route("/api/reset", reset, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Open http://127.0.0.1:{port}  (Ctrl+C to stop)")
    # 127.0.0.1 = this machine only; the chatbot isn't exposed to your network
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
