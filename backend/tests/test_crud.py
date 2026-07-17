"""P2 검증 — 프로젝트·에픽·이슈 CRUD, 이슈키 채번, 라벨, 진행률."""


async def _project(client, headers, key="STR"):
    r = await client.post(
        "/api/projects", json={"key": key, "name": "STRIPE"}, headers=headers
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_project_create_and_duplicate_key(auth):
    c, h = auth["client"], auth["headers"]
    p = await _project(c, h)
    assert p["key"] == "STR"
    assert p["issue_seq"] == 0
    # 중복 키 → 409
    dup = await c.post("/api/projects", json={"key": "STR", "name": "x"}, headers=h)
    assert dup.status_code == 409


async def test_issue_key_numbering(auth):
    """에픽·이슈가 프로젝트 카운터를 공유하며 순차 채번."""
    c, h = auth["client"], auth["headers"]
    p = await _project(c, h)
    pid = p["id"]

    epic = await c.post(
        f"/api/projects/{pid}/epics", json={"title": "설계"}, headers=h
    )
    assert epic.status_code == 201
    assert epic.json()["key"] == "STR-1"

    i1 = await c.post(
        f"/api/projects/{pid}/issues", json={"title": "이슈 A"}, headers=h
    )
    i2 = await c.post(
        f"/api/projects/{pid}/issues", json={"title": "이슈 B"}, headers=h
    )
    assert i1.json()["key"] == "STR-2"
    assert i2.json()["key"] == "STR-3"
    # 생성 시 기본값
    assert i1.json()["status"] == "TODO"
    assert i1.json()["priority"] == "MEDIUM"
    assert i1.json()["reporter_id"] == auth["user"].id


async def test_issue_list_filters(auth):
    c, h = auth["client"], auth["headers"]
    pid = (await _project(c, h))["id"]
    await c.post(f"/api/projects/{pid}/issues", json={"title": "todo"}, headers=h)
    hi = await c.post(
        f"/api/projects/{pid}/issues",
        json={"title": "high 검색어", "priority": "HIGH", "status": "IN_PROGRESS"},
        headers=h,
    )
    # status 필터
    r = await c.get(f"/api/projects/{pid}/issues?status=IN_PROGRESS", headers=h)
    assert len(r.json()) == 1 and r.json()[0]["key"] == hi.json()["key"]
    # q 제목 검색
    r2 = await c.get(f"/api/projects/{pid}/issues?q=검색어", headers=h)
    assert len(r2.json()) == 1


async def test_issue_move_and_persist(auth):
    c, h = auth["client"], auth["headers"]
    pid = (await _project(c, h))["id"]
    iid = (await c.post(f"/api/projects/{pid}/issues", json={"title": "이동"}, headers=h)).json()["id"]

    mv = await c.patch(
        f"/api/issues/{iid}/move",
        json={"status": "DONE", "board_order": 5.5},
        headers=h,
    )
    assert mv.status_code == 200
    assert mv.json()["status"] == "DONE"
    # 재조회 유지
    got = await c.get(f"/api/issues/{iid}", headers=h)
    assert got.json()["status"] == "DONE"
    assert got.json()["board_order"] == 5.5


async def test_labels_attach_detach(auth):
    c, h = auth["client"], auth["headers"]
    pid = (await _project(c, h))["id"]
    iid = (await c.post(f"/api/projects/{pid}/issues", json={"title": "라벨"}, headers=h)).json()["id"]
    lbl = await c.post(
        f"/api/projects/{pid}/labels", json={"name": "버그", "color": "#EF4444"}, headers=h
    )
    lid = lbl.json()["id"]

    attached = await c.post(f"/api/issues/{iid}/labels", json={"label_id": lid}, headers=h)
    assert len(attached.json()["labels"]) == 1
    assert attached.json()["labels"][0]["name"] == "버그"

    detached = await c.delete(f"/api/issues/{iid}/labels/{lid}", headers=h)
    assert len(detached.json()["labels"]) == 0


async def test_epic_progress(auth):
    c, h = auth["client"], auth["headers"]
    pid = (await _project(c, h))["id"]
    eid = (await c.post(f"/api/projects/{pid}/epics", json={"title": "E"}, headers=h)).json()["id"]

    i1 = (await c.post(f"/api/projects/{pid}/issues", json={"title": "a", "epic_id": eid}, headers=h)).json()
    await c.post(f"/api/projects/{pid}/issues", json={"title": "b", "epic_id": eid}, headers=h)
    # 하나 DONE 처리
    await c.patch(f"/api/issues/{i1['id']}", json={"status": "DONE"}, headers=h)

    epics = await c.get(f"/api/projects/{pid}/epics", headers=h)
    e = epics.json()[0]
    assert e["total"] == 2
    assert e["done"] == 1
    assert e["percent"] == 50


async def test_epic_delete_detaches_issues(auth):
    c, h = auth["client"], auth["headers"]
    pid = (await _project(c, h))["id"]
    eid = (await c.post(f"/api/projects/{pid}/epics", json={"title": "E"}, headers=h)).json()["id"]
    iid = (await c.post(f"/api/projects/{pid}/issues", json={"title": "x", "epic_id": eid}, headers=h)).json()["id"]

    d = await c.delete(f"/api/epics/{eid}", headers=h)
    assert d.status_code == 204
    got = await c.get(f"/api/issues/{iid}", headers=h)
    assert got.json()["epic_id"] is None
