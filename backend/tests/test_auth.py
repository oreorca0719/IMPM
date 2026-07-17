"""P1 검증 — 로그인 → 토큰 발급 → /auth/me."""
from app.core.security import hash_password
from app.models import User


async def _make_user(session, email="kbj@impm.team", pw="pw12345"):
    user = User(email=email, name="김범준", role="admin", password_hash=hash_password(pw))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_login_and_me(client, session):
    await _make_user(session, pw="secret-pw")

    # 로그인
    resp = await client.post(
        "/api/auth/login",
        json={"email": "kbj@impm.team", "password": "secret-pw"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "kbj@impm.team"
    token = data["access_token"]

    # /me
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["name"] == "김범준"


async def test_login_wrong_password(client, session):
    await _make_user(session, pw="right-pw")
    resp = await client.post(
        "/api/auth/login",
        json={"email": "kbj@impm.team", "password": "WRONG"},
    )
    assert resp.status_code == 401


async def test_me_requires_token(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401  # HTTPBearer: 인증 헤더 없음


async def test_users_list_requires_auth(client, session):
    user = await _make_user(session, pw="pw")
    # 무인증
    assert (await client.get("/api/users")).status_code == 401
    # 인증
    login = await client.post(
        "/api/auth/login", json={"email": user.email, "password": "pw"}
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
