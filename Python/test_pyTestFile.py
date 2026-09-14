import pytest


@pytest.mark.smoke
def test_addition():
    print("Running test_addition")
    result = 2+3
    assert result == 5, f"Expected 5 but got {result}"


@pytest.mark.regression
def test_regreesion():
    print("Running test_aregreesion")
    result = 2+3
    assert result == 5, f"Expected 5 but got {result}"



