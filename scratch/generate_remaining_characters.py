import os, sys, time, json, re, urllib.parse, requests
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.image_engine import crop_and_resize_to_vertical, remove_image_background
from app.core.project_manager import get_project, save_or_update_project

project_id = "platero_y_yo"
proj = get_project(project_id)
personajes_dir = Path("proyectos/platero_y_yo/personajes")
personajes_dir.mkdir(parents=True, exist_ok=True)

prompts = {
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

def generate_one_character(cid: str, prompt: str):
    print(f"\n==========================================")
    print(f"Generando personaje: {cid}")
    print(f"==========================================")
    clean_prompt = " ".join(prompt.strip().split()).replace('"', '').replace("'", "")
    encoded_prompt = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&model=sana&nologo=true"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    max_attempts = 5
    for attempt in range(max_attempts):
        print(f"Intento {attempt+1}/{max_attempts} para {cid}...")
        try:
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type", "").startswith("image"):
                print(f"Éxito descargando imagen ({len(r.content)} bytes)")
                temp_jpg = personajes_dir / f"temp_{cid}.jpg"
                final_jpg = personajes_dir / f"{cid}.jpg"
                final_png = personajes_dir / f"{cid}.png"

                with open(temp_jpg, "wb") as f:
                    f.write(r.content)

                crop_and_resize_to_vertical(temp_jpg, final_jpg)
                if temp_jpg.exists():
                    temp_jpg.unlink()

                print(f"Guardado {final_jpg} ({os.path.getsize(final_jpg)} bytes)")
                print("Generando recorte PNG con rembg...")
                remove_image_background(final_jpg, final_png)
                print(f"Guardado {final_png} ({os.path.getsize(final_png)} bytes)")

                # Actualizar proyecto.json
                p = get_project(project_id)
                for char in p.get("personajes", []):
                    if char.get("id") == cid:
                        ts = int(time.time())
                        char["imagen_url"] = f"/proyectos_data/{project_id}/personajes/{cid}.jpg?t={ts}"
                        char["prompt_retrato"] = prompt
                        break
                save_or_update_project(p)
                print(f"Registrado en proyecto.json como {char['imagen_url']}")
                return True
            elif r.status_code in (402, 429):
                wait_sec = 50
                try:
                    match = re.search(r"Retry after (\d+)s", r.text)
                    if match:
                        wait_sec = max(int(match.group(1)) + 5, 20)
                except Exception:
                    pass
                print(f"Rate limit de Pollinations. Esperando {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                print(f"Respuesta inesperada: HTTP {r.status_code}. Reintentando en 15s...")
                time.sleep(15)
        except Exception as e:
            print(f"Error en petición: {e}. Esperando 15s...")
            time.sleep(15)
    return False

# Ejecutar secuencialmente
for cid, prompt in prompts.items():
    ok = generate_one_character(cid, prompt)
    if not ok:
        print(f"ALERTA: No se pudo generar {cid} tras varios intentos.")
    # Cooldown preventivo de 48s entre personajes
    print("Esperando enfriamiento de 48s para el siguiente personaje...")
    time.sleep(48)

print("\n=== TODOS LOS PERSONAJES GENERADOS EXITOSAMENTE ===")
