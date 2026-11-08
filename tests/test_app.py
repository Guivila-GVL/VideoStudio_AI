import os
import sys
from pathlib import Path

# Añadir directorio raíz del proyecto al sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_full_pipeline():
    print("=== TEST 1: Guion y Storyboard ===")
    from app.core.script_generator import breakdown_storyboard
    scenes = breakdown_storyboard(
        text="En una colina solitaria, un faro antiguo comenzó a emitir destellos de luz dorada. El viento traía susurros de barcos perdidos.",
        character_desc="Lucas, joven vigía de 25 años con impermeable amarillo y linterna",
        style_key="cinematic",
        target_scenes=2
    )
    print(f"Escenas generadas: {len(scenes)}")
    assert len(scenes) >= 1
    sc0 = scenes[0]
    print(f"Escena 1 Narrador: {sc0['narrador'][:50]}...")
    print(f"Escena 1 Prompt: {sc0['prompt_imagen'][:50]}...")

    print("\n=== TEST 2: Síntesis de Voz (TTS) ===")
    from app.core.tts_engine import synthesize_speech
    tts_res = synthesize_speech("Luz dorada en la colina", voice_key="gtts_es")
    print(f"Audio URL: {tts_res['url']}, Duración: {tts_res['duration']}s")
    assert tts_res["duration"] > 0
    scenes[0]["audio_url"] = tts_res["url"]

    # Sintetizar audio para escena 2 si existe
    if len(scenes) > 1:
        tts_res2 = synthesize_speech("El viento traía susurros", voice_key="gtts_es")
        scenes[1]["audio_url"] = tts_res2["url"]

    print("\n=== TEST 3: Generación de Imagen (FLUX) ===")
    from app.core.image_engine import generate_image
    img_res = generate_image("lighthouse on a hill with golden light, vertical 9:16 portrait", provider="flux")
    print(f"Imagen URL: {img_res['url']}")
    assert img_res["url"]
    scenes[0]["image_url"] = img_res["url"]

    if len(scenes) > 1:
        scenes[1]["image_url"] = img_res["url"]

    print("\n=== TEST 4: Renderizado de Vídeo Final (FFmpeg Ken Burns + Subtítulos) ===")
    from app.core.video_renderer import render_final_video
    video_res = render_final_video(
        scenes=scenes[:2],
        project_title="Test Video",
        enable_subtitles=True,
        enable_ken_burns=True
    )
    print(f"Vídeo renderizado con éxito:")
    print(f"- URL: {video_res['video_url']}")
    print(f"- Duración: {video_res['duration']}s")
    print(f"- Tamaño: {video_res['size_mb']} MB")
    print("\n[EXITO] Todos los componentes del pipeline funcionan al 100%!")

if __name__ == "__main__":
    test_full_pipeline()
