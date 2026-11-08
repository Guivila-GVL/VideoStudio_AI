import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.image_engine import crop_and_resize_to_vertical
from app.core.project_manager import get_project, save_or_update_project

PROJECT_ID = "platero_y_yo"
PROJECT_DIR = ROOT_DIR / "proyectos" / PROJECT_ID
ESCENARIOS_DIR = PROJECT_DIR / "escenarios"
ESCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

SCENARIOS = {
    "pozo_viejo_huerto": (
        "Children's storybook watercolor illustration on textured paper of El Pozo Viejo y el Huerto in Moguer, "
        "an ancient rustic stone water well surrounded by centenary fig trees, ivy-covered adobe tapial walls, "
        "ripe open pomegranates, green reflective pond, warm golden Mediterranean sunlight, "
        "delicate poetic watercolor washes, subtle pencil outlines, empty scene, no people, "
        "vertical 9:16 portrait composition, masterpiece"
    ),
    "establo_platero": (
        "Children's storybook watercolor illustration on textured paper of El Establo de Platero, "
        "a cozy rustic Andalusian barn interior with darkened wooden beams and Arabic roof tiles, "
        "pine manger filled with fresh golden straw and hay, warm sunlight beams piercing wooden gaps, "
        "delicate poetic watercolor washes, subtle pencil outlines, empty scene, no people, "
        "vertical 9:16 portrait composition, masterpiece"
    ),
    "ribera_rio_tinto": (
        "Children's storybook watercolor illustration on textured paper of La Ribera del Rio Tinto in Andalusia at sunset, "
        "mystical reddish coppery water reflections, marshland reeds swaying in the sea breeze, "
        "purple twilight sky with fiery golden accents, abandoned wooden rowboats on muddy shore, "
        "delicate poetic watercolor washes, subtle pencil outlines, empty scene, no people, "
        "vertical 9:16 portrait composition, masterpiece"
    )
}

openai_key = os.getenv("OPENAI_API_KEY")

def generate_with_dalle(eid: str, prompt: str, dest_path: Path):
    print(f"Generating {eid} with DALL-E 3...")
    from openai import OpenAI
    client = OpenAI(api_key=openai_key)
    res = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1792",
        quality="standard",
        n=1
    )
    url = res.data[0].url
    r = requests.get(url, timeout=40)
    temp_path = dest_path.parent / f"temp_{dest_path.name}"
    with open(temp_path, "wb") as f:
        f.write(r.content)
    crop_and_resize_to_vertical(temp_path, dest_path)
    if temp_path.exists():
        temp_path.unlink()
    print(f"[SUCCESS] {dest_path.name} saved via DALL-E 3 ({dest_path.stat().st_size} bytes)")

def update_metadata():
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
    print("Metadata synchronized.")

if __name__ == "__main__":
    for eid, prompt in SCENARIOS.items():
        dest = ESCENARIOS_DIR / f"{eid}.jpg"
        if dest.exists() and dest.stat().st_size > 50000:
            print(f"[SKIP] {eid} already exists.")
            continue
        try:
            generate_with_dalle(eid, prompt, dest)
            update_metadata()
        except Exception as e:
            print(f"[ERROR] DALL-E 3 error for {eid}: {e}")

    update_metadata()
    print("ALL SCENARIOS COMPLETE!")
