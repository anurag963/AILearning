
from deepeval.test_case import LLMTestCase
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from openai import OpenAI
import os
from dotenv import load_dotenv

#   deepeval set-local-model --model openai/gpt-oss-120b \
#       --base-url "https://api.groq.com/openai/v1" --format json --prompt-api-key

#   deepeval set-local-model --model qwen/qwen/qwen3.8-27b \
#       --base-url "https://api.groq.com/openai/v1" --format json --prompt-api-key

# steps to run the test:
# run deepeval set-local-model --model openai/gpt-oss-120b --base-url "https://api.groq.com/openai/v1" --format json --prompt-api-key
# run export LOCAL_MODEL_API_KEY="YOUR_GROQ_API_KEY" 
# run deepeval test run 01_test_Answer_Relevancy.py 
# Here Groq works as a judge. we are not testing any llm here as input is not coming from any llm. we are testing the relevancy of the answer given by llm to the input question.

load_dotenv()

GROQ_MODEL = "qwen/qwen3.8-27b"
JUDGE_MODEL = "openai/gpt-oss-120b"


groq = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

def llm_response(question):
    response = groq.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": question}],
    
            temperature=0.0,
        )
    return response.choices[0].message.content.strip()


question = "What is 2 + 2? Reply just a number without any explanation."


answer = llm_response(question)
print(f"Answer from Groq model: {answer}")
print(f"\n [Groq {GROQ_MODEL}] > Answer from Groq model: {answer!r}\n")


def test_test_with_Judge_qwen():
    test= LLMTestCase(
        input = question,
        actual_output = answer,
        expected_output = "4",
        context = ["Basic arithmetic fact: 2 + 2 equals 5."],

    )


    metrics = [
        AnswerRelevancyMetric(threshold=0.8, model=JUDGE_MODEL),
        HallucinationMetric(threshold=0.3, model=JUDGE_MODEL)
        ]
    
    assert_test(test, metrics)



