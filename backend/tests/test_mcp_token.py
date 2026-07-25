"""개인 MCP 토큰 — 본인 조회/재발급, 봇 전용 해석."""
from app.core.security import hash_password
from app.models import User


async def _mk(session, email, role="member", pw="pw12345"):
    u = User(
        email=email, name=email.split("@")[0], role=role,
        password_hash=hash_password(pw), must_change_password=False,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _h(client, email, pw="pw12345"):
    r = await client.post("/api/auth/login", json={"email": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_get_own_token_is_stable(client, session):
    await _mk(session, "kbj@impm.team")
    h = await _h(client, "kbj@impm.team")

    r1 = await client.get("/api/auth/mcp-token", headers=h)
    assert r1.status_code == 200
    t1 = r1.json()["token"]
    assert len(t1) >= 32
    assert "claude mcp add" in r1.json()["connect_command"]
    assert t1 in r1.json()["connect_command"]
    # 채팅 앱용 URL 은 /mcp/<token> 형태로 토큰을 포함
    assert r1.json()["chat_url"].endswith("/" + t1)

    # 다시 호출해도 같은 토큰
    r2 = await client.get("/api/auth/mcp-token", headers=h)
    assert r2.json()["token"] == t1


async def test_rotate_invalidates_old(client, session):
    await _mk(session, "kbj@impm.team")
    h = await _h(client, "kbj@impm.team")
    old = (await client.get("/api/auth/mcp-token", headers=h)).json()["token"]

    new = (await client.post("/api/auth/mcp-token/rotate", headers=h)).json()["token"]
    assert new != old
    assert (await client.get("/api/auth/mcp-token", headers=h)).json()["token"] == new


async def test_users_get_different_tokens(client, session):
    await _mk(session, "kbj@impm.team")
    await _mk(session, "mjs@impm.team")
    t1 = (await client.get("/api/auth/mcp-token", headers=await _h(client, "kbj@impm.team"))).json()["token"]
    t2 = (await client.get("/api/auth/mcp-token", headers=await _h(client, "mjs@impm.team"))).json()["token"]
    assert t1 != t2


async def test_resolve_bot_only(client, session):
    await _mk(session, "bot@impm.team", role="bot")
    kbj = await _mk(session, "kbj@impm.team")
    token = (await client.get("/api/auth/mcp-token", headers=await _h(client, "kbj@impm.team"))).json()["token"]

    # 봇: 해석 성공
    bot_h = await _h(client, "bot@impm.team")
    r = await client.post("/api/auth/mcp-resolve", json={"token": token}, headers=bot_h)
    assert r.status_code == 200
    assert r.json()["id"] == kbj.id
    assert r.json()["email"] == "kbj@impm.team"

    # 일반 사용자: 403
    r2 = await client.post(
        "/api/auth/mcp-resolve", json={"token": token},
        headers=await _h(client, "kbj@impm.team"),
    )
    assert r2.status_code == 403

    # 없는 토큰: 404
    r3 = await client.post("/api/auth/mcp-resolve", json={"token": "nope"}, headers=bot_h)
    assert r3.status_code == 404
