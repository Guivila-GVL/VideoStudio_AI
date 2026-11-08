import os
import sys
import time
import json
import re
import shutil
import urllib.parse
import requests
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.image_engine import crop_and_resize_to_vertical, remove_image_background, sanitize_image_prompt
from app.core.project_manager import get_project, save_or_update_project

PROJECT_ID = "platero_y_yo"
PROJECT_DIR = ROOT_DIR / "proyectos" / PROJECT_ID
PERSONAJES_DIR = PROJECT_DIR / "personajes"
ESCENARIOS_DIR = PROJECT_DIR / "escenarios"
MEDIA_DIR = ROOT_DIR / "app" / "static" / "media"

PERSONAJES_DIR.mkdir(parents=True, exist_ok=True)
ESCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

# 1. Adopt already verified high-quality test images
existing_mappings = {
    "personajes": {
        "lord": MEDIA_DIR / "img_52c5c5ac18.jpg"
    },
    "escenarios": {
        "calles_blancas_moguer": MEDIA_DIR / "img_9ff4f4da55.jpg",
        "colinas_molino_viento": MEDIA_DIR / "img_e6ba5388ba.jpg"
    }
}

for char_id, src_path in existing_mappings["personajes"].items():
    if src_path.exists():
        dest = PERSONAJES_DIR / f"{char_id}.jpg"
        shutil.copy2(src_path, dest)
        print(f"[PRESERVED] Copied {src_path.name} to {dest.name}")
        png_dest = PERSONAJES_DIR / f"{char_id}.png"
        remove_image_background(dest, png_dest)

for esc_id, src_path in existing_mappings["escenarios"].items():
    if src_path.exists():
        dest = ESCENARIOS_DIR / f"{esc_id}.jpg"
        shutil.copy2(src_path, dest)
        print(f"[PRESERVED] Copied {src_path.name} to {dest.name}")

# Characters and scenarios that need generation
CHARACTERS_TO_GENERATE = {
    "el_poeta": "Full body character turnaround model sheet of the young Spanish contemplative writer and poet of Moguer around 25 years old adult male, sensitive noble face, dark wavy hair, thoughtful eyes, wearing a rustic raw linen shirt unbuttoned at the collar, fine dark wool waistcoat, earthy trousers, and holding or wearing a wide-brim Andalusian hat, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, adult human anatomy, standing alone head to toe, no children, no other characters, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "canario_verde": "Full body character turnaround model sheet of a tiny singing canary bird named El Canario Verde, radiant emerald-green plumage with fresh lemon-yellow highlights, small shiny eyes, perched naturally, winged avian anatomy with feathers and beak, no humans, no quadrupeds, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "la_nina_chica": "Full body character turnaround model sheet of a sweet petite angelic young Andalusian girl from Moguer named La Nina Chica, rosy cheeks, braided blonde hair with ribbons, wearing a rustic percale dress and white ruffled apron, human child anatomy, no other characters, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "anilla_la_hungara": "Full body character turnaround model sheet of vibrant Andalusian flamenco dancer woman named Anilla la Hungara, warm tanned skin, sparkling dark ember eyes, wavy black hair with comb, colorful ruffled layered flamenco dress and Manila shawl, adult human anatomy, no other characters, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece"
}

SCENARIOS_TO_GENERATE = {
    "pozo_viejo_huerto": "Children's book watercolor illustration of El Pozo Viejo y el Huerto de los Frailes in Moguer, a shady rustic stone water well surrounded by ancient fig trees, ivy-covered adobe walls, ripe open pomegranates, green pond reflecting golden sunlight, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece",
    "establo_platero": "Children's book watercolor illustration of El Establo de Platero, a rustic cozy Andalusian barn with darkened wooden beams and Arabic roof tiles, pine manger filled with fresh hay and golden straw, sunlight beams piercing wooden door gaps, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece",
    "ribera_rio_tinto": "Children's book watercolor illustration of La Ribera del Rio Tinto in Andalusia at dusk, mystical reddish wine-colored water reflections, marshland reeds swaying in the gentle Atlantic breeze, purple twilight sky with fiery sunset accents, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def generate_asset_image(prompt: str, dest_jpg: Path) -> bool:
    clean_prompt = sanitize_image_prompt(prompt, max_chars=800)
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=sana&nologo=true"

    max_retries = 6
    for attempt in range(max_retries):
        print(f"  Attempt {attempt+1}/{max_retries}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type", "").startswith("image"):
                temp_jpg = dest_jpg.parent / f"temp_{dest_jpg.name}"
                with open(temp_jpg, "wb") as f:
                    f.write(r.content)
                crop_and_resize_to_vertical(temp_jpg, dest_jpg)
                if temp_jpg.exists():
                    temp_jpg.unlink()
                print(f"  [SUCCESS] Saved {dest_jpg.name} ({os.path.getsize(dest_jpg)} bytes)")
                return True
            elif r.status_code in (402, 429):
                wait_time = 48
                try:
                    m = re.search(r"Retry after (\d+)s", r.text)
                    if m:
                        wait_time = max(int(m.group(1)) + 5, 20)
                except Exception:
                    pass
                print(f"  Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  HTTP {r.status_code}. Waiting 15s...")
                time.sleep(15)
        except Exception as ex:
            print(f"  Exception: {ex}. Waiting 15s...")
            time.sleep(15)
    return False

def sync_all_to_project_json():
    proj = get_project(PROJECT_ID)
    ts = int(time.time())

    for c in proj.get("personajes", []):
        cid = c["id"]
        jpg_path = PERSONAJES_DIR / f"{cid}.jpg"
        if jpg_path.exists():
            c["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/personajes/{cid}.jpg?t={ts}"
            if cid in CHARACTERS_TO_GENERATE:
                c["prompt_retrato"] = CHARACTERS_TO_GENERATE[cid]

    for e in proj.get("escenarios", []):
        eid = e["id"]
        jpg_path = ESCENARIOS_DIR / f"{eid}.jpg"
        if jpg_path.exists():
            e["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/escenarios/{eid}.jpg?t={ts}"
            if eid in SCENARIOS_TO_GENERATE:
                e["prompt_escenario"] = SCENARIOS_TO_GENERATE[eid]

    save_or_update_project(proj)
    print("\n[PROYECTO.JSON] Updated project metadata successfully!")

if __name__ == "__main__":
    # Generate Characters
    for cid, prompt in CHARACTERS_TO_GENERATE.items():
        dest = PERSONAJES_DIR / f"{cid}.jpg"
        if dest.exists() and dest.stat().st_size > 50000:
            print(f"[SKIP] {cid} already exists ({dest.stat().st_size} bytes)")
            continue
        print(f"\n>>> Generating Character: {cid}")
        ok = generate_asset_image(prompt, dest)
        if ok:
            png_dest = PERSONAJES_DIR / f"{cid}.png"
            try:
                print(f"  Removing background for {cid}.png...")
                remove_image_background(dest, png_dest)
            except Exception as e:
                print(f"  rembg notice: {e}")
            sync_all_to_project_json()
        print("Waiting 48s cooldown before next generation...")
        time.sleep(48)

    # Generate Scenarios
    for eid, prompt in SCENARIOS_TO_GENERATE.items():
        dest = ESCENARIOS_DIR / f"{eid}.jpg"
        if dest.exists() and dest.stat().st_size > 50000:
            print(f"[SKIP] {eid} already exists ({dest.stat().st_size} bytes)")
            continue
        print(f"\n>>> Generating Scenario: {eid}")
        ok = generate_asset_image(prompt, dest)
        if ok:
            sync_all_to_project_json()
        print("Waiting 48s cooldown before next generation...")
        time.sleep(48)

    sync_all_to_project_json()
    print("\n==========================================")
    print("STEP 3 BATCH GENERATION COMPLETE!")
    print("==========================================")
