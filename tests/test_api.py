import pytest
from fastapi.testclient import TestClient

from app.db.repository_factory import repository
from app.main import app


@pytest.fixture(autouse=True)
def reset_repository():
    repository.jobs.clear()
    repository.topics.clear()
    repository.trends.clear()
    repository.scores.clear()
    repository.links.clear()
    repository.settings.clear()
    yield


def test_health_check():
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_settings_round_trip():
    client = TestClient(app)
    payload = {
        "user_id": "personal-user",
        "enabled_topics": ["AI"],
        "custom_topics": ["스타트업"],
        "period": "7d",
        "result_limit": 10,
        "enabled_sources": ["rss", "official_blog", "news"],
    }

    update_response = client.put("/api/settings", json=payload)
    read_response = client.get("/api/settings?user_id=personal-user")

    assert update_response.status_code == 200
    assert read_response.status_code == 200
    assert read_response.json() == payload


def test_trend_analysis_flow():
    client = TestClient(app)

    analyze_response = client.post(
        "/api/trends/analyze",
        json={
            "user_id": "personal-user",
            "topics": ["AI", "기술", "개발도구"],
            "period": "24h",
            "result_limit": 3,
            "sources": ["rss", "official_blog", "news"],
        },
    )
    job_id = analyze_response.json()["job_id"]
    status_response = client.get(f"/api/trends/jobs/{job_id}")
    result_response = client.get(f"/api/trends/jobs/{job_id}/result")
    result = result_response.json()
    trend_id = result["topics"][0]["trends"][0]["trend_id"]
    detail_response = client.get(f"/api/trends/{trend_id}")
    latest_response = client.get("/api/trends/latest?user_id=personal-user")

    assert analyze_response.status_code == 201
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["progress"] == 100
    assert result_response.status_code == 200
    assert [len(topic["trends"]) for topic in result["topics"]] == [3, 3, 3]
    assert detail_response.status_code == 200
    assert len(detail_response.json()["links"]) >= 3
    assert latest_response.status_code == 200


def test_unknown_source_is_recorded_without_failing_job():
    client = TestClient(app)

    analyze_response = client.post(
        "/api/trends/analyze",
        json={
            "user_id": "personal-user",
            "topics": ["AI"],
            "period": "24h",
            "result_limit": 2,
            "sources": ["rss", "unknown"],
        },
    )
    job_id = analyze_response.json()["job_id"]
    status_response = client.get(f"/api/trends/jobs/{job_id}")
    result_response = client.get(f"/api/trends/jobs/{job_id}/result")

    assert status_response.json()["status"] == "completed"
    assert result_response.status_code == 200
    assert len(result_response.json()["topics"][0]["trends"]) == 2
