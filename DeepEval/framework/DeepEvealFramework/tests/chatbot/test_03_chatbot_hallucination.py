"""03 - Hallucination: does the reply contradict the ground-truth context?

Faithfulness asks "is every claim supported?"; hallucination asks "is anything
contradicted?". A reply that adds an unsupported but harmless claim can fail
one and pass the other. It reads `context` (the truth), not `retrieval_context`.
Score is 1.0 when nothing is contradicted; the test passes at or above the threshold.
"""
import pytest
from deepeval import assert_test

from metrics_catalog import SPEC_HALLUCINATION

GOLDENS = SPEC_HALLUCINATION.cases()


@pytest.mark.chatbot
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.input[:45])
def test_chatbot_hallucination(chatbot, judge, golden):
    reply = chatbot.chat(golden.input).reply
    tc = SPEC_HALLUCINATION.build_case(golden, reply)
    assert_test(tc, [SPEC_HALLUCINATION.build_metric(judge)])
