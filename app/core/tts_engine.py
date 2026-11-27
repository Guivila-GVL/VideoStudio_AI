import os
import uuid
import subprocess
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

import static_ffmpeg
static_ffmpeg.add_paths()

load_dotenv()

MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

def _edge_es_voice(
    id_: str,
    name: str,
    voice_id: str,
    gender: str,
    region_tag: str,
    description: str,
    age_group: str = "adulto",
    pitch: str = "+0Hz",
    rate: str = "+0%",
    extra_tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    tags = [region_tag, "Español Nativo", "Gratuito"]
    if extra_tags:
        tags.extend(extra_tags)
    return {
        "id": id_,
        "name": name,
        "provider": "edge",
        "voice_id": voice_id,
        "pitch": pitch,
        "rate": rate,
        "gender": gender,
        "age_group": age_group,
        "category": "espanol_nativo",
        "tags": tags,
        "description": description,
    }


DEFAULT_VOICES = [
    # --- Voces Nativas en Español (España Peninsular - 100% Sin Acento Anglosajón) ---
    _edge_es_voice(
        "edge_alvaro_joven",
        "Álvaro Joven (🇪🇸 España - Joven 12-14a)",
        "es-ES-AlvaroNeural",
        "masculino",
        "🇪🇸 España",
        "Voz juvenil masculina modulada a timbre de 12-14 años con pronunciación nativa castellana. Ideal para narradores sensibles, niños o adolescentes.",
        age_group="joven",
        pitch="+12Hz",
        rate="-3%",
        extra_tags=["Joven 12-14a", "Lírico"],
    ),
    _edge_es_voice(
        "edge_alvaro",
        "Álvaro (🇪🇸 España - Castellano Estándar)",
        "es-ES-AlvaroNeural",
        "masculino",
        "🇪🇸 España",
        "Narrador adulto en español de España neutro, dicción impecable y calidez literaria para cuentos y documentales.",
        extra_tags=["Adulto", "Claro"],
    ),
    _edge_es_voice(
        "edge_alvaro_grave",
        "Álvaro Grave (🇪🇸 España - Narrador Literario)",
        "es-ES-AlvaroNeural",
        "masculino",
        "🇪🇸 España",
        "Versión más grave y pausada de Álvaro en español de España, pensada para narración literaria clásica y reflexiva.",
        age_group="maduro",
        pitch="-10Hz",
        rate="-5%",
        extra_tags=["Grave", "Literario"],
    ),
    _edge_es_voice(
        "edge_elvira",
        "Elvira (🇪🇸 España - Femenina Cálida)",
        "es-ES-ElviraNeural",
        "femenino",
        "🇪🇸 España",
        "Voz femenina con acento de España, envolvente, dulce y expresiva para literatura infantil y relatos nostálgicos.",
        extra_tags=["Femenina", "Cálida"],
    ),
    _edge_es_voice(
        "edge_elvira_suave",
        "Elvira Suave (🇪🇸 España - Poética y Pausada)",
        "es-ES-ElviraNeural",
        "femenino",
        "🇪🇸 España",
        "Variante más suave y pausada de Elvira en español de España para cuentos íntimos y poéticos.",
        pitch="+6Hz",
        rate="-5%",
        extra_tags=["Femenina", "Poética"],
    ),
    _edge_es_voice(
        "edge_ximena",
        "Ximena (🇪🇸 España - Joven Dinámica)",
        "es-ES-XimenaNeural",
        "femenino",
        "🇪🇸 España",
        "Voz femenina juvenil y ágil para historias dinámicas y diálogos frescos en español de España.",
        age_group="joven",
        extra_tags=["Femenina", "Joven"],
    ),
    {
        "id": "eleven_ZtGDHPi9jPEEuRGCBOY5",
        "name": "Narración Clásica ES (ElevenLabs - Cuenta Personal)",
        "provider": "elevenlabs",
        "voice_id": "ZtGDHPi9jPEEuRGCBOY5",
        "gender": "masculino",
        "age_group": "adulto",
        "category": "espanol_nativo",
        "tags": ["🇪🇸 Español", "Narrador", "ElevenLabs Personal"],
        "description": "Voz personalizada en tu cuenta de ElevenLabs en idioma español."
    },
    # --- Fallback Gratuito ---
    {
        "id": "gtts_es",
        "name": "Español Estándar (Fallback Sintético - gTTS)",
        "provider": "gtts",
        "voice_id": "es",
        "gender": "neutro",
        "age_group": "adulto",
        "category": "gratuito",
        "tags": ["Gratuito", "Sin API Key", "Sintético"],
        "description": "Voz sintética estándar de Google Translate para pruebas sin coste ni cuota de API."
    }
]

def get_audio_duration(file_path: str) -> float:
    """Calcula la duración precisa de un archivo de audio usando ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return round(float(res.stdout.strip()), 2)
    except Exception as e:
        print(f"[TTS] Error obteniendo duración de audio con ffprobe: {e}")
        return 5.0

def list_voices() -> List[Dict[str, Any]]:
    """Devuelve la lista completa de voces estructurada y categorizada."""
    voices = list(DEFAULT_VOICES)
    eleven_key = os.getenv("ELEVENLABS_API_KEY")
    if eleven_key:
        try:
            r = requests.get(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": eleven_key},
                timeout=5
            )
            if r.status_code == 200:
                user_voices = r.json().get("voices", [])
                api_voices = []
                for v in user_voices:
                    # Evitar duplicar las que ya están en DEFAULT_VOICES
                    vid = v.get("voice_id", "")
                    if any(existing.get("voice_id") == vid for existing in DEFAULT_VOICES):
                        continue
                    cat = v.get("category", "")
                    # Omitir voces premade en inglés de ElevenLabs
                    if cat == "premade":
                        continue
                    labels = v.get("labels", {})
                    lang = (labels.get("language") or "").strip().lower()
                    if lang and lang not in ("es", "spanish", "español"):
                        continue
                    gender = labels.get("gender", "neutro")
                    age = labels.get("age", "adulto")
                    api_voices.append({
                        "id": f"eleven_{vid}",
                        "name": f"{v['name']} (ElevenLabs - {v.get('category', 'Custom')})",
                        "provider": "elevenlabs",
                        "voice_id": vid,
                        "gender": gender,
                        "age_group": age,
                        "category": "elevenlabs_custom",
                        "tags": [gender.capitalize(), age.capitalize(), "ElevenLabs"],
                        "description": v.get("description") or f"Voz personalizada de ElevenLabs: {v['name']}"
                    })
                if api_voices:
                    voices = api_voices + voices
        except Exception:
            pass
    return voices

def _normalize_text_for_tts(text: str) -> str:
    """Normaliza saltos de línea de PDF/libro y guiones para una lectura fluida de audiolibro."""
    import re
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not t:
        return "..."
    # Párrafos dobles o títulos seguidos de salto -> pausa de punto si no termina en puntuación
    lines = [ln.strip() for ln in t.split("\n")]
    merged: List[str] = []
    for idx, ln in enumerate(lines):
        if not ln:
            if merged and not merged[-1].endswith((".", "!", "?", "…", ":")):
                merged[-1] = merged[-1] + "."
            continue
        # Si la primera línea es un título corto sin punto (ej. "Mariposas blancas")
        if idx == 0 and len(ln) <= 45 and not ln.endswith((".", "!", "?", "…", ":", ",")) and len(lines) > 1:
            merged.append(ln + ".")
        else:
            merged.append(ln)
    t = " ".join(merged)
    # Limpiar guiones de diálogo al inicio de intervención para evitar pausas bruscas
    t = re.sub(r"\s*—\s*", ", ", t).lstrip(", ")
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t or "..."


def synthesize_speech(
    text: str,
    voice_key: str = "edge_alvaro",
    provider: Optional[str] = None,
    custom_voice_id: Optional[str] = None,
    expressive: bool = True,
    dialogue_voice_map: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Sintetiza audio a partir de texto y guarda el archivo en static/media.
    Devuelve la URL web del archivo, su duración real y timestamps exactos por frase y palabra.
    Por defecto en producción (expressive=True) aplica el patrón adoptado de Skill #87
    ChrisChen667788/wind-comic (services/tts.service.ts):
      1) Modulación emocional por frase (velocidad / tono dinámicos).
      2) Voz diferenciada para narrador y personajes en diálogos.
      3) Timestamps exactos por frase (`sentences`) y palabra (`words`) para subtítulos.
    """
    clean_text = _normalize_text_for_tts(text)

    filename = f"audio_{uuid.uuid4().hex[:10]}.mp3"
    out_path = MEDIA_DIR / filename
    web_url = f"/static/media/{filename}"

    # Resolver coincidencia en catálogo
    matched_voice = next((v for v in DEFAULT_VOICES if v["id"] == voice_key or v.get("voice_id") == voice_key), None)
    if matched_voice:
        if not provider:
            provider = matched_voice["provider"]
        if not custom_voice_id:
            custom_voice_id = matched_voice["voice_id"]

    # Identificar proveedor si sigue sin definir
    if not provider:
        if voice_key.startswith("edge_"):
            provider = "edge"
        elif voice_key.startswith("eleven_"):
            provider = "elevenlabs"
        elif voice_key.startswith("openai_"):
            provider = "openai"
        else:
            provider = "gtts"

    # 0. Edge-TTS (Microsoft Neural - 100% Castellano Nativo + Patrón expresivo wind-comic en producción)
    if provider == "edge" or voice_key.startswith("edge_") or (matched_voice and matched_voice.get("provider") == "edge"):
        if expressive:
            try:
                expr_res = synthesize_expressive_speech(
                    text=text,
                    narrator_voice=voice_key,
                    dialogue_voice_map=dialogue_voice_map,
                    output_path=out_path,
                )
                if out_path.exists() and out_path.stat().st_size > 0:
                    return {
                        "url": web_url,
                        "duration": expr_res["duration"],
                        "provider": "edge",
                        "engine_mode": "edge_wind_comic_expressive",
                        "file_path": str(out_path),
                        "sentences": expr_res.get("sentences", []),
                        "words": expr_res.get("words", []),
                        "sentences_json_path": expr_res.get("sentences_json_path"),
                        "words_json_path": expr_res.get("words_json_path"),
                    }
            except Exception as e:
                print(f"[TTS] Edge-TTS expresivo (wind-comic) excepción, aplicando fallback plano: {e}")

        voice_id = custom_voice_id or (matched_voice.get("voice_id") if matched_voice else None) or "es-ES-AlvaroNeural"
        pitch = (matched_voice.get("pitch") if matched_voice else None) or "+0Hz"
        rate = (matched_voice.get("rate") if matched_voice else None) or "+0%"
        try:
            import asyncio
            import concurrent.futures
            import edge_tts

            def _run_edge():
                async def _save():
                    comm = edge_tts.Communicate(
                        clean_text,
                        voice_id,
                        pitch=pitch,
                        rate=rate,
                        boundary="WordBoundary",
                    )
                    word_timings = []
                    with open(out_path, "wb") as audio_file:
                        async for chunk in comm.stream():
                            ctype = chunk.get("type")
                            if ctype == "audio":
                                audio_file.write(chunk["data"])
                            elif ctype == "WordBoundary":
                                word_timings.append({
                                    "word": chunk.get("text", ""),
                                    "start": round(chunk.get("offset", 0) / 10_000_000, 3),
                                    "duration": round(chunk.get("duration", 0) / 10_000_000, 3),
                                })
                    return word_timings
                return asyncio.run(_save())

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                word_timings = pool.submit(_run_edge).result()

            if out_path.exists() and out_path.stat().st_size > 0:
                import json as _json
                duration = get_audio_duration(str(out_path))
                if word_timings:
                    words_path = out_path.with_suffix(".words.json")
                    words_path.write_text(_json.dumps(word_timings, ensure_ascii=False), encoding="utf-8")
                sentence_timings = [{
                    "index": 1,
                    "speaker": "narrador",
                    "is_dialogue": False,
                    "voice_key": voice_key,
                    "voice_id": voice_id,
                    "emotion": "neutral",
                    "pitch": pitch,
                    "rate": rate,
                    "text": clean_text,
                    "start": 0.0,
                    "end": duration,
                    "duration": duration,
                    "words_count": len(word_timings),
                }]
                sentences_path = out_path.with_suffix(".sentences.json")
                sentences_path.write_text(_json.dumps(sentence_timings, ensure_ascii=False, indent=2), encoding="utf-8")
                return {
                    "url": web_url,
                    "duration": duration,
                    "provider": "edge",
                    "engine_mode": "edge_flat",
                    "file_path": str(out_path),
                    "sentences": sentence_timings,
                    "words": word_timings,
                    "sentences_json_path": str(sentences_path),
                }
            else:
                print(f"[TTS] Edge-TTS no generó el archivo de audio.")
        except Exception as e:
            print(f"[TTS] Edge-TTS excepción: {e}")

    eleven_key = os.getenv("ELEVENLABS_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # 1. ElevenLabs
    if provider == "elevenlabs" and eleven_key:
        voice_id = custom_voice_id or voice_key.replace("eleven_", "")
        if voice_id == "george":
            voice_id = "JBFqnCBsd6RMkjVDRZzb"
        elif voice_id == "charlie":
            voice_id = "IKne3meq5aSn9XLyUdCD"
        elif voice_id == "sarah":
            voice_id = "EXAVITQu4vr4xnSDxMaL"
        elif voice_id == "liam":
            voice_id = "TX3LPaxmHKxFdv7VOQHJ"
        elif voice_id == "will":
            voice_id = "bIHbv24MWmeRgasZH58o"

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": eleven_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=25)
            if resp.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(resp.content)
                duration = get_audio_duration(str(out_path))
                return {"url": web_url, "duration": duration, "provider": "elevenlabs", "file_path": str(out_path)}
            else:
                print(f"[TTS] ElevenLabs error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[TTS] ElevenLabs excepción: {e}")

    # 2. OpenAI TTS
    if provider == "openai" and openai_key and openai_key.startswith("sk-"):
        voice_id = custom_voice_id or voice_key.replace("openai_", "")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice_id,
                input=clean_text
            )
            response.stream_to_file(out_path)
            duration = get_audio_duration(str(out_path))
            return {"url": web_url, "duration": duration, "provider": "openai", "file_path": str(out_path)}
        except Exception as e:
            print(f"[TTS] OpenAI TTS excepción: {e}")

    # 3. Fallback: gTTS (gratuito y fiable)
    try:
        from gtts import gTTS
        tts = gTTS(text=clean_text, lang="es", slow=False)
        tts.save(str(out_path))
        duration = get_audio_duration(str(out_path))
        return {"url": web_url, "duration": duration, "provider": "gtts", "file_path": str(out_path)}
    except Exception as e:
        print(f"[TTS] gTTS excepción: {e}")
        raise RuntimeError(f"No fue posible sintetizar el audio: {e}")


# ==============================================================================
# ADAPTACIÓN SKILL #87: ChrisChen667788/wind-comic (patrón services/tts.service.ts)
# Paso 5: Locución neuronal y narración de audio (Opt-in / Sin romper producción)
#   1) Modulación emocional por frase (velocidad / tono dinámicos)
#   2) Voz diferenciada para narrador y personajes en diálogos
#   3) Timestamps exactos por frase y palabra para subtítulos sincronizados
# ==============================================================================

EMOTION_PROSODY_MAP: Dict[str, Dict[str, Any]] = {
    "neutral":      {"pitch_delta_hz": 0,   "rate_delta_pct": 0,   "pause_after_ms": 260, "label": "Narración neutra"},
    "lyrical":      {"pitch_delta_hz": -3,  "rate_delta_pct": -7,  "pause_after_ms": 380, "label": "Lírico / contemplativo"},
    "joyful":       {"pitch_delta_hz": +8,  "rate_delta_pct": +6,  "pause_after_ms": 240, "label": "Alegre / entusiasta"},
    "tender":       {"pitch_delta_hz": +4,  "rate_delta_pct": -9,  "pause_after_ms": 360, "label": "Tierno / íntimo"},
    "question":     {"pitch_delta_hz": +10, "rate_delta_pct": -4,  "pause_after_ms": 340, "label": "Pregunta / curiosidad"},
    "urgent":       {"pitch_delta_hz": +6,  "rate_delta_pct": +10, "pause_after_ms": 200, "label": "Exclamación / urgencia"},
    "melancholic":  {"pitch_delta_hz": -6,  "rate_delta_pct": -11, "pause_after_ms": 420, "label": "Melancólico / susurro"},
}

DEFAULT_SPEAKER_VOICE_MAP: Dict[str, str] = {
    "narrator": "edge_alvaro",
    "narrador": "edge_alvaro",
    "protagonista_joven": "edge_alvaro_joven",
    "character_female": "edge_elvira",
    "character_young_female": "edge_ximena",
    "character_male_elder": "edge_alvaro_grave",
    "character_default": "edge_elvira",
}


def _parse_hz(pitch_str: str) -> int:
    import re
    m = re.search(r"([+-]?\d+)", str(pitch_str or "+0Hz"))
    return int(m.group(1)) if m else 0


def _parse_pct(rate_str: str) -> int:
    import re
    m = re.search(r"([+-]?\d+)", str(rate_str or "+0%"))
    return int(m.group(1)) if m else 0


def _combine_prosody(base_pitch: str, base_rate: str, emotion: str) -> Dict[str, str]:
    emo = EMOTION_PROSODY_MAP.get(emotion, EMOTION_PROSODY_MAP["neutral"])
    final_hz = max(-30, min(35, _parse_hz(base_pitch) + int(emo["pitch_delta_hz"])))
    final_pct = max(-35, min(35, _parse_pct(base_rate) + int(emo["rate_delta_pct"])))
    return {
        "pitch": f"{final_hz:+d}Hz",
        "rate": f"{final_pct:+d}%",
        "pause_after_ms": emo["pause_after_ms"],
    }


def detect_sentence_emotion(sentence: str, is_dialogue: bool = False) -> str:
    """Infiere la emoción dominante de una frase literaria en español para modular pitch/rate."""
    s = (sentence or "").strip()
    s_low = s.lower()

    if "¿" in s or s.endswith("?"):
        return "question"
    if any(w in s_low for w in ("llor", "triste", "sombra", "pena", "silencio", "oscuro", "lejos", "adiós", "noche")):
        return "melancholic"
    if any(w in s_low for w in ("suave", "algodón", "acarici", "blando", "pequeño", "tierno", "dulce", "mim", "dorm")):
        return "tender"
    if "¡" in s or s.endswith("!"):
        if any(w in s_low for w in ("mira", "corre", "vamos", "ven", "rápido", "cuidado")):
            return "urgent"
        return "joyful"
    if any(w in s_low for w in ("mariposa", "sol", "luz", "cristal", "risa", "alegr", "rosa", "oro", "jugar", "cielo")):
        return "joyful" if is_dialogue else "lyrical"
    if "…" in s or "..." in s or ";" in s:
        return "lyrical"
    return "neutral"


def parse_expressive_script(
    text: str,
    narrator_voice: str = "edge_alvaro",
    dialogue_voice_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Segmenta un texto literario en frases siguiendo el patrón de services/tts.service.ts (wind-comic):
    - Separa intervenciones de diálogo (con raya —, guion largo o comillas «») del narrador.
    - Detecta incisos del narrador dentro de un diálogo (ej. «—¡Mira, Platero! —le dije sonriendo—. ¡Qué hermosas!»).
    - Asigna voz por hablante y emoción por frase.
    """
    import re

    voice_map = dict(DEFAULT_SPEAKER_VOICE_MAP)
    voice_map["narrator"] = narrator_voice
    voice_map["narrador"] = narrator_voice
    if dialogue_voice_map:
        voice_map.update(dialogue_voice_map)

    default_dialogue_voice = voice_map.get("character_default", "edge_elvira")
    if default_dialogue_voice == narrator_voice:
        default_dialogue_voice = "edge_elvira" if narrator_voice != "edge_elvira" else "edge_alvaro_joven"

    raw_lines = [ln.strip() for ln in (text or "").replace("\r\n", "\n").split("\n") if ln.strip()]
    segments: List[Dict[str, Any]] = []
    dialogue_turn = 0

    for line in raw_lines:
        # Etiqueta explícita tipo [Personaje: emoción] Texto
        explicit_match = re.match(r"^\[(?P<speaker>[^:\]]+)(?::\s*(?P<emotion>[^\]]+))?\]\s*(?P<content>.+)$", line)
        if explicit_match:
            spk = explicit_match.group("speaker").strip().lower()
            emo = (explicit_match.group("emotion") or "").strip().lower()
            content = explicit_match.group("content").strip()
            is_diag = spk not in ("narrador", "narrator")
            v_key = voice_map.get(spk, default_dialogue_voice if is_diag else narrator_voice)
            for sent in re.split(r"(?<=[.!?…])\s+", content):
                sent = sent.strip()
                if not sent:
                    continue
                chosen_emo = emo if emo in EMOTION_PROSODY_MAP else detect_sentence_emotion(sent, is_dialogue=is_diag)
                segments.append({
                    "speaker": spk,
                    "is_dialogue": is_diag,
                    "voice_key": v_key,
                    "emotion": chosen_emo,
                    "text": sent,
                })
            continue

        # Detectar línea con raya de diálogo española (—)
        if line.startswith(("—", "-", "«", "\"")):
            dialogue_turn += 1
            # Alternar entre voces de personajes si hay varios turnos de diálogo
            alt_voices = [
                voice_map.get("character_default", default_dialogue_voice),
                voice_map.get("protagonista_joven", "edge_alvaro_joven"),
                voice_map.get("character_young_female", "edge_ximena"),
            ]
            alt_voices = [v for v in alt_voices if v != narrator_voice] or [default_dialogue_voice]
            current_char_voice = alt_voices[(dialogue_turn - 1) % len(alt_voices)]

            # Si contiene incisos del narrador entre rayas: —Texto diálogo —inciso narrador—. Más diálogo
            parts = re.split(r"\s*—\s*", line)
            parts = [p.strip() for p in parts if p.strip()]
            for p_idx, part in enumerate(parts):
                # En español, tras la primera raya (p_idx=0 -> diálogo), el segundo bloque suele ser inciso si empieza en minúscula con verbo dicendi
                is_narrator_aside = (
                    p_idx % 2 == 1
                    and bool(re.match(r"^(le\s+|me\s+|se\s+|dijo|dij[eo]|pregunt[oó]|exclam[oó]|susurr[oó]|respondi[oó]|añadi[oó]|grit[oó]|murmur[oó])", part.lower()))
                )
                spk = "narrador" if is_narrator_aside else f"personaje_{dialogue_turn}"
                is_diag = not is_narrator_aside
                v_key = narrator_voice if is_narrator_aside else current_char_voice
                clean_part = part.lstrip(". ,;").strip()
                if not clean_part:
                    continue
                if not clean_part.endswith((".", "!", "?", "…", ":")):
                    clean_part += "."
                for sent in re.split(r"(?<=[.!?…])\s+", clean_part):
                    sent = sent.strip()
                    if not sent:
                        continue
                    segments.append({
                        "speaker": spk,
                        "is_dialogue": is_diag,
                        "voice_key": v_key,
                        "emotion": detect_sentence_emotion(sent, is_dialogue=is_diag),
                        "text": sent,
                    })
        else:
            # Narración pura: dividir por frases para modular cada oración según su emoción
            for sent in re.split(r"(?<=[.!?…;])\s+", line):
                sent = sent.strip()
                if not sent:
                    continue
                if not sent.endswith((".", "!", "?", "…", ";", ":")):
                    sent += "."
                segments.append({
                    "speaker": "narrador",
                    "is_dialogue": False,
                    "voice_key": narrator_voice,
                    "emotion": detect_sentence_emotion(sent, is_dialogue=False),
                    "text": sent,
                })

    return segments


def synthesize_expressive_speech(
    text: str,
    narrator_voice: str = "edge_alvaro",
    dialogue_voice_map: Optional[Dict[str, str]] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Adaptación del patrón services/tts.service.ts de Skill #87 (ChrisChen667788/wind-comic).
    1) Modula velocidad y tono por frase según análisis emocional.
    2) Diferencia voz de narrador y voces de personajes en diálogos.
    3) Devuelve timestamps exactos por frase (`sentences`) y por palabra (`words`) para subtítulos.
    Mantiene intacto `synthesize_speech` para compatibilidad 100% con producción.
    """
    import asyncio
    import concurrent.futures
    import json as _json
    import tempfile
    import edge_tts

    segments = parse_expressive_script(
        text=text,
        narrator_voice=narrator_voice,
        dialogue_voice_map=dialogue_voice_map,
    )
    if not segments:
        segments = [{
            "speaker": "narrador",
            "is_dialogue": False,
            "voice_key": narrator_voice,
            "emotion": "neutral",
            "text": _normalize_text_for_tts(text),
        }]

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        filename = out_path.name
    else:
        filename = f"audio_expr_{uuid.uuid4().hex[:10]}.mp3"
        out_path = MEDIA_DIR / filename

    web_url = f"/static/media/{filename}"

    temp_dir = Path(tempfile.mkdtemp(prefix="videostudio_windcomic_tts_"))
    segment_files: List[Path] = []
    sentence_timings: List[Dict[str, Any]] = []
    all_word_timings: List[Dict[str, Any]] = []
    current_offset_sec = 0.0

    def _synth_segment_edge(seg_text: str, voice_id: str, pitch: str, rate: str, seg_out: Path):
        async def _save_seg():
            comm = edge_tts.Communicate(
                seg_text,
                voice_id,
                pitch=pitch,
                rate=rate,
                boundary="WordBoundary",
            )
            words = []
            with open(seg_out, "wb") as f:
                async for chunk in comm.stream():
                    ctype = chunk.get("type")
                    if ctype == "audio":
                        f.write(chunk["data"])
                    elif ctype == "WordBoundary":
                        words.append({
                            "word": chunk.get("text", ""),
                            "start": round(chunk.get("offset", 0) / 10_000_000, 3),
                            "duration": round(chunk.get("duration", 0) / 10_000_000, 3),
                        })
            return words
        return asyncio.run(_save_seg())

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        for idx, seg in enumerate(segments):
            v_key = seg["voice_key"]
            matched_v = next((v for v in DEFAULT_VOICES if v["id"] == v_key or v.get("voice_id") == v_key), None)
            voice_id = (matched_v.get("voice_id") if matched_v else None) or "es-ES-AlvaroNeural"
            base_pitch = (matched_v.get("pitch") if matched_v else None) or "+0Hz"
            base_rate = (matched_v.get("rate") if matched_v else None) or "+0%"

            prosody = _combine_prosody(base_pitch, base_rate, seg["emotion"])
            seg_file = temp_dir / f"seg_{idx:03d}.mp3"
            clean_seg_text = _normalize_text_for_tts(seg["text"])

            words = pool.submit(
                _synth_segment_edge,
                clean_seg_text,
                voice_id,
                prosody["pitch"],
                prosody["rate"],
                seg_file,
            ).result()

            seg_dur = get_audio_duration(str(seg_file)) if seg_file.exists() else 0.0
            segment_files.append(seg_file)

            # Desplazar word timings al reloj global del audio ensamblado
            shifted_words = []
            for w in words:
                sw = {
                    "word": w["word"],
                    "start": round(current_offset_sec + w["start"], 3),
                    "duration": w["duration"],
                    "speaker": seg["speaker"],
                    "emotion": seg["emotion"],
                }
                shifted_words.append(sw)
                all_word_timings.append(sw)

            start_sec = round(current_offset_sec, 3)
            end_sec = round(current_offset_sec + seg_dur, 3)
            sentence_timings.append({
                "index": idx + 1,
                "speaker": seg["speaker"],
                "is_dialogue": seg["is_dialogue"],
                "voice_key": v_key,
                "voice_id": voice_id,
                "emotion": seg["emotion"],
                "pitch": prosody["pitch"],
                "rate": prosody["rate"],
                "text": seg["text"],
                "start": start_sec,
                "end": end_sec,
                "duration": round(seg_dur, 3),
                "words_count": len(shifted_words),
            })

            # Generar silencio breve natural entre frases (pausa dramática según emoción)
            pause_sec = round(int(prosody["pause_after_ms"]) / 1000.0, 3)
            silence_file = temp_dir / f"sil_{idx:03d}.mp3"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", str(pause_sec), "-q:a", "9", "-acodec", "libmp3lame",
                    str(silence_file),
                ],
                capture_output=True,
                check=False,
            )
            if silence_file.exists() and silence_file.stat().st_size > 0:
                segment_files.append(silence_file)
                current_offset_sec += seg_dur + pause_sec
            else:
                current_offset_sec += seg_dur

    # Concatenar todos los segmentos y silencios en el MP3 final con recodificación limpia
    concat_list_path = temp_dir / "concat_list.txt"
    concat_lines = [f"file '{p.as_posix()}'" for p in segment_files if p.exists()]
    concat_list_path.write_text("\n".join(concat_lines), encoding="utf-8")

    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path),
            "-ar", "24000", "-ac", "1", "-b:a", "128k",
            str(out_path),
        ],
        capture_output=True,
        check=True,
    )

    # Guardar metadatos de timestamps por frase y palabra junto al audio
    words_path = out_path.with_suffix(".words.json")
    words_path.write_text(_json.dumps(all_word_timings, ensure_ascii=False, indent=2), encoding="utf-8")

    sentences_path = out_path.with_suffix(".sentences.json")
    sentences_path.write_text(_json.dumps(sentence_timings, ensure_ascii=False, indent=2), encoding="utf-8")

    # Limpieza de temporales
    for p in temp_dir.glob("*"):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    total_duration = get_audio_duration(str(out_path))
    return {
        "url": web_url,
        "duration": total_duration,
        "provider": "edge_wind_comic_expressive",
        "file_path": str(out_path),
        "sentences": sentence_timings,
        "words": all_word_timings,
        "sentences_json_path": str(sentences_path),
        "words_json_path": str(words_path),
    }

