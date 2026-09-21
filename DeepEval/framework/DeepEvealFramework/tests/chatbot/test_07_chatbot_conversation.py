"""07 - Multi-turn: does the bot remember what the user already told it?

Single-turn tests cannot see a bot that answers every message correctly but
forgets a fact from two turns ago. Each golden replays a scripted conversation
through one bot instance (so history accumulates) and scores the transcript.
"""
import pytest
from deepeval import assert_test

from metrics_catalog import SPEC_FACT_HONOURED, SPEC_KNOWLEDGE_RETENTION

GOLDENS = SPEC_KNOWLEDGE_RETENTION.cases()


def _replay(chatbot, golden):
    return [chatbot.chat(msg).reply for msg in golden.user_turns]


@pytest.mark.chatbot
@pytest.mark.conversation
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.name)
def test_chatbot_knowledge_retention(chatbot, judge, golden):
    tc = SPEC_KNOWLEDGE_RETENTION.build_case(golden, _replay(chatbot, golden))
    assert_test(tc, [SPEC_KNOWLEDGE_RETENTION.build_metric(judge)])


@pytest.mark.chatbot
@pytest.mark.conversation
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.name)
def test_chatbot_fact_honoured(chatbot, judge, golden):
    tc = SPEC_FACT_HONOURED.build_case(golden, _replay(chatbot, golden))
    assert_test(tc, [SPEC_FACT_HONOURED.build_metric(judge, golden)])
