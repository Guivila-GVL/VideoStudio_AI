import os
import math
import time
import uuid
import base64
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from app.core.image_engine import _build_fal_image_input
from app.core.video_renderer import resolve_media_path

MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

FAL_VIDEO_MODELS = {
    "draft_free": "local/ffmpeg-directed-motion",
    "kling_v21_pro": "fal-ai/kling-video/v2.1/pro/image-to-video",
    "kling_v25_pro": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    "hailuo_02_pro": "fal-ai/minimax/hailuo-02/pro/image-to-video",
    "kling_v21": "fal-ai/kling-video/v2.1/standard/image-to-video",
    "kling_v16": "fal-ai/kling-video/v1.6/standard/image-to-video",
    "wan_i2v": "fal-ai/wan/v2.2-a14b/image-to-video",
}


def _generate_draft_motion_clip(
    image_url: str,
    prompt: str,
    target_duration_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Genera un clip MP4 animado de borrador (100% gratuito, 0€) mediante FFmpeg local,
    dirigiendo el movimiento de cámara y encuadre según la acción física descrita en la escena.
    """
    local_img = resolve_media_path(image_url)
    if not local_img.exists():
        raise FileNotFoundError(f"No se encontró la imagen de la escena para animar en borrador: {image_url}")

    dur = max(5.0, min(28.0, float(target_duration_sec or 10.0)))
    fps = 25
    total_frames = max(125, int(round(dur * fps)))
    p_low = (prompt or "").lower()

    # Seleccionar coreografía de cámara según la acción descrita en la escena
    if any(k in p_low for k in ("sube", "asciend", "vuelan", "mariposa", "cielo", "torre", "ascend", "butterfl", "sky", "upward")):
        # Travelling vertical ascendente acompañando el vuelo o subida por el camino
        z_expr = "min(1.04+0.0005*on,1.18)"
        x_expr = "iw/2-(iw/zoom/2)+sin(on/28)*14"
        y_expr = f"(ih-ih/zoom)*(1-on/{total_frames})"
    elif any(k in p_low for k in ("baja", "amedrenta", "retrocede", "pincho", "casucha", "guarda", "steps back", "down")):
        # Acercamiento dramático con leve tensión lateral
        z_expr = "min(1.0+0.0007*on,1.22)"
        x_expr = "iw/2-(iw/zoom/2)+sin(on/15)*18"
        y_expr = "ih/2-(ih/zoom/2)"
    elif any(k in p_low for k in ("camina", "avanza", "trote", "paseo", "sendero", "calleja", "walk", "trot", "path")):
        # Travelling lateral de seguimiento de caminata
        z_expr = "1.15"
        x_expr = f"(iw-iw/zoom)*(on/{total_frames})"
        y_expr = "ih/2-(ih/zoom/2)+sin(on/12)*10"
    else:
        # Push-in cinematográfico suave de cuento
        z_expr = "min(1.0+0.0006*on,1.18)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    filename = f"anim_draft_{uuid.uuid4().hex[:10]}.mp4"
    out_path = MEDIA_DIR / filename
    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s=1080x1920:fps={fps}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(local_img.resolve()),
        "-vf", vf,
        "-t", f"{dur:.2f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", "-crf", "20",
        str(out_path.resolve()),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    size_mb = round(out_path.stat().st_size / (1024 * 1024), 2)
    return {
        "video_clip_url": f"/static/media/{filename}",
        "provider": "local/ffmpeg-directed-motion (Borrador 0€)",
        "duration": round(dur, 1),
        "segments": 1,
        "linked_next": False,
        "size_mb": size_mb,
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


def _submit_and_poll_fal_queue(model_id: str, payload: Dict[str, Any], fal_key: str, timeout_sec: int = 480) -> Dict[str, Any]:
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


def _extract_last_frame_data_uri(video_path: Path) -> str:
    """Extrae el último fotograma de un MP4 como data URI JPEG para encadenar otro segmento hacia adelante."""
    tmp_jpg = video_path.with_suffix(".last.jpg")
    try:
        cmd = [
            "ffmpeg", "-y", "-sseof", "-0.12", "-i", str(video_path),
            "-frames:v", "1", "-q:v", "2", str(tmp_jpg),
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        b64 = base64.b64encode(tmp_jpg.read_bytes()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    finally:
        if tmp_jpg.exists():
            tmp_jpg.unlink()


def _concat_mp4_segments(segment_paths: List[Path], out_path: Path) -> None:
    """Concatena segmentos MP4 secuenciales en un único vídeo continuo sin cortes ni rebobinados."""
    cmd = ["ffmpeg", "-y"]
    for sp in segment_paths:
        cmd.extend(["-i", str(sp)])
    inputs_tag = "".join(f"[{i}:v]" for i in range(len(segment_paths)))
    cmd.extend([
        "-filter_complex", f"{inputs_tag}concat=n={len(segment_paths)}:v=1:a=0[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18",
        str(out_path),
    ])
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def animate_scene_image(
    prompt: str,
    image_url: str,
    next_image_url: Optional[str] = None,
    transition_text: str = "",
    duration: str = "5",
    aspect_ratio: str = "9:16",
    model_key: str = "kling_v21_pro",
    target_duration_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Convierte una imagen de escena en un clip MP4 animado (Image-to-Video) mediante Fal.ai.
    Si target_duration_sec supera 15.5s, encadena múltiples clips de 10s hacia adelante
    extrayendo el último fotograma de cada segmento para evitar rebobinados (ping-pong).
    Si se proporciona next_image_url, enlaza el último segmento con el fotograma inicial de la escena siguiente.
    """
    if model_key in ("draft_free", "draft", "free"):
        return _generate_draft_motion_clip(
            image_url=image_url,
            prompt=prompt,
            target_duration_sec=target_duration_sec,
        )

    fal_key = os.getenv("FAL_KEY", "").strip()
    if not fal_key:
        raise ValueError("FAL_KEY no está configurada en .env. Configúrala en Ajustes (⚙️) para animar escenas.")

    model_id = FAL_VIDEO_MODELS.get(model_key, FAL_VIDEO_MODELS["kling_v21_pro"])
    start_uri = _to_fal_data_uri(image_url)

    action_prompt = (prompt or "").strip()
    if transition_text:
        action_prompt = f"{action_prompt}. Smooth continuous transition: {transition_text.strip()}".strip(". ")
    if not action_prompt:
        action_prompt = "Gentle natural character movement, blinking, soft breeze in hair and foliage, warm cinematic storybook motion"
    action_prompt = (
        f"{action_prompt}. Anatomically accurate limbs, natural gait, smooth steady camera, no extra legs, no morphing distortion"
    )[:900]

    chosen_dur = str(duration if str(duration) in ("5", "10") else "5")
    num_segments = 1
    if target_duration_sec is not None:
        t_dur = float(target_duration_sec)
        if t_dur > 6.5:
            chosen_dur = "10"
        if t_dur > 15.5:
            # Cada segmento de 10s cubre cómodamente hasta ~13.5s sin deformar el ritmo
            num_segments = max(2, min(4, math.ceil(t_dur / 13.5)))

    aspect = aspect_ratio if aspect_ratio in ("9:16", "16:9", "1:1") else "9:16"
    segment_paths: List[Path] = []
    cur_start_uri = start_uri
    linked_next = False

    try:
        for seg_idx in range(num_segments):
            is_last = seg_idx == num_segments - 1
            payload: Dict[str, Any] = {
                "prompt": action_prompt,
                "image_url": cur_start_uri,
                "duration": chosen_dur,
                "aspect_ratio": aspect,
            }
            seg_linked = False
            if is_last and next_image_url:
                try:
                    payload["tail_image_url"] = _to_fal_data_uri(next_image_url)
                    seg_linked = True
                except Exception as e:
                    print(f"[I2V] No se pudo cargar next_image_url ({next_image_url}): {e}")

            try:
                result = _submit_and_poll_fal_queue(model_id, payload, fal_key)
            except Exception as first_err:
                if seg_linked and "tail_image_url" in payload:
                    print(f"[I2V] Reintentando sin tail_image_url tras error: {first_err}")
                    payload.pop("tail_image_url", None)
                    seg_linked = False
                    result = _submit_and_poll_fal_queue(model_id, payload, fal_key)
                else:
                    raise

            if is_last:
                linked_next = seg_linked

            video_info = result.get("video") or {}
            video_url_remote = video_info.get("url")
            if not video_url_remote:
                raise RuntimeError(f"Fal.ai ({model_id}) no devolvió URL de vídeo: {result}")

            dl = requests.get(video_url_remote, timeout=90)
            if dl.status_code != 200:
                raise RuntimeError(f"Error descargando vídeo generado HTTP {dl.status_code}")

            seg_path = MEDIA_DIR / f"_tmp_seg_{uuid.uuid4().hex[:8]}_{seg_idx}.mp4"
            seg_path.write_bytes(dl.content)
            segment_paths.append(seg_path)

            if not is_last:
                cur_start_uri = _extract_last_frame_data_uri(seg_path)

        filename = f"anim_{uuid.uuid4().hex[:10]}.mp4"
        out_path = MEDIA_DIR / filename
        if len(segment_paths) == 1:
            segment_paths[0].replace(out_path)
        else:
            _concat_mp4_segments(segment_paths, out_path)

        size_mb = round(out_path.stat().st_size / (1024 * 1024), 2)
        return {
            "video_clip_url": f"/static/media/{filename}",
            "provider": model_id,
            "duration": int(chosen_dur) * num_segments,
            "segments": num_segments,
            "linked_next": linked_next,
            "size_mb": size_mb,
        }
    finally:
        for sp in segment_paths:
            if sp.exists():
                try:
                    sp.unlink()
                except Exception:
                    pass
