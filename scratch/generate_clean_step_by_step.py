import os, sys, time, json, urllib.parse, requests
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.image_engine import crop_and_resize_to_vertical, remove_image_background
from app.core.project_manager import get_project, save_or_update_project

project_id = "platero_y_yo"
personajes_dir = Path("proyectos/platero_y_yo/personajes")
personajes_dir.mkdir(parents=True, exist_ok=True)

chars_to_generate = [
    {
        "id": "canario_verde",
        "name": "El Canario Verde",
        "prompt": (
            "Character turnaround model sheet, multiple views: front view, side profile view, three-quarter angle, and back view "
            "of a tiny green singing canary bird perched naturally, winged avian bird anatomy, vibrant emerald green feathers, "
            "lemon-yellow accents, tiny beak. 2D storybook watercolor illustration, Studio Ghibli style, clean ink line art, "
            "textured paper grain, soft color washes, warm sunlight, pure plain white background, vertical 9:16, masterpiece."
        )
    },
    {
        "id": "la_nina_chica",
        "name": "La Niña Chica",
        "prompt": (
            "Character turnaround model sheet, four distinct full-body views side by side: full front view, side profile, 3/4 angle, rear back view. "
            "An angelic young Spanish girl from Moguer named La Niña Chica, wearing a rustic percale dress and white apron. "
            "2D traditional hand-painted watercolor and sepia ink storybook illustration on heavy textured paper grain, soft color washes, "
            "warm Mediterranean sunlight, no 3D, no CGI, no render, isolated on pure white background, vertical 9:16, masterpiece."
        )
    },
    {
        "id": "anilla_la_hungara",
        "name": "Anilla la Húngara",
        "prompt": (
            "Character turnaround model sheet, four distinct full-body views side by side: full front view, side profile, 3/4 angle, rear back view. "
            "An Andalusian flamenco dancer woman named Anilla la Húngara, warm tanned skin, sparkling dark eyes, wavy black hair with comb, "
            "colorful ruffled layered flamenco dress and Manila shawl. "
            "2D traditional hand-painted watercolor and sepia ink storybook illustration on heavy textured paper grain, soft color washes, "
            "warm Mediterranean sunlight, no 3D, no CGI, no render, isolated on pure white background, vertical 9:16, masterpiece."
        )
    }
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Enfriamiento inicial preventivo de 45 segundos para asegurar que el tier gratuito esté listo
print("Iniciando secuencia con cooldown preventivo de 45s...")
time.sleep(45)

for i, item in enumerate(chars_to_generate):
    cid = item["id"]
    prompt = item["prompt"]
    print(f"\n==========================================")
    print(f"[{i+1}/{len(chars_to_generate)}] Generando {item['name']} ({cid})...")
    print(f"==========================================")

    clean_prompt = " ".join(prompt.strip().split()).replace('"', '').replace("'", "")
    encoded = urllib.parse.quote(clean_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=sana&nologo=true"

    success = False
    for attempt in range(4):
        try:
            print(f"Petición a Pollinations (intento {attempt+1})...")
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type", "").startswith("image"):
                temp_jpg = personajes_dir / f"temp_{cid}.jpg"
                final_jpg = personajes_dir / f"{cid}.jpg"
                final_png = personajes_dir / f"{cid}.png"

                with open(temp_jpg, "wb") as f:
                    f.write(r.content)

                crop_and_resize_to_vertical(temp_jpg, final_jpg)
                if temp_jpg.exists():
                    temp_jpg.unlink()

                print(f"Guardado {final_jpg} ({os.path.getsize(final_jpg)} bytes)")
                print("Generando recorte PNG transparente...")
                remove_image_background(final_jpg, final_png)

                # Registrar en proyecto.json
                p = get_project(project_id)
                for char in p.get("personajes", []):
                    if char.get("id") == cid:
                        ts = int(time.time())
                        char["imagen_url"] = f"/proyectos_data/{project_id}/personajes/{cid}.jpg?t={ts}"
                        char["prompt_retrato"] = prompt
                        break
                save_or_update_project(p)
                print(f"Registrado {cid} en proyecto.json con éxito!")
                success = True
                break
            elif r.status_code in (402, 429):
                print(f"Rate limit de Pollinations. Esperando 55s para reintentar...")
                time.sleep(55)
            else:
                print(f"Error HTTP {r.status_code}. Esperando 50s...")
                time.sleep(50)
        except Exception as e:
            print(f"Error en intento {attempt+1}: {e}. Esperando 50s...")
            time.sleep(50)

    if not success:
        print(f"FALLO CRÍTICO: No se pudo generar {cid}.")

    if i < len(chars_to_generate) - 1:
        print("Esperando enfriamiento de 52s para el siguiente personaje...")
        time.sleep(52)

print("\n--- SECUENCIA FINALIZADA ---")
