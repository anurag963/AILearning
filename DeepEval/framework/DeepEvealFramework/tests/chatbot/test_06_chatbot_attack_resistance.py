"""06 - Attack resistance: does the bot hold its rules under adversarial input?

Runs every technique in dataset/attacks.py (direct injection, jailbreak,
obfuscation, exfiltration, social engineering, out-of-domain misuse). The test
id carries the technique, so a failure tells you WHICH defence is missing
rather than just that "safety" failed.
"""
import pytest
from deepeval import assert_test

from metrics_catalog import SPEC_ATTACK_RESISTANCE

ATTACKS = SPEC_ATTACK_RESISTANCE.cases()


@pytest.mark.chatbot
@pytest.mark.safety
@pytest.mark.slow
@pytest.mark.needs_chatbot
@pytest.mark.parametrize("attack", ATTACKS, ids=lambda a: f"{a.technique}-{a.input[:35]}")
def test_chatbot_attack_resistance(chatbot, judge, attack):
    reply = chatbot.chat(attack.input).reply
    tc = SPEC_ATTACK_RESISTANCE.build_case(attack, reply)
    assert_test(tc, [SPEC_ATTACK_RESISTANCE.build_metric(judge, attack)])
