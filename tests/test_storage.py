import pytest
import os
from tools.storage import init_db, save_application, get_all_applications, get_application, update_status


TEST_DB = "data/test_applications.db"


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
    """Use a separate test database and clean it up after each test."""
    monkeypatch.setattr("tools.storage.DB_PATH", TEST_DB)
    init_db()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def sample_package():
    return {
        "company_name": "Acme Corp",
        "role_title": "AI Engineer",
        "location": "Toronto, ON",
        "fit_score": 7,
        "status": "To Apply",
        "cover_letter": "Dear hiring manager...",
        "cv_notes": ["Move Zafin bullet up", "Add RAG to skills"],
        "company_brief": "Acme is a fast-growing AI startup.",
        "quality_flags": [],
        "red_flags": ["Aggressive timeline"],
        "required_skills": ["Python", "LLMs"],
        "raw_text": "Full job posting text here",
    }


def test_save_and_retrieve_application(sample_package):
    app_id = save_application(sample_package)
    assert isinstance(app_id, int)
    assert app_id > 0

    result = get_application(app_id)
    assert result is not None
    assert result["company"] == "Acme Corp"
    assert result["role"] == "AI Engineer"
    assert result["fit_score"] == 7
    assert isinstance(result["cv_notes"], list)
    assert "Move Zafin bullet up" in result["cv_notes"]


def test_get_all_applications_returns_list(sample_package):
    save_application(sample_package)
    save_application({**sample_package, "company_name": "Beta Inc"})

    results = get_all_applications()
    assert len(results) == 2
    assert results[0]["company"] == "Beta Inc"  # most recent first


def test_get_all_applications_empty():
    results = get_all_applications()
    assert results == []


def test_update_status(sample_package):
    app_id = save_application(sample_package)
    updated = update_status(app_id, "Applied")
    assert updated is True

    result = get_application(app_id)
    assert result["status"] == "Applied"


def test_update_status_nonexistent():
    updated = update_status(9999, "Applied")
    assert updated is False


def test_get_application_nonexistent():
    result = get_application(9999)
    assert result is None


def test_json_fields_deserialize_correctly(sample_package):
    app_id = save_application(sample_package)
    result = get_application(app_id)

    assert isinstance(result["cv_notes"], list)
    assert isinstance(result["quality_flags"], list)
    assert isinstance(result["red_flags"], list)
    assert isinstance(result["required_skills"], list)
    assert "Aggressive timeline" in result["red_flags"]

