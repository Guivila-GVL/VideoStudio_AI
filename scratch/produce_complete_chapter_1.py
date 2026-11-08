import os, sys, time, json, urllib.parse, requests
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.image_engine import crop_and_resize_to_vertical
from app.core.tts_engine import synthesize_speech
from app.core.video_renderer import render_final_video
from app.core.project_manager import get_project, save_project_chapter

BASE_DIR = Path("d:/OneDrive/04_Desarrollo_proyectos/2026_Proyecto_Videos")
cap_dir = BASE_DIR / "proyectos/platero_y_yo/capitulos/cap_01_platero"
cap_dir.mkdir(parents=True, exist_ok=True)
media_dir = BASE_DIR / "app/static/media"
media_dir.mkdir(parents=True, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def generate_scene_image(prompt: str, filename: str) -> str:
    final_path = cap_dir / filename
    web_url = f"/proyectos_data/platero_y_yo/capitulos/cap_01_platero/{filename}"
    
    clean = " ".join(prompt.strip().split()).replace('"', '').replace("'", "")
    encoded = urllib.parse.quote(clean)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&model=sana&nologo=true"
    
    print(f"\n[IMAGE] Generando fotograma para {filename}...")
    for attempt in range(4):
        try:
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200 and len(r.content) > 1000 and r.headers.get("content-type", "").startswith("image"):
                temp_p = cap_dir / f"temp_{filename}"
                with open(temp_p, "wb") as f:
                    f.write(r.content)
                crop_and_resize_to_vertical(temp_p, final_path)
                if temp_p.exists():
                    temp_p.unlink()
                print(f"-> Guardado exitoso: {final_path} ({os.path.getsize(final_path)} bytes)")
                return web_url
            elif r.status_code in (402, 429):
                print(f"-> Rate limit (402). Esperando 52s para reintentar...")
                time.sleep(52)
            else:
                print(f"-> HTTP {r.status_code}. Esperando 30s...")
                time.sleep(30)
        except Exception as e:
            print(f"-> Error: {e}. Esperando 30s...")
            time.sleep(30)
    
    return web_url

# 1. Definición canónica de las 3 escenas de Capítulo 1
scene_definitions = [
    {
        "id": 1,
        "narrador": "Platero es pequeño, peludo, suave; tan blando por fuera que se diría todo de algodón. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro.",
        "personajes_en_escena": ["Platero"],
        "escenario_clave": "Las Colinas y el Molino de Viento",
        "duracion_estimada": 7,
        "prompt_imagen": (
            "Platero, small fluffy silver-grey Andalusian donkey with gentle dark crystal black eyes and soft cotton-like coat, "
            "standing on all four legs, grazing in a sunny green meadow filled with pink, blue, and yellow wildflowers. "
            "In the background, rolling golden hills and an iconic whitewashed windmill under a clear Mediterranean sky. "
            "2D traditional storybook watercolor illustration, Studio Ghibli aesthetic, soft translucent washes, "
            "visible textured paper grain, subtle sepia ink outlines, warm golden sunlight, vertical 9:16 portrait composition, "
            "masterpiece, no text, no words, no labels, no title."
        ),
        "image_file": "sc1_platero_colinas.jpg"
    },
    {
        "id": 2,
        "narrador": "Lo llamo dulcemente: «¿Platero?», y viene a mí con un trotecillo alegre que parece que se ríe, en un cascabeleo ideal, a comer uvas moscateles y mandarinas frescas.",
        "personajes_en_escena": ["Platero", "El Poeta"],
        "escenario_clave": "El Pozo Viejo y el Huerto de los Frailes",
        "duracion_estimada": 7,
        "prompt_imagen": (
            "Platero, small fluffy silver-grey donkey, trotting happily towards the young Spanish poet who is kneeling gently with an outstretched hand holding amber grapes, "
            "in a sunlit Andalusian orchard beside an ancient stone well and ivy-covered adobe wall with lush fig trees and green foliage. "
            "2D traditional storybook watercolor illustration, Studio Ghibli aesthetic, soft translucent washes, "
            "visible textured paper grain, subtle sepia ink outlines, warm golden Mediterranean sunlight, vertical 9:16 portrait composition, "
            "masterpiece, no text, no words, no labels."
        ),
        "image_file": "sc2_poeta_platero.jpg"
    },
    {
        "id": 3,
        "narrador": "Los domingos, por las callejas de cal blanca de Moguer, los hombres del campo se quedan mirándolo: «Tiene acero... Acero y plata de luna al mismo tiempo».",
        "personajes_en_escena": ["Platero", "El Poeta"],
        "escenario_clave": "Calles Blancas y Azoteas de Moguer",
        "duracion_estimada": 7,
        "prompt_imagen": (
            "Platero, small fluffy silver-grey donkey, walking proudly down a narrow picturesque cobblestone street of Moguer beside the young Spanish poet wearing a wide-brim hat. "
            "Dazzling whitewashed houses with wrought iron balconies adorned with red geraniums and bougainvillea under a bright cobalt blue sky. "
            "Andalusian villagers watching in the warm background. 2D traditional storybook watercolor illustration, Studio Ghibli aesthetic, "
            "soft translucent washes, visible textured paper grain, subtle sepia ink outlines, warm golden Mediterranean sunlight, "
            "vertical 9:16 portrait composition, masterpiece, no text, no words, no labels."
        ),
        "image_file": "sc3_calles_moguer.jpg"
    }
]

# 2. Generar Fotogramas de Escena (Scene 1 ya existe, generar Scene 2 y Scene 3)
final_scenes = []
for sc_def in scene_definitions:
    fname = sc_def["image_file"]
    fpath = cap_dir / fname
    if fpath.exists() and fpath.stat().st_size > 50000:
        print(f"\n[FOTOGRAMA] Reutilizando fotograma verificado existente: {fname} ({fpath.stat().st_size} bytes)")
        img_url = f"/proyectos_data/platero_y_yo/capitulos/cap_01_platero/{fname}?t={int(time.time())}"
    else:
        # Respetar enfriamiento preventivo de 50s
        print(f"\nEsperando 50s de enfriamiento para generar {fname}...")
        time.sleep(50)
        img_url = generate_scene_image(sc_def["prompt_imagen"], fname)
        img_url += f"?t={int(time.time())}"

    # 3. Generar Audio de Locución (TTS)
    print(f"[TTS] Sintetizando locución de voz para Escena {sc_def['id']}...")
    tts = synthesize_speech(
        text=sc_def["narrador"],
        voice_key="edge_es_alvaro"
    )
    print(f"-> Audio: {tts['url']} ({tts['duration']}s)")

    scene_obj = {
        "id": sc_def["id"],
        "narrador": sc_def["narrador"],
        "prompt_imagen": sc_def["prompt_imagen"],
        "personajes_en_escena": sc_def["personajes_en_escena"],
        "escenario_clave": sc_def["escenario_clave"],
        "duracion_estimada": sc_def["duracion_estimada"],
        "audio_url": tts["url"],
        "image_url": img_url,
        "duracion_real": tts["duration"]
    }
    final_scenes.append(scene_obj)

# 4. Renderizado del Vídeo Vertical Completo con Ken Burns y Subtítulos
print("\n" + "=" * 60)
print("[VIDEO] Renderizando vídeo vertical final 9:16 con FFmpeg...")
print("=" * 60)
video_res = render_final_video(
    scenes=final_scenes,
    project_title="Platero y Yo - Cap 1: Platero",
    enable_subtitles=True,
    enable_ken_burns=True
)

print(f"\n[OK] Vídeo renderizado con éxito:")
print(f"-> URL: {video_res['video_url']}")
print(f"-> Duración: {video_res['duration']}s")
print(f"-> Tamaño: {video_res['size_mb']} MB")

# 5. Guardar capítulo actualizado en proyecto
chapter_data = {
    "id": "cap_01_platero",
    "titulo": "Capítulo 1: Platero",
    "orden": 1,
    "origen_tipo": "capitulo",
    "origen_ref": "Capítulo 1",
    "texto_original": (
        "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. "
        "Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro. "
        "Lo dejo suelto, y se va al prado, y acaricia tibiamente con su hocico, rozándolas apenas, las florecillas rosas, celestes y gualdas... "
        "Lo llamo dulcemente: «¿Platero?», y viene a mí con un trotecillo alegre que parece que se ríe, en no sé qué cascabeleo ideal... "
        "Come cuanto le doy. Le gustan las naranjas mandarina, las uvas moscateles, todas de ámbar, los higos morados, con su cristalina gotita de miel... "
        "Es tierno y mimoso igual que un niño, que una niña...; pero fuerte y seco por dentro, como de piedra. "
        "Cuando paso sobre él, los domingos, por las últimas callejas del pueblo, los hombres del campo, vestidos de limpio y despaciosos, se quedan mirándolo: "
        "—T'iene asero... Tiene acero. Acero y plata de luna, al mismo tiempo."
    ),
    "scenes": final_scenes,
    "video_url": video_res["video_url"],
    "duracion": video_res["duration"]
}

saved = save_project_chapter("platero_y_yo", chapter_data)
print(f"\n[EXITO] Capítulo 1 actualizado y guardado: ID={saved['id']}, Status=Renderizado")
