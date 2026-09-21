"""Judge LLM for every metric: Groq's OpenAI-compatible endpoint via deepeval's LocalModel.

Built explicitly rather than relying on `deepeval set-local-model`, so the suite
runs from a clean checkout with only GROQ_API_KEY set.
"""
import os

from deepeval.models import LocalModel

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")


def build_judge() -> LocalModel:
    return LocalModel(
        model=JUDGE_MODEL,
        api_key=os.environ["GROQ_API_KEY"],
        base_url=GROQ_BASE_URL,
        temperature=0.0,  # a judge should be as repeatable as possible
    )
