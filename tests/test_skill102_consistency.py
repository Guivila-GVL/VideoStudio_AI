import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app
from app.core.project_manager import get_skill102_reference_prompts


def test_skill102_reference_prompts():
    data = get_skill102_reference_prompts("el_principito")
    assert data["personajes"], "debe haber personajes"
    p = data["personajes"][0]["prompt_6_vistas"]
    assert "#FFFFFF" in p and "front view" in p
    for e in data["escenarios"]:
        assert "9:16" in e["prompt_escenario"] and "Darb" not in e["prompt_escenario"].split("Strict")[0]
    r = TestClient(app).get("/api/projects/el_principito/consistency-reference-prompts")
    assert r.status_code == 200 and r.json()["success"]
    assert TestClient(app).get("/api/projects/no_existe_xx/consistency-reference-prompts").status_code == 404


if __name__ == "__main__":
    test_skill102_reference_prompts()
    print("[OK] skill102")
