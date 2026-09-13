"""The token guards the door, and failures come back with the status that names them."""

from fastapi.testclient import TestClient

from elenchus_interp.server import create_app

TOKEN = "t" * 24


def _client(analyzer) -> TestClient:
    return TestClient(create_app(lambda: analyzer, TOKEN, model="tiny-qwen3", revision="test"))


def test_no_token_no_analysis(analyzer, captured):
    with _client(analyzer) as client:
        assert client.post("/analyse", json=captured).status_code == 401
        wrong = {"Authorization": "Bearer nope"}
        assert client.post("/analyse", json=captured, headers=wrong).status_code == 401


def test_with_the_token_a_reading_and_an_attribution_come_back(analyzer, captured):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    with _client(analyzer) as client:
        assert client.get("/health").json()["ready"] is True
        reading = client.post("/analyse", json=captured, headers=headers)
        attribution = client.post(
            "/attribute", json={**captured, "target_tool": "record_answer"}, headers=headers
        )
        # A valid body without the token, so it is the token that is refused and not the
        # body: FastAPI validates a body before the handler can look at the header.
        unsigned = client.post("/attribute", json={**captured, "target_tool": "record_answer"})
        assert unsigned.status_code == 401
    assert reading.status_code == 200 and reading.json()["pick"]
    assert attribution.status_code == 200
    assert attribution.json()["attribution"]["target"] == "record_answer"


def test_a_bad_request_is_a_422_that_says_why(analyzer, captured):
    with _client(analyzer) as client:
        response = client.post(
            "/attribute",
            json={**captured, "target_tool": "delete_everything"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
    assert response.status_code == 422
    assert "was not offered" in response.json()["detail"]
