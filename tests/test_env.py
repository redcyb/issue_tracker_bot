import os


def test_env():
    assert os.environ["ENV"] == "test"
