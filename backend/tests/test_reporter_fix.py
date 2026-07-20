"""등록자(작성자) 정정 — 잘못된 계정으로 기록된 이슈 바로잡기."""
from app.core.security import hash_password
from app.models import User


async def _mk(session, email, pw="pw12345"):
    u = User(email=email, name=email.split("@")[0], role="admin",
             password_hash=hash_password(pw), must_change_password=False)
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _h(client, email, pw="pw12345"):
    r = await client.post("/api/auth/login", json={"email": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_change_reporter_and_log(client, session):
    cjh = await _mk(session, "cjh@impm.team")
    kbj = await _mk(session, "kbj@impm.team")
    h_cjh = await _h(client, "cjh@impm.team")
    h_kbj = await _h(client, "kbj@impm.team")

    pid = (await client.post("/api/projects", json={"key": "STR", "name": "S"}, headers=h_cjh)).json()["id"]
    issue = (await client.post(f"/api/projects/{pid}/issues", json={"title": "잘못 등록"}, headers=h_cjh)).json()
    assert issue["reporter_id"] == cjh.id

    # 김범준으로 등록자 정정
    r = await client.patch(f"/api/issues/{issue['id']}", json={"reporter_id": kbj.id}, headers=h_kbj)
    assert r.status_code == 200
    assert r.json()["reporter_id"] == kbj.id

    # 정정 이력이 활동로그에 남는다
    acts = (await client.get(f"/api/issues/{issue['id']}/activity", headers=h_kbj)).json()
    rc = [a for a in acts if a["action"] == "reporter_changed"]
    assert len(rc) == 1
    assert rc[0]["old_value"] == str(cjh.id)
    assert rc[0]["new_value"] == str(kbj.id)
    assert rc[0]["actor_id"] == kbj.id  # 정정한 사람


async def test_reporter_must_be_valid(client, session):
    kbj = await _mk(session, "kbj@impm.team")
    h = await _h(client, "kbj@impm.team")
    pid = (await client.post("/api/projects", json={"key": "STR", "name": "S"}, headers=h)).json()["id"]
    issue = (await client.post(f"/api/projects/{pid}/issues", json={"title": "t"}, headers=h)).json()

    assert (await client.patch(f"/api/issues/{issue['id']}", json={"reporter_id": 9999}, headers=h)).status_code == 400
    assert (await client.patch(f"/api/issues/{issue['id']}", json={"reporter_id": None}, headers=h)).status_code == 400
