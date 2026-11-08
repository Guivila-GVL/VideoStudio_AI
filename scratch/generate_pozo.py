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

eid = "pozo_viejo_huerto"
prompt = (
    "Children's book watercolor illustration of an ancient rustic stone water well surrounded by centenary fig trees "
    "and ivy-covered adobe walls in Moguer Andalusia, ripe open pomegranates, green pond reflecting golden sunlight, "
    "delicate poetic watercolor washes, textured paper grain, empty scene, no people, vertical 9:16 background scenery, masterpiece"
)
dest_jpg = ESCENARIOS_DIR / f"{eid}.jpg"

clean = sanitize_image_prompt(prompt, max_chars=600)
encoded = urllib.parse.quote(clean)
url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=sana&nologo=true"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Requesting pozo_viejo_huerto from Pollinations sana...")
r = requests.get(url, headers=headers, timeout=90)
if r.status_code == 200 and len(r.content) > 2000 and r.headers.get("content-type", "").startswith("image"):
    temp_jpg = dest_jpg.parent / f"temp_{dest_jpg.name}"
    with open(temp_jpg, "wb") as f:
        f.write(r.content)
    crop_and_resize_to_vertical(temp_jpg, dest_jpg)
    if temp_jpg.exists():
        temp_jpg.unlink()
    print(f"[SUCCESS] {dest_jpg.name} generated successfully ({dest_jpg.stat().st_size} bytes)")

    # Update metadata
    proj = get_project(PROJECT_ID)
    ts = int(time.time())
    for e in proj.get("escenarios", []):
        if e["id"] == eid:
            e["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/escenarios/{eid}.jpg?t={ts}"
            e["prompt_escenario"] = prompt
            break
    save_or_update_project(proj)
    print("Metadata synchronized.")
else:
    print(f"Failed: HTTP {r.status_code} ({len(r.content)} bytes)")
    if r.status_code != 200:
        print(r.text[:200])
