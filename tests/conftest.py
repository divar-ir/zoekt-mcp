import os
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def load_env():
    """Load .env file for integration tests."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)


@pytest.fixture
def mock_zoekt_response():
    """Mock response from Zoekt search API."""
    return {
        "result": {
            "FileMatches": [
                {
                    "FileName": "test.py",
                    "Repo": "github.com/test/repo",
                    "Matches": [
                        {
                            "LineNum": 10,
                            "Fragments": [
                                {"Pre": "def ", "Match": "hello", "Post": "():"}
                            ],
                            "URL": "https://github.com/test/repo/blob/main/test.py#L10"
                        }
                    ],
                }
            ]
        }
    }


@pytest.fixture
def mock_zoekt_file_content_response():
    """Mock response from Zoekt print API."""
    return '<pre class="inline-pre">def hello():\n    print("world")</pre>'


@pytest.fixture
def mock_search_params():
    """Mock search parameters."""
    return {"q": "test", "num": 10, "format": "json", "ctx": 5}
