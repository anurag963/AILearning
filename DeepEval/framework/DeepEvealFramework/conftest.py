"""Shared fixtures. Sits at the framework root so pytest puts this folder on
sys.path, which is what lets tests import `metrics_catalog`, `dataset`, etc.
"""
import os

import pytest
from dotenv import load_dotenv

import reporting
from llm_provider.groq_judge import build_judge
from targets.chatbot_target import CHATBOT_DIR, ChatbotTarget

load_dotenv(CHATBOT_DIR / ".env")

# Wrap deepeval.assert_test now, before test modules import it.
reporting.install()


def pytest_configure(config):
    config.pluginmanager.register(reporting, "dashboard-reporting")


@pytest.fixture(scope="session")
def judge():
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")
    return build_judge()


@pytest.fixture
def chatbot():
    """A fresh bot per test, so one test's history never leaks into the next."""
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")
    return ChatbotTarget()
