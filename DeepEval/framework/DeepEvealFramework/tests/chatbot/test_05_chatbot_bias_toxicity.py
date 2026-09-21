"""05 - Bias and toxicity: does the bot stay clean when baited?

Prompts invite stereotyping, insults, and mockery. Both metrics score 1.0 for a
clean reply, so the test passes at or above the threshold. Separate tests so a
report shows which of the two regressed.
"""
import pytest
from deepeval import assert_test

from metrics_catalog import SPEC_BIAS, SPEC_TOXICITY

PROMPTS = SPEC_BIAS.cases()


@pytest.mark.chatbot
@pytest.mark.safety
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("prompt", PROMPTS, ids=lambda p: p.input[:45])
def test_chatbot_bias(chatbot, judge, prompt):
    reply = chatbot.chat(prompt.input).reply
    tc = SPEC_BIAS.build_case(prompt, reply)
    assert_test(tc, [SPEC_BIAS.build_metric(judge)])


@pytest.mark.chatbot
@pytest.mark.safety
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("prompt", PROMPTS, ids=lambda p: p.input[:45])
def test_chatbot_toxicity(chatbot, judge, prompt):
    reply = chatbot.chat(prompt.input).reply
    tc = SPEC_TOXICITY.build_case(prompt, reply)
    assert_test(tc, [SPEC_TOXICITY.build_metric(judge)])
