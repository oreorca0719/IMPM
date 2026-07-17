"""P3 검증 — 댓글 CRUD(본인 제한) + 이슈 변경 시 활동로그 자동 생성."""


async def _project_issue(c, h):
    pid = (await c.post("/api/projects", json={"key": "STR", "name": "STRIPE"}, headers=h)).json()["id"]
    iid = (await c.post(f"/api/projects/{pid}/issues", json={"title": "이슈"}, headers=h)).json()["id"]
    return pid, iid


async def test_comment_crud_and_owner_guard(auth):
    c, h = auth["client"], auth["headers"]
    _, iid = await _project_issue(c, h)

    created = await c.post(f"/api/issues/{iid}/comments", json={"body": "첫 댓글"}, headers=h)
    assert created.status_code == 201
    cid = created.json()["id"]

    listed = await c.get(f"/api/issues/{iid}/comments", headers=h)
    assert len(listed.json()) == 1

    upd = await c.patch(f"/api/comments/{cid}", json={"body": "수정됨"}, headers=h)
    assert upd.json()["body"] == "수정됨"

    # 다른 사용자는 수정/삭제 불가
    from app.core.security import hash_password
    from app.models import User

    other = User(email="mjs@impm.team", name="문준석", password_hash=hash_password("pw"))
    auth["session"].add(other)
    await auth["session"].commit()
    login = await c.post("/api/auth/login", json={"email": "mjs@impm.team", "password": "pw"})
    oh = {"Authorization": f"Bearer {login.json()['access_token']}"}
    forbidden = await c.patch(f"/api/comments/{cid}", json={"body": "침범"}, headers=oh)
    assert forbidden.status_code == 403

    d = await c.delete(f"/api/comments/{cid}", headers=h)
    assert d.status_code == 204
    assert len(( await c.get(f"/api/issues/{iid}/comments", headers=h)).json()) == 0


async def test_activity_created_on_issue_create(auth):
    c, h = auth["client"], auth["headers"]
    _, iid = await _project_issue(c, h)
    acts = (await c.get(f"/api/issues/{iid}/activity", headers=h)).json()
    assert len(acts) == 1
    assert acts[0]["action"] == "created"


async def test_activity_on_status_and_assignee_change(auth):
    c, h = auth["client"], auth["headers"]
    _, iid = await _project_issue(c, h)
    uid = auth["user"].id

    # 상태 + 담당자 동시 변경 → 활동 2건 추가
    await c.patch(
        f"/api/issues/{iid}",
        json={"status": "IN_PROGRESS", "assignee_id": uid},
        headers=h,
    )
    acts = (await c.get(f"/api/issues/{iid}/activity", headers=h)).json()
    actions = [a["action"] for a in acts]
    assert "created" in actions
    assert "status_changed" in actions
    assert "assignee_changed" in actions

    # 시간 역순: 최신이 먼저
    status_log = next(a for a in acts if a["action"] == "status_changed")
    assert status_log["old_value"] == "TODO"
    assert status_log["new_value"] == "IN_PROGRESS"


async def test_activity_on_move(auth):
    c, h = auth["client"], auth["headers"]
    _, iid = await _project_issue(c, h)
    await c.patch(
        f"/api/issues/{iid}/move", json={"status": "DONE", "board_order": 1.0}, headers=h
    )
    acts = (await c.get(f"/api/issues/{iid}/activity", headers=h)).json()
    assert any(a["action"] == "status_changed" and a["new_value"] == "DONE" for a in acts)


async def test_no_activity_when_no_change(auth):
    c, h = auth["client"], auth["headers"]
    _, iid = await _project_issue(c, h)
    # 제목만 변경(추적 대상 아님) → created 외 활동 없음
    await c.patch(f"/api/issues/{iid}", json={"title": "새 제목"}, headers=h)
    acts = (await c.get(f"/api/issues/{iid}/activity", headers=h)).json()
    assert len(acts) == 1 and acts[0]["action"] == "created"
