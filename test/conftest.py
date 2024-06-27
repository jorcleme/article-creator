"""module pytest"""
import pytest
from src.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """
    Returns the a test client that can be used to 
    call FastAPI endpoints in tests
    """
    return TestClient(app)
