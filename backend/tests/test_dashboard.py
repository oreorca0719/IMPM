"""P7 검증 — 대시보드 집계."""
from datetime import date, timedelta


async def test_dashboard_aggregation(auth):
    c, h = auth["client"], auth["headers"]
    uid = auth["user"].id
    pid = (await c.post("/api/projects", json={"key": "STR", "name": "STRIPE"}, headers=h)).json()["id"]
    eid = (await c.post(f"/api/projects/{pid}/epics", json={"title": "설계"}, headers=h)).json()["id"]

    # 이슈 3개: 1 DONE(에픽), 1 진행중(담당자+마감임박), 1 TODO
    i1 = (await c.post(f"/api/projects/{pid}/issues", json={"title": "a", "epic_id": eid}, headers=h)).json()
    await c.post(f"/api/projects/{pid}/issues", json={"title": "b", "epic_id": eid}, headers=h)
    soon = (date.today() + timedelta(days=3)).isoformat()
    i3 = (await c.post(
        f"/api/projects/{pid}/issues",
        json={"title": "임박", "assignee_id": uid, "due_date": soon, "status": "IN_PROGRESS"},
        headers=h,
    )).json()
    await c.patch(f"/api/issues/{i1['id']}", json={"status": "DONE"}, headers=h)

    d = (await c.get(f"/api/projects/{pid}/dashboard", headers=h)).json()

    assert d["status_counts"].get("DONE") == 1
    assert d["status_counts"].get("IN_PROGRESS") == 1
    assert d["status_counts"].get("TODO") == 1

    ep = next(e for e in d["epic_progress"] if e["epic_key"].endswith("-1"))
    assert ep["total"] == 2 and ep["done"] == 1 and ep["percent"] == 50

    # 담당자 부하: 김범준 open>=1
    kbj = next(a for a in d["assignee_load"] if a["user"] == "김범준")
    assert kbj["open"] >= 1

    # 마감 임박: 임박 이슈 포함
    assert any(x["key"] == i3["key"] for x in d["due_soon"])
