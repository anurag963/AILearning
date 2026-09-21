"""Adapter that gives the support chatbot the `.chat(msg).reply` shape the tests use."""
import sys
from dataclasses import dataclass
from pathlib import Path

CHATBOT_DIR = Path(__file__).resolve().parents[2] / "Chatbot"
sys.path.insert(0, str(CHATBOT_DIR))

from chatbot import SupportChatbot  # noqa: E402  (Chatbot/chatbot.py)


@dataclass
class ChatResult:
    reply: str


class ChatbotTarget:
    def __init__(self):
        self._bot = SupportChatbot()

    def chat(self, message: str) -> ChatResult:
        return ChatResult(reply=self._bot.ask(message))

    def reset(self) -> None:
        self._bot.reset()
