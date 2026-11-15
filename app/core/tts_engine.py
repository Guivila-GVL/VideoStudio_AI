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

def synthesize_speech(
    text: str,
    voice_key: str = "openai_fable",
    provider: Optional[str] = None,
    custom_voice_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sintetiza audio a partir de texto y guarda el archivo en static/media.
    Devuelve la URL web del archivo y su duración real.
    """
    clean_text = text.strip()
    if not clean_text:
        clean_text = "..."

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

    # 0. Edge-TTS (Microsoft Neural - 100% Castellano Nativo, Calidad de Estudio, Gratuito)
    if provider == "edge" or voice_key.startswith("edge_") or (matched_voice and matched_voice.get("provider") == "edge"):
        voice_id = custom_voice_id or (matched_voice.get("voice_id") if matched_voice else None) or "es-ES-AlvaroNeural"
        pitch = (matched_voice.get("pitch") if matched_voice else None) or "+0Hz"
        rate = (matched_voice.get("rate") if matched_voice else None) or "+0%"
        try:
            import asyncio
            import concurrent.futures
            import edge_tts

            def _run_edge():
                async def _save():
                    comm = edge_tts.Communicate(clean_text, voice_id, pitch=pitch, rate=rate)
                    await comm.save(str(out_path))
                asyncio.run(_save())

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(_run_edge).result()

            if out_path.exists() and out_path.stat().st_size > 0:
                duration = get_audio_duration(str(out_path))
                return {"url": web_url, "duration": duration, "provider": "edge", "file_path": str(out_path)}
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
