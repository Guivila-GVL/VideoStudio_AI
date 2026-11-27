"""
Prueba A/B aislada en scratch/ — Tarea #208 (Propuesta #P1 del Gestor de Skills)
Skill candidata: #87 ChrisChen667788/wind-comic (patrón services/tts.service.ts)
Paso estricto: Paso 5: Locución neuronal y narración de audio

Genera dos archivos MP3 en scratch/ sobre el mismo fragmento literario (~20 segundos)
con diálogo y cambios emocionales de 'Platero y yo':
  1. scratch/audio_ANTES_actual.mp3      -> Motor actual (synthesize_speech: 1 sola voz fija y tono plano)
  2. scratch/audio_DESPUES_adaptado.mp3  -> Motor adaptado wind-comic (synthesize_expressive_speech:
                                            modulación emocional por frase + voces diferenciadas narrador/diálogo
                                            + timestamps exactos por frase en audio_DESPUES_adaptado.sentences.json)
"""
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.tts_engine import (
    get_audio_duration,
    synthesize_expressive_speech,
    synthesize_speech,
)

FRAGMENTO_LITERARIO_20S = (
    "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón.\n"
    "—¡Mira, Platero! —le dijo la niña sonriendo en el prado—. ¿Ves esas mariposas blancas entre las flores?\n"
    "El burrito alzó despacio las orejas bajo la sombra triste del crepúsculo.\n"
    "—¡Ven aquí, pequeño amigo, vamos a correr hacia la luz del arroyo!"
)


def run_ab_test() -> dict:
    scratch_dir = PROJECT_ROOT / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    antes_path = scratch_dir / "audio_ANTES_actual.mp3"
    despues_path = scratch_dir / "audio_DESPUES_adaptado.mp3"

    print("=== 1. Generando audio ANTES (implementación actual plana, 1 sola voz) ===")
    res_antes = synthesize_speech(
        text=FRAGMENTO_LITERARIO_20S,
        voice_key="edge_alvaro",
    )
    shutil.copyfile(res_antes["file_path"], antes_path)
    if Path(res_antes["file_path"]).with_suffix(".words.json").exists():
        shutil.copyfile(
            Path(res_antes["file_path"]).with_suffix(".words.json"),
            antes_path.with_suffix(".words.json"),
        )
    dur_antes = get_audio_duration(str(antes_path))
    print(f"[OK] ANTES guardado en: {antes_path} ({dur_antes}s, {antes_path.stat().st_size} bytes)")

    print("\n=== 2. Generando audio DESPUÉS (adaptación wind-comic services/tts.service.ts) ===")
    res_despues = synthesize_expressive_speech(
        text=FRAGMENTO_LITERARIO_20S,
        narrator_voice="edge_alvaro",
        dialogue_voice_map={
            "character_default": "edge_elvira",
            "protagonista_joven": "edge_alvaro_joven",
        },
        output_path=despues_path,
    )
    dur_despues = get_audio_duration(str(despues_path))
    print(f"[OK] DESPUÉS guardado en: {despues_path} ({dur_despues}s, {despues_path.stat().st_size} bytes)")

    print("\n=== 3. Desglose de frases, voces, emociones y timestamps (DESPUÉS) ===")
    for s in res_despues["sentences"]:
        print(
            f"  [Frase #{s['index']} | {s['start']:05.2f}s -> {s['end']:05.2f}s] "
            f"Hablante={s['speaker']} | Voz={s['voice_key']} | Emoción={s['emotion']} "
            f"(pitch={s['pitch']}, rate={s['rate']}) -> {s['text']}"
        )

    report = {
        "fragmento": FRAGMENTO_LITERARIO_20S,
        "antes": {
            "file_path": str(antes_path),
            "size_bytes": antes_path.stat().st_size,
            "duration_sec": dur_antes,
            "voices_used": ["edge_alvaro (única voz fija)"],
            "emotions_modulated": ["ninguna (+0Hz, +0% plano)"],
            "sentence_timestamps": False,
        },
        "despues": {
            "file_path": str(despues_path),
            "size_bytes": despues_path.stat().st_size,
            "duration_sec": dur_despues,
            "voices_used": sorted(list({s["voice_key"] for s in res_despues["sentences"]})),
            "emotions_modulated": [
                f"#{s['index']} {s['emotion']} ({s['pitch']}, {s['rate']})"
                for s in res_despues["sentences"]
            ],
            "sentence_timestamps_file": res_despues["sentences_json_path"],
            "word_timestamps_file": res_despues["words_json_path"],
            "sentences": res_despues["sentences"],
        },
    }

    report_path = scratch_dir / "comparativa_AB_wind_comic_tts.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Reporte comparativo guardado en: {report_path}")
    return report


if __name__ == "__main__":
    run_ab_test()
