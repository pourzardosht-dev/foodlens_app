from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import hash_token
from app.db.models import Base, ProfileToken
from app.db.session import get_db_session
from app.main import app
from app.settings import Settings, get_settings


def create_test_client() -> tuple[TestClient, sessionmaker[Session]]:
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
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        token_pepper="test-only-pepper"
    )
    return TestClient(app), session_factory


def test_anonymous_profile_token_lifecycle() -> None:
    client, session_factory = create_test_client()
    try:
        created = client.post(
            "/v1/profiles/anonymous",
            json={"timezone": "Asia/Tehran", "daily_calorie_target": 2100},
        )

        assert created.status_code == 201
        body = created.json()
        token = body["token"]
        assert len(token) >= 43
        assert body["timezone"] == "Asia/Tehran"
        assert body["daily_calorie_target"] == "2100"

        with session_factory() as session:
            stored_token = session.scalar(select(ProfileToken))
            assert stored_token is not None
            assert stored_token.token_hash == hash_token(token, "test-only-pepper")
            assert token.encode() != stored_token.token_hash

        headers = {"Authorization": f"Bearer {token}"}
        fetched = client.get("/v1/profile", headers=headers)
        assert fetched.status_code == 200
        assert "token" not in fetched.json()

        updated = client.patch(
            "/v1/profile",
            headers=headers,
            json={"timezone": "UTC", "locale": "en"},
        )
        assert updated.status_code == 200
        assert updated.json()["timezone"] == "UTC"

        exported = client.get("/v1/profile/export", headers=headers)
        assert exported.status_code == 200
        assert exported.json()["meals"] == []

        deleted = client.delete("/v1/profile", headers=headers)
        assert deleted.status_code == 204
        assert client.get("/v1/profile", headers=headers).status_code == 401
        assert client.get(
            "/v1/profile", headers={"Authorization": "Bearer invalid"}
        ).status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_anonymous_profile_rejects_invalid_timezone() -> None:
    client, _ = create_test_client()
    try:
        response = client.post(
            "/v1/profiles/anonymous", json={"timezone": "Not/A-Timezone"}
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()