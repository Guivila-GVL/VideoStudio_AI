import os
import sys
import time
import json
import re
import shutil
import urllib.parse
import requests
from pathlib import Path

# Line buffering for immediate output visibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.core.image_engine import crop_and_resize_to_vertical, remove_image_background, sanitize_image_prompt
from app.core.project_manager import get_project, save_or_update_project

PROJECT_ID = "platero_y_yo"
PROJECT_DIR = ROOT_DIR / "proyectos" / PROJECT_ID
PERSONAJES_DIR = PROJECT_DIR / "personajes"
ESCENARIOS_DIR = PROJECT_DIR / "escenarios"

PERSONAJES_DIR.mkdir(parents=True, exist_ok=True)
ESCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

# 4 characters to generate
CHARACTERS = {
    "el_poeta": "Full body character turnaround model sheet of the young Spanish contemplative writer and poet of Moguer around 25 years old adult male, sensitive noble face, dark wavy hair, thoughtful eyes, wearing a rustic raw linen shirt unbuttoned at the collar, fine dark wool waistcoat, earthy trousers, and holding or wearing a wide-brim Andalusian hat, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, adult human anatomy, standing alone head to toe, no children, no other characters, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "canario_verde": "Full body character turnaround model sheet of a tiny singing canary bird named El Canario Verde, radiant emerald-green plumage with fresh lemon-yellow highlights, small shiny eyes, perched naturally, winged avian anatomy with feathers and beak, no humans, no quadrupeds, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "la_nina_chica": "Full body character turnaround model sheet of a sweet petite angelic young Andalusian girl from Moguer named La Nina Chica, rosy cheeks, braided blonde hair with ribbons, wearing a rustic percale dress and white ruffled apron, human child anatomy, no other characters, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece",
    "anilla_la_hungara": "Full body character turnaround model sheet of vibrant Andalusian flamenco dancer woman named Anilla la Hungara, warm tanned skin, sparkling dark ember eyes, wavy black hair with comb, colorful ruffled layered flamenco dress and Manila shawl, adult human anatomy, no other characters, four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view, delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece"
}

# 3 scenarios to generate
SCENARIOS = {
    "pozo_viejo_huerto": "Children's book watercolor illustration of El Pozo Viejo y el Huerto de los Frailes in Moguer, a shady rustic stone water well surrounded by ancient fig trees, ivy-covered adobe walls, ripe open pomegranates, green pond reflecting golden sunlight, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece",
    "establo_platero": "Children's book watercolor illustration of El Establo de Platero, a rustic cozy Andalusian barn with darkened wooden beams and Arabic roof tiles, pine manger filled with fresh hay and golden straw, sunlight beams piercing wooden door gaps, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece",
    "ribera_rio_tinto": "Children's book watercolor illustration of La Ribera del Rio Tinto in Andalusia at dusk, mystical reddish wine-colored water reflections, marshland reeds swaying in the gentle Atlantic breeze, purple twilight sky with fiery sunset accents, delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight, empty scene, no people, vertical 9:16 background scenery, masterpiece"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

LAST_CALL_TIMESTAMP = 0

def fetch_from_pollinations(prompt: str, dest_jpg: Path) -> bool:
    global LAST_CALL_TIMESTAMP
    clean_prompt = sanitize_image_prompt(prompt, max_chars=800)
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=sana&nologo=true"

    max_retries = 5
    for attempt in range(max_retries):
        # Guarantee at least 48s cooldown since last call
        elapsed = time.time() - LAST_CALL_TIMESTAMP
        if elapsed < 48:
            sleep_time = int(48 - elapsed) + 1
            print(f"  [COOLDOWN] Waiting {sleep_time}s to respect Pollinations IP rate limit...", flush=True)
            time.sleep(sleep_time)

        print(f"  [HTTP] Requesting generation (attempt {attempt+1}/{max_retries})...", flush=True)
        LAST_CALL_TIMESTAMP = time.time()

        try:
            r = requests.get(url, headers=HEADERS, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type", "").startswith("image"):
                temp_jpg = dest_jpg.parent / f"temp_{dest_jpg.name}"
                with open(temp_jpg, "wb") as f:
                    f.write(r.content)
                crop_and_resize_to_vertical(temp_jpg, dest_jpg)
                if temp_jpg.exists():
                    temp_jpg.unlink()
                print(f"  [SUCCESS] {dest_jpg.name} generated successfully ({os.path.getsize(dest_jpg)} bytes)", flush=True)
                return True
            elif r.status_code in (402, 429):
                wait_sec = 50
                try:
                    match = re.search(r"Retry after (\d+)s", r.text)
                    if match:
                        wait_sec = max(int(match.group(1)) + 5, 48)
                except Exception:
                    pass
                print(f"  [RATE LIMIT] Pollinations returned {r.status_code}. Sleeping {wait_sec}s...", flush=True)
                time.sleep(wait_sec)
            else:
                print(f"  [STATUS] Unexpected HTTP {r.status_code}. Sleeping 15s...", flush=True)
                time.sleep(15)
        except Exception as ex:
            print(f"  [ERROR] {ex}. Sleeping 15s...", flush=True)
            time.sleep(15)

    return False

def update_metadata():
    proj = get_project(PROJECT_ID)
    ts = int(time.time())

    for c in proj.get("personajes", []):
        cid = c["id"]
        jpg = PERSONAJES_DIR / f"{cid}.jpg"
        if jpg.exists():
            c["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/personajes/{cid}.jpg?t={ts}"
            if cid in CHARACTERS:
                c["prompt_retrato"] = CHARACTERS[cid]

    for e in proj.get("escenarios", []):
        eid = e["id"]
        jpg = ESCENARIOS_DIR / f"{eid}.jpg"
        if jpg.exists():
            e["imagen_url"] = f"/proyectos_data/{PROJECT_ID}/escenarios/{eid}.jpg?t={ts}"
            if eid in SCENARIOS:
                e["prompt_escenario"] = SCENARIOS[eid]

    save_or_update_project(proj)
    print(f"  [METADATA] proyecto.json synchronized.", flush=True)

def main():
    print("==================================================", flush=True)
    print("STARTING ROBUST STEP 3 UNIFIED ASSET GENERATION", flush=True)
    print("==================================================", flush=True)

    # First update metadata to register preserved images
    update_metadata()

    # 1. Characters
    total_chars = len(CHARACTERS)
    for idx, (cid, prompt) in enumerate(CHARACTERS.items(), start=1):
        dest_jpg = PERSONAJES_DIR / f"{cid}.jpg"
        print(f"\n[{idx}/{total_chars}] Processing Character: {cid}", flush=True)
        if dest_jpg.exists() and dest_jpg.stat().st_size > 50000:
            print(f"  [SKIP] Already exists ({dest_jpg.stat().st_size} bytes)", flush=True)
            continue

        ok = fetch_from_pollinations(prompt, dest_jpg)
        if ok:
            png_dest = PERSONAJES_DIR / f"{cid}.png"
            print(f"  [REMBG] Generating transparent cutout for {cid}...", flush=True)
            try:
                remove_image_background(dest_jpg, png_dest)
                print(f"  [REMBG] Saved {png_dest.name} ({png_dest.stat().st_size} bytes)", flush=True)
            except Exception as e:
                print(f"  [REMBG NOTICE] {e}", flush=True)
            update_metadata()

    # 2. Scenarios
    total_scens = len(SCENARIOS)
    for idx, (eid, prompt) in enumerate(SCENARIOS.items(), start=1):
        dest_jpg = ESCENARIOS_DIR / f"{eid}.jpg"
        print(f"\n[{idx}/{total_scens}] Processing Scenario: {eid}", flush=True)
        if dest_jpg.exists() and dest_jpg.stat().st_size > 50000:
            print(f"  [SKIP] Already exists ({dest_jpg.stat().st_size} bytes)", flush=True)
            continue

        ok = fetch_from_pollinations(prompt, dest_jpg)
        if ok:
            update_metadata()

    print("\n==================================================", flush=True)
    print("ALL ASSETS SUCCESSFULLY GENERATED & SYNCHRONIZED!", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    main()
