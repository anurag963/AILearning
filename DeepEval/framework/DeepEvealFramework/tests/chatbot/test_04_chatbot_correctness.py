"""04 - Correctness: does the reply match the reference answer?

The only test that uses `expected_output`. It runs on every golden, including
the out-of-scope ones, where the reference is a refusal, so it doubles as the
check that the bot declines what it cannot answer instead of guessing.
"""
import pytest
from deepeval import assert_test

from metrics_catalog import SPEC_CORRECTNESS

GOLDENS = SPEC_CORRECTNESS.cases()


@pytest.mark.chatbot
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.input[:45])
def test_chatbot_correctness(chatbot, judge, golden):
    reply = chatbot.chat(golden.input).reply
    tc = SPEC_CORRECTNESS.build_case(golden, reply)
    assert_test(tc, [SPEC_CORRECTNESS.build_metric(judge)])
