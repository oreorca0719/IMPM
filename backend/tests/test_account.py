"""아이디(이메일)·비밀번호 변경 + 최초 변경 강제 플래그."""
from app.core.security import hash_password
from app.models import User


async def _mk(session, email="kbj@impm.team", pw="pw12345", must_change=True):
    u = User(
        email=email,
        name="김범준",
        role="admin",
        password_hash=hash_password(pw),
        must_change_password=must_change,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _token(client, email, pw):
    r = await client.post("/api/auth/login", json={"email": email, "password": pw})
    return r.json()["access_token"]


async def test_login_exposes_must_change_flag(client, session):
    await _mk(session, pw="seed-pw")
    r = await client.post(
        "/api/auth/login", json={"email": "kbj@impm.team", "password": "seed-pw"}
    )
    assert r.json()["user"]["must_change_password"] is True


async def test_change_password_clears_flag(client, session):
    await _mk(session, pw="seed-pw")
    tok = await _token(client, "kbj@impm.team", "seed-pw")
    h = {"Authorization": f"Bearer {tok}"}

    r = await client.post(
        "/api/auth/password",
        json={"current_password": "seed-pw", "new_password": "new-strong-pw"},
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["must_change_password"] is False

    # 새 비밀번호로 로그인되고, 옛 비밀번호는 실패
    assert (await client.post("/api/auth/login", json={"email": "kbj@impm.team", "password": "new-strong-pw"})).status_code == 200
    assert (await client.post("/api/auth/login", json={"email": "kbj@impm.team", "password": "seed-pw"})).status_code == 401


async def test_change_password_wrong_current(client, session):
    await _mk(session, pw="seed-pw")
    tok = await _token(client, "kbj@impm.team", "seed-pw")
    r = await client.post(
        "/api/auth/password",
        json={"current_password": "WRONG", "new_password": "new-strong-pw"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 400


async def test_change_email_and_login_with_it(client, session):
    await _mk(session, pw="seed-pw")
    tok = await _token(client, "kbj@impm.team", "seed-pw")
    r = await client.patch(
        "/api/auth/me",
        json={"email": "bumjun@impm.team", "name": "범준", "current_password": "seed-pw"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "bumjun@impm.team"
    assert r.json()["name"] == "범준"
    # 새 아이디로 로그인 가능
    assert (await client.post("/api/auth/login", json={"email": "bumjun@impm.team", "password": "seed-pw"})).status_code == 200


async def test_change_email_duplicate_conflict(client, session):
    await _mk(session, pw="seed-pw")
    await _mk(session, email="mjs@impm.team", pw="pw")
    tok = await _token(client, "kbj@impm.team", "seed-pw")
    r = await client.patch(
        "/api/auth/me",
        json={"email": "mjs@impm.team", "current_password": "seed-pw"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 409


async def test_act_as_accepts_user_id(client, session):
    """MCP 대행이 이메일 대신 사용자 ID 로도 동작(이메일 변경 대비)."""
    bot = User(email="bot@impm.team", name="claude-bot", role="bot",
               password_hash=hash_password("pw"), must_change_password=False)
    session.add(bot)
    target = await _mk(session, email="kbj@impm.team", pw="pw")
    await session.commit()
    tok = await _token(client, "bot@impm.team", "pw")
    r = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tok}", "X-Act-As": str(target.id)},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "kbj@impm.team"
