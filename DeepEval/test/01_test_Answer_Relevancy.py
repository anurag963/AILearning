
from deepeval.test_case import LLMTestCase
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric


# source .venv/bin/activate

#   deepeval set-local-model --model openai/gpt-oss-120b \
#       --base-url "https://api.groq.com/openai/v1" --format json --prompt-api-key
# export LOCAL_MODEL_API_KEY="YOUR_GROQ_API_KEY"


# deepeval test run 01_test_Answer_Relevancy.py   

# steps to run the test:
# run deepeval set-local-model --model openai/gpt-oss-120b --base-url "https://api.groq.com/openai/v1" --format json --prompt-api-key
# run export LOCAL_MODEL_API_KEY="YOUR_GROQ_API_KEY" 
# run deepeval test run 01_test_Answer_Relevancy.py 
# Here Groq works as a judge. we are not testing any llm here as input is not coming from any llm. we are testing the relevancy of the answer given by llm to the input question.


def test_HelloWorld():
    test= LLMTestCase(
        input = "What is 2 + 2?",
        actual_output = "4",
        expected_output = "4",
        context = ["Basic arithmetic peform and give result"]

    )

    metrics = [AnswerRelevancyMetric(threshold=0.9)]
    assert_test(test, metrics)


