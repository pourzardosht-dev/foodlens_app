import json
import logging
from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_db_session
from app.main import app
from app.settings import Settings, get_settings


client = TestClient(app)


def create_database_client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record) -> None:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.create_function(
            "char_length", 1, lambda value: len(value) if value is not None else None
        )

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session
            session.commit()

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        token_pepper="test-only-pepper"
    )
    return TestClient(app)


def test_request_id_and_route_metrics_do_not_include_resource_ids() -> None:
    request_id = "test-request-id"
    response = client.get(
        "/v1/foods/ghormeh-sabzi", headers={"X-Request-ID": request_id}
    )

    assert response.headers["x-request-id"] == request_id
    metrics = client.get("/metrics").text
    assert 'route="/v1/foods/{food_id}"' in metrics
    assert "ghormeh-sabzi" not in metrics


def test_export_audit_log_omits_profile_and_nutrition(caplog) -> None:
    database_client = create_database_client()
    profile = database_client.post(
        "/v1/profiles/anonymous", json={"timezone": "Asia/Tehran"}
    ).json()
    try:
        with caplog.at_level(logging.INFO, logger="foodlens"):
            response = database_client.get(
                "/v1/profile/export",
                headers={"Authorization": f"Bearer {profile['token']}"},
            )

        assert response.status_code == 200
        event = json.loads(caplog.records[-1].message)
        assert event["event"] == "profile_exported"
        assert set(event) == {"event", "request_id"}
    finally:
        app.dependency_overrides.clear()