import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from app.core.image_engine import _build_fal_image_input
from app.core.video_renderer import resolve_media_path

MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

FAL_VIDEO_MODELS = {
    "kling_v16": "fal-ai/kling-video/v1.6/standard/image-to-video",
    "kling_v21": "fal-ai/kling-video/v2.1/standard/image-to-video",
    "wan_i2v": "fal-ai/wan/v2.2-a14b/image-to-video",
}


def _to_fal_data_uri(image_url: str) -> str:
    """Convierte una URL local (/static/media/... o /proyectos_data/...) a data URI base64 para Fal.ai."""
    local_path = resolve_media_path(image_url)
    data_uri = _build_fal_image_input({
        "exists": local_path.exists(),
        "local_path": str(local_path),
        "reference_url": image_url,
    })
    if data_uri:
        return data_uri
    raise FileNotFoundError(f"No se pudo cargar la imagen local para animar: {image_url}")


def _submit_and_poll_fal_queue(model_id: str, payload: Dict[str, Any], fal_key: str, timeout_sec: int = 240) -> Dict[str, Any]:
    """Envía una tarea a queue.fal.run y espera su resultado."""
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    submit_url = f"https://queue.fal.run/{model_id}"
    resp = requests.post(submit_url, headers=headers, json=payload, timeout=45)
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(f"Error enviando a Fal.ai ({model_id}) HTTP {resp.status_code}: {resp.text[:350]}")

    qdata = resp.json()
    if "video" in qdata:
        return qdata

    status_url = qdata.get("status_url")
    response_url = qdata.get("response_url")
    if not status_url or not response_url:
        raise RuntimeError(f"Respuesta inesperada de cola Fal.ai ({model_id}): {qdata}")

    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        st_resp = requests.get(status_url, headers={"Authorization": f"Key {fal_key}"}, timeout=20)
        if st_resp.status_code == 200:
            st = st_resp.json()
            state = st.get("status")
            if state == "COMPLETED":
                res_resp = requests.get(response_url, headers={"Authorization": f"Key {fal_key}"}, timeout=30)
                if res_resp.status_code != 200:
                    raise RuntimeError(f"Error leyendo resultado Fal.ai HTTP {res_resp.status_code}: {res_resp.text[:300]}")
                return res_resp.json()
            if state in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"Fal.ai ({model_id}) falló en cola: {st}")
        time.sleep(3)

    raise TimeoutError(f"Tiempo agotado ({timeout_sec}s) esperando vídeo animado en {model_id}")


def animate_scene_image(
    prompt: str,
    image_url: str,
    next_image_url: Optional[str] = None,
    transition_text: str = "",
    duration: str = "5",
    aspect_ratio: str = "9:16",
    model_key: str = "kling_v16",
    target_duration_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convierte una imagen de escena en un clip MP4 animado (Image-to-Video) mediante Fal.ai.
    Si se proporciona next_image_url, intenta enlazar fotograma inicial -> fotograma final.
    """
    fal_key = os.getenv("FAL_KEY", "").strip()
    if not fal_key:
        raise ValueError("FAL_KEY no está configurada en .env. Configúrala en Ajustes (⚙️) para animar escenas.")

    model_id = FAL_VIDEO_MODELS.get(model_key, FAL_VIDEO_MODELS["kling_v16"])
    start_uri = _to_fal_data_uri(image_url)

    action_prompt = (prompt or "").strip()
    if transition_text:
        action_prompt = f"{action_prompt}. Smooth continuous transition: {transition_text.strip()}".strip(". ")
    if not action_prompt:
        action_prompt = "Gentle natural character movement, blinking, soft breeze in hair and foliage, warm cinematic storybook motion"

    # Limitar longitud del prompt para modelos de vídeo
    action_prompt = action_prompt[:900]

    # Elegir automáticamente 10s si la locución de la escena supera 6.5s
    chosen_dur = str(duration if str(duration) in ("5", "10") else "5")
    if target_duration_sec is not None and float(target_duration_sec) > 6.5:
        chosen_dur = "10"

    payload: Dict[str, Any] = {
        "prompt": action_prompt,
        "image_url": start_uri,
        "duration": chosen_dur,
        "aspect_ratio": aspect_ratio if aspect_ratio in ("9:16", "16:9", "1:1") else "9:16",
    }

    linked_next = False
    if next_image_url:
        try:
            payload["tail_image_url"] = _to_fal_data_uri(next_image_url)
            linked_next = True
        except Exception as e:
            print(f"[I2V] No se pudo cargar next_image_url ({next_image_url}): {e}")

    try:
        result = _submit_and_poll_fal_queue(model_id, payload, fal_key)
    except Exception as first_err:
        if linked_next and "tail_image_url" in payload:
            # Reintentar sin tail_image_url si el modelo concreto no soporta last-frame
            print(f"[I2V] Reintentando sin tail_image_url tras error: {first_err}")
            payload.pop("tail_image_url", None)
            linked_next = False
            result = _submit_and_poll_fal_queue(model_id, payload, fal_key)
        else:
            raise

    video_info = result.get("video") or {}
    video_url_remote = video_info.get("url")
    if not video_url_remote:
        raise RuntimeError(f"Fal.ai ({model_id}) no devolvió URL de vídeo: {result}")

    dl = requests.get(video_url_remote, timeout=90)
    if dl.status_code != 200:
        raise RuntimeError(f"Error descargando vídeo generado HTTP {dl.status_code}")

    filename = f"anim_{uuid.uuid4().hex[:10]}.mp4"
    out_path = MEDIA_DIR / filename
    out_path.write_bytes(dl.content)

    return {
        "video_clip_url": f"/static/media/{filename}",
        "provider": model_id,
        "duration": int(payload["duration"]),
        "linked_next": linked_next,
        "size_mb": round(len(dl.content) / (1024 * 1024), 2),
    }
