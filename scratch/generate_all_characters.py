import os, sys, time, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.project_manager import get_project, save_or_update_project, generate_character_portrait

project_id = "platero_y_yo"
proj = get_project(project_id)

prompts_update = {
    "lord": (
        "Character model sheet of Lord, an old noble English greyhound dog, standing naturally on all four legs, "
        "authentic quadruped canine anatomy, no humans. Melancholic wise eyes, lean ribs visible beneath an aged brindle grey coat, "
        "grey fur around muzzle. Exactly four distinct full-body views: front view, side profile view, three-quarters angle, and rear back view. "
        "Delicate poetic watercolor and ink storybook illustration, soft translucent washes, visible paper grain texture, "
        "subtle sepia pencil outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, "
        "no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece."
    ),
    "canario_verde": (
        "Character model sheet of El Canario Verde, a tiny singing canary bird, perched naturally, "
        "winged avian bird anatomy with feathers and tiny beak, no humans, no quadrupeds. "
        "Radiant emerald green plumage with fresh lemon-yellow highlights, small shiny seed-like dark eyes, delicate beak. "
        "Exactly four distinct views: front view, side profile view, three-quarters angle, and rear back view. "
        "Delicate poetic watercolor and ink storybook illustration, soft translucent washes, visible paper grain texture, "
        "subtle sepia pencil outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, "
        "no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece."
    ),
    "la_nina_chica": (
        "Character model sheet of La Niña Chica, a petite angelic young Andalusian girl from Moguer, "
        "standing alone head to toe, human anatomy, no other characters. Rosy cheeks, braided blonde hair with ribbons, "
        "clear innocent eyes, wearing a simple rustic percale dress with ruffled white apron and worn leather shoes. "
        "Exactly four distinct full-body views: front view, side profile view, three-quarters angle, and rear back view. "
        "Delicate poetic watercolor and ink storybook illustration, soft translucent washes, visible paper grain texture, "
        "subtle sepia pencil outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, "
        "no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece."
    ),
    "anilla_la_hungara": (
        "Character model sheet of Anilla la Húngara, an Andalusian flamenco dancer woman, "
        "standing alone head to toe, human anatomy, no other characters. Warm tanned skin, sparkling dark ember eyes, "
        "wavy black hair with tortoiseshell comb, wearing a colorful layered ruffled flamenco skirt and Manila shawl. "
        "Exactly four distinct full-body views: front view, side profile view, three-quarters angle, and rear back view. "
        "Delicate poetic watercolor and ink storybook illustration, soft translucent washes, visible paper grain texture, "
        "subtle sepia pencil outlines, warm Mediterranean sunlight, isolated on solid plain pure white background, "
        "no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece."
    )
}

# 1. Update prompts in project_data first
for char in proj.get("personajes", []):
    cid = char.get("id")
    if cid in prompts_update:
        char["prompt_retrato"] = prompts_update[cid]
        print(f"Updated prompt for {cid}")

save_or_update_project(proj)
print("Saved updated prompts to proyecto.json")

# 2. Generate each character
targets = ["lord", "canario_verde", "la_nina_chica", "anilla_la_hungara"]
for i, cid in enumerate(targets):
    print(f"\n==========================================")
    print(f"[{i+1}/{len(targets)}] Generando personaje: {cid}...")
    print(f"==========================================")
    prompt = prompts_update[cid]
    try:
        t0 = time.time()
        res = generate_character_portrait(
            project_id=project_id,
            character_id=cid,
            prompt_override=prompt,
            sin_fondo=True,
            formato_vista="giro_360"
        )
        print(f"SUCCESS {cid} en {round(time.time() - t0, 1)}s: {res.get('imagen_url')}")
    except Exception as e:
        print(f"ERROR generando {cid}: {e}")

print("\n--- PROCESO DE GENERACIÓN COMPLETADO ---")
