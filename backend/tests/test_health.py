"""P0 검증 — 앱이 부팅되고 헬스체크가 응답한다."""


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "IMPM"


async def test_openapi_docs(client):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "IMPM"
