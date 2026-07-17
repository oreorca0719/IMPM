"""봇 대행(impersonation) — X-Act-As 로 팀원별 귀속. 봇만 허용."""
from app.core.security import hash_password
from app.models import User


async def _mk(session, email, role="member"):
    u = User(email=email, name=email.split("@")[0], role=role, password_hash=hash_password("pw"))
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _token(client, email):
    r = await client.post("/api/auth/login", json={"email": email, "password": "pw"})
    return r.json()["access_token"]


async def test_bot_can_impersonate(client, session):
    await _mk(session, "bot@impm.team", role="bot")
    await _mk(session, "kbj@impm.team", role="admin")
    tok = await _token(client, "bot@impm.team")

    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.json()["email"] == "bot@impm.team"

    me2 = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tok}", "X-Act-As": "kbj@impm.team"},
    )
    assert me2.json()["email"] == "kbj@impm.team"


async def test_nonbot_cannot_impersonate(client, session):
    await _mk(session, "mjs@impm.team", role="member")
    await _mk(session, "kbj@impm.team", role="admin")
    tok = await _token(client, "mjs@impm.team")
    me = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tok}", "X-Act-As": "kbj@impm.team"},
    )
    assert me.json()["email"] == "mjs@impm.team"  # 무시됨


async def test_impersonation_attributes_actions(client, session):
    await _mk(session, "bot@impm.team", role="bot")
    kbj = await _mk(session, "kbj@impm.team", role="admin")
    tok = await _token(client, "bot@impm.team")
    h = {"Authorization": f"Bearer {tok}", "X-Act-As": "kbj@impm.team"}

    pid = (await client.post("/api/projects", json={"key": "STR", "name": "S"}, headers=h)).json()["id"]
    issue = (await client.post(f"/api/projects/{pid}/issues", json={"title": "t"}, headers=h)).json()
    assert issue["reporter_id"] == kbj.id

    acts = (await client.get(f"/api/issues/{issue['id']}/activity", headers=h)).json()
    assert acts[0]["actor_id"] == kbj.id  # 활동로그도 대행자로 귀속


async def test_unknown_act_as_400(client, session):
    await _mk(session, "bot@impm.team", role="bot")
    tok = await _token(client, "bot@impm.team")
    r = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tok}", "X-Act-As": "ghost@impm.team"},
    )
    assert r.status_code == 400
