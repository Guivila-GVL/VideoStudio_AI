import os
import sys
import time
import json
import urllib.parse
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.image_engine import crop_and_resize_to_vertical, sanitize_image_prompt
from app.core.project_manager import get_project, save_or_update_project

PROJECT_ID = "platero_y_yo"
PROJECT_DIR = ROOT_DIR / "proyectos" / PROJECT_ID
ESCENARIOS_DIR = PROJECT_DIR / "escenarios"
ESCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

SCENARIOS = {
    "pozo_viejo_huerto": (
        "Children's book watercolor illustration of an ancient rustic stone water well surrounded by centenary fig trees "
        "and ivy-covered adobe walls in Moguer Andalusia, ripe open pomegranates, green pond reflecting golden sunlight, "
        "delicate poetic watercolor washes, textured paper grain, empty scene, no people, vertical 9:16 background scenery, masterpiece"
    ),
    "establo_platero": (
        "Children's book watercolor illustration of a cozy rustic Andalusian barn interior with darkened wooden beams "
        "and Arabic roof tiles, pine manger filled with fresh hay and golden straw, warm sunlight beams piercing wooden door gaps, "
        "delicate poetic watercolor washes, textured paper grain, empty scene, no people, vertical 9:16 background scenery, masterpiece"
    ),
    "ribera_rio_tinto": (
        "Children's book watercolor illustration of the mystical banks of Rio Tinto in Andalusia at sunset, "
        "reddish coppery water reflections, marshland reeds swaying in breeze, purple twilight sky with fiery golden accents, "
        "delicate poetic watercolor washes, textured paper grain, empty scene, no people, vertical 9:16 background scenery, masterpiece"
    )
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def generate_scenario(eid: str, prompt: str, dest_jpg: Path):
    print(f"\n==========================================")
    print(f"Generating Scenario: {eid}")
    print(f"==========================================")
    clean = sanitize_image_prompt(prompt, max_chars=600)
    encoded = urllib.parse.quote(clean)

    models_to_try = ["sana", "flux", "turbo"]
    for m in models_to_try:
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model={m}&nologo=true"
        print(f"Trying model '{m}'...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200 and len(r.content) > 2000 and r.headers.get("content-type", "").startswith("image"):
                temp_jpg = dest_jpg.parent / f"temp_{dest_jpg.name}"
                with open(temp_jpg, "wb") as f:
                    f.write(r.content)
                crop_and_resize_to_vertical(temp_jpg, dest_jpg)
                if temp_jpg.exists():
                    temp_jpg.unlink()
                print(f"[SUCCESS] {dest_jpg.name} generated with model '{m}' ({dest_jpg.stat().st_size} bytes)")
                return True
            else:
                print(f"  Model '{m}' returned {r.status_code} ({len(r.content)} bytes)")
        except Exception as ex:
            print(f"  Model '{m}' exception: {ex}")
    return False

def sync_metadata():
    proj = get_project(PROJECT_ID)
    ts = int(time.time())
    for e in proj.get("escenarios", []):
        eid = e["id"]
        jpg = ESCENARIOS_DIR / f"{eid}.jpg"
        if jpg.exists():
            e["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/escenarios/{eid}.jpg?t={ts}"
            if eid in SCENARIOS:
                e["prompt_escenario"] = SCENARIOS[eid]
    save_or_update_project(proj)
    print("[METADATA] Synchronized proyecto.json successfully.")

if __name__ == "__main__":
    for eid, prompt in SCENARIOS.items():
        dest = ESCENARIOS_DIR / f"{eid}.jpg"
        if dest.exists() and dest.stat().st_size > 50000:
            print(f"[SKIP] {eid} already exists.")
            continue
        ok = generate_scenario(eid, prompt, dest)
        if ok:
            sync_metadata()
        print("Cooldown 48s for next scenario...")
        time.sleep(48)

    sync_metadata()
    print("\nALL SCENARIOS COMPLETE!")
