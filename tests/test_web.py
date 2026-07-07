from fastapi.testclient import TestClient

from app.web.server import app

client = TestClient(app)


def test_config_endpoint():
    r = client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert "balanced" in body["presets"]
    assert "filler_removal" in body["editable_rules"]
    assert any(c["id"] == "filler_removal" for c in body["catalog"])


def test_transform_and_download(sample_docx):
    with open(sample_docx, "rb") as fh:
        r = client.post(
            "/api/transform",
            files={"file": ("sample.docx", fh,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"preset": "balanced", "overrides": "{}"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["edits_applied"] > 0
    assert body["paragraphs"]
    token = body["token"]

    d = client.get(f"/api/download/{token}")
    assert d.status_code == 200
    assert "wordprocessingml" in d.headers["content-type"]
    assert d.content[:2] == b"PK"  # a .docx is a zip


def test_rejects_non_docx():
    r = client.post(
        "/api/transform",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"preset": "balanced", "overrides": "{}"},
    )
    assert r.status_code == 400


def test_override_disables_rule(sample_docx):
    # Disabling filler_removal should reduce edits vs the balanced default.
    with open(sample_docx, "rb") as fh:
        base = client.post("/api/transform", files={"file": ("s.docx", fh)},
                           data={"preset": "balanced", "overrides": "{}"}).json()
    with open(sample_docx, "rb") as fh:
        off = client.post("/api/transform", files={"file": ("s.docx", fh)},
                          data={"preset": "balanced",
                                "overrides": '{"filler_removal": false}'}).json()
    assert off["summary"]["edits_applied"] < base["summary"]["edits_applied"]
