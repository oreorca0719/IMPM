"""관리자 계정 삭제 + 시드 재실행 시 유령 계정 방지."""
from app.core.security import hash_password
from app.models import User


async def _mk(session, email, role="member", pw="pw12345"):
    u = User(email=email, name=email.split("@")[0], role=role,
             password_hash=hash_password(pw), must_change_password=False)
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


async def _h(client, email, pw="pw12345"):
    r = await client.post("/api/auth/login", json={"email": email, "password": pw})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_admin_can_delete_unused_account(client, session):
    await _mk(session, "admin@impm.team", role="admin")
    ghost = await _mk(session, "ghost@impm.team")
    h = await _h(client, "admin@impm.team")

    r = await client.delete(f"/api/users/{ghost.id}", headers=h)
    assert r.status_code == 204
    assert all(u["id"] != ghost.id for u in (await client.get("/api/users", headers=h)).json())


async def test_member_cannot_delete(client, session):
    await _mk(session, "member@impm.team")
    ghost = await _mk(session, "ghost@impm.team")
    r = await client.delete(f"/api/users/{ghost.id}", headers=await _h(client, "member@impm.team"))
    assert r.status_code == 403


async def test_cannot_delete_self(client, session):
    admin = await _mk(session, "admin@impm.team", role="admin")
    r = await client.delete(f"/api/users/{admin.id}", headers=await _h(client, "admin@impm.team"))
    assert r.status_code == 400


async def test_cannot_delete_user_with_data(client, session):
    await _mk(session, "admin@impm.team", role="admin")
    worker = await _mk(session, "worker@impm.team")
    h_admin = await _h(client, "admin@impm.team")
    h_worker = await _h(client, "worker@impm.team")

    pid = (await client.post("/api/projects", json={"key": "STR", "name": "S"}, headers=h_worker)).json()["id"]
    await client.post(f"/api/projects/{pid}/issues", json={"title": "t"}, headers=h_worker)

    r = await client.delete(f"/api/users/{worker.id}", headers=h_admin)
    assert r.status_code == 409


async def test_seed_skips_when_users_exist(session):
    """이미 계정이 있으면 시드가 사용자를 재생성하지 않는다(유령 계정 방지)."""
    from sqlalchemy import func
    from sqlmodel import select

    import scripts.seed as seed

    await _mk(session, "someone@impm.team")
    before = (await session.exec(select(func.count()).select_from(User))).one()
    await seed.run()
    after = (await session.exec(select(func.count()).select_from(User))).one()
    assert after == before
