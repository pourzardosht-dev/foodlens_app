from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.rate_limit import FixedWindowRateLimiter


def test_rate_limiter_isolated_by_real_client_ip() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window_seconds=60)
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(limiter)])
    def limited() -> dict[str, str]:
        return {"status": "ok"}

    client = TestClient(app)
    first_headers = {"X-Real-IP": "192.0.2.1"}
    second_headers = {"X-Real-IP": "192.0.2.2"}

    assert client.get("/limited", headers=first_headers).status_code == 200
    assert client.get("/limited", headers=first_headers).status_code == 200
    limited_response = client.get("/limited", headers=first_headers)
    assert limited_response.status_code == 429
    assert int(limited_response.headers["retry-after"]) >= 1
    assert client.get("/limited", headers=second_headers).status_code == 200