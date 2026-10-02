import importlib.metadata
import sys

import httpx
import bs4
import pydantic
import openai
import dotenv
import pytest


def test_python_runtime_version():
    assert sys.version_info >= (3, 11)


def test_core_dependencies_import():
    assert httpx.__version__
    assert bs4.__version__
    assert pydantic.__version__
    assert openai.__version__
    assert hasattr(dotenv, "load_dotenv")
    assert importlib.metadata.version("python-dotenv") == "1.2.4"
    assert pytest.__version__
