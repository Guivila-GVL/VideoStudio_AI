import os
import uuid
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

import static_ffmpeg
static_ffmpeg.add_paths()

MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
PROYECTOS_DIR = Path(__file__).resolve().parent.parent.parent / "proyectos"

TARGET_W = 1080
TARGET_H = 1920
FPS = 25

def resolve_media_path(url_or_path: str) -> Path:
    """Resuelve URLs /static/media/... o /proyectos_data/... a rutas físicas válidas en disco."""
    clean = str(url_or_path).split("?")[0].strip()
    if clean.startswith("/static/media/"):
        return MEDIA_DIR / clean.replace("/static/media/", "")
    elif clean.startswith("/proyectos_data/"):
        return PROYECTOS_DIR / clean.replace("/proyectos_data/", "")
    elif (MEDIA_DIR / Path(clean).name).exists():
        return MEDIA_DIR / Path(clean).name
    p = Path(clean)
    if p.exists():
        return p
    return MEDIA_DIR / p.name

def get_audio_duration_seconds(audio_path: str) -> float:
    """Obtiene la duración exacta del audio con ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return max(1.5, round(float(res.stdout.strip()), 2))
    except Exception:
        return 4.0

def create_subtitle_overlay(
    text: str,
    output_path: Path,
    width: int = TARGET_W,
    height: int = TARGET_H
):
    """
    Crea una imagen PNG transparente con subtítulos centrados y
    diseño moderno con tarjeta oscura translúcida y tipografía de alto contraste.
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Intentar cargar una fuente atractiva o usar la por defecto
    font = None
    font_size = 42
    font_names = [
        "arialbd.ttf", "arial.ttf", "segoeui.ttf", "segoeuib.ttf",
        "calibri.ttf", "calibrib.ttf", "DejaVuSans.ttf"
    ]
    for fn in font_names:
        try:
            font = ImageFont.truetype(fn, font_size)
            break
        except Exception:
            continue
    if not font:
        font = ImageFont.load_default()

    clean_text = text.strip()
    if not clean_text:
        overlay.save(output_path, "PNG")
        return

    # Ajustar saltos de línea para que quepa en la pantalla vertical
    wrapped_lines = textwrap.wrap(clean_text, width=32)
    line_spacing = 14

    # Calcular dimensiones del texto
    total_text_h = 0
    max_line_w = 0
    line_bboxes = []
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        line_bboxes.append((w, h))
        max_line_w = max(max_line_w, w)
        total_text_h += h + line_spacing

    total_text_h -= line_spacing

    # Posicionar en el tercio inferior (zona estándar de Shorts/Reels para evitar botones de interfaz)
    padding_x = 40
    padding_y = 26
    box_w = max_line_w + (padding_x * 2)
    box_h = total_text_h + (padding_y * 2)

    box_x1 = (width - box_w) // 2
    box_y1 = height - 420 - box_h
    box_x2 = box_x1 + box_w
    box_y2 = box_y1 + box_h

    # Dibujar tarjeta translúcida con bordes redondeados
    draw.rounded_rectangle(
        [box_x1, box_y1, box_x2, box_y2],
        radius=20,
        fill=(12, 16, 24, 215),
        outline=(255, 255, 255, 40),
        width=2
    )

    # Dibujar texto centrado con sombra suave
    current_y = box_y1 + padding_y
    for i, line in enumerate(wrapped_lines):
        w, h = line_bboxes[i]
        line_x = (width - w) // 2
        # Sombra
        draw.text((line_x + 2, current_y + 2), line, font=font, fill=(0, 0, 0, 200))
        # Texto principal blanco puro
        draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255, 255))
        current_y += h + line_spacing

    overlay.save(output_path, "PNG")

def render_scene_clip(
    image_path: Path,
    audio_path: Path,
    output_clip_path: Path,
    scene_index: int,
    narrador_text: str,
    enable_subtitles: bool = True,
    enable_ken_burns: bool = True
) -> float:
    """
    Renderiza un clip individual sincronizado con su locución,
    aplicando movimiento dinámico de cámara y subtítulos.
    """
    duration = get_audio_duration_seconds(str(audio_path))
    total_frames = int(duration * FPS) + 1

    temp_overlay_path = output_clip_path.parent / f"temp_sub_{output_clip_path.stem}.png"

    # Seleccionar variación de movimiento (Ken Burns)
    if enable_ken_burns:
        motion_idx = scene_index % 3
        if motion_idx == 0:
            # Zoom In suave hacia el centro
            zoom_expr = f"min(zoom+0.0012,1.15)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif motion_idx == 1:
            # Zoom Out suave
            zoom_expr = f"max(1.15-0.0012*on,1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            # Paneo suave con ligero zoom constante
            zoom_expr = "1.10"
            x_expr = "((iw-iw/zoom)/2)+sin(on/25)*20"
            y_expr = "ih/2-(ih/zoom/2)"
        vf_zoom = f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={TARGET_W}x{TARGET_H}:fps={FPS}"
    else:
        vf_zoom = f"scale={TARGET_W}:{TARGET_H},fps={FPS}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
    ]

    if enable_subtitles and narrador_text.strip():
        create_subtitle_overlay(narrador_text, temp_overlay_path)
        cmd.extend([
            "-loop", "1", "-i", str(temp_overlay_path),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{vf_zoom}[vz];[vz][1:v]overlay=0:0:shortest=1[vfinal]",
            "-map", "[vfinal]",
            "-map", "2:a"
        ])
    else:
        cmd.extend([
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{vf_zoom}[vfinal]",
            "-map", "[vfinal]",
            "-map", "1:a"
        ])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-af", "volume=1.5",
        "-t", str(duration),
        "-shortest",
        str(output_clip_path)
    ])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    finally:
        if temp_overlay_path.exists():
            temp_overlay_path.unlink()

    return duration

def render_final_video(
    scenes: List[Dict[str, Any]],
    project_title: str = "Video Short",
    enable_subtitles: bool = True,
    enable_ken_burns: bool = True,
    project_id: Optional[str] = None,
    chapter_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Renderiza todos los clips de las escenas y los concatena en el archivo
    final vertical MP4 listo para descargar o publicar, ubicándolo
    en la carpeta dedicada del proyecto correspondiente.
    """
    if not scenes:
        raise ValueError("No hay escenas para renderizar.")

    render_id = uuid.uuid4().hex[:8]
    temp_dir = MEDIA_DIR / f"render_{render_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    total_duration = 0.0

    try:
        # 1. Renderizar cada escena por separado
        for i, sc in enumerate(scenes):
            img_url = sc.get("image_url")
            audio_url = sc.get("audio_url")

            if not img_url or not audio_url:
                raise ValueError(f"La escena {i+1} no tiene imagen o audio generado aún.")

            img_path = resolve_media_path(img_url)
            audio_path = resolve_media_path(audio_url)

            if not img_path.exists() or not audio_path.exists():
                raise FileNotFoundError(f"Archivos de media no encontrados para escena {i+1} (img: {img_path}, audio: {audio_path}).")

            clip_path = temp_dir / f"clip_{i:02d}.mp4"
            dur = render_scene_clip(
                image_path=img_path,
                audio_path=audio_path,
                output_clip_path=clip_path,
                scene_index=i,
                narrador_text=sc.get("narrador", ""),
                enable_subtitles=enable_subtitles,
                enable_ken_burns=enable_ken_burns
            )
            total_duration += dur
            clip_paths.append(clip_path)

        # 2. Archivo de lista para el demuxer concat de FFmpeg
        concat_list_file = temp_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in clip_paths:
                # Usar formato compatible con FFmpeg en Windows
                normalized_path = str(p.resolve()).replace("\\", "/")
                f.write(f"file '{normalized_path}'\n")

        # 3. Concatenar clips en el MP4 definitivo en MEDIA_DIR
        temp_final_filename = f"video_short_{render_id}.mp4"
        temp_final_path = MEDIA_DIR / temp_final_filename

        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(temp_final_path)
        ]
        subprocess.run(concat_cmd, capture_output=True, text=True, check=True)

        file_size_bytes = temp_final_path.stat().st_size
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        # Generar miniatura del primer frame
        thumb_filename = f"thumb_{render_id}.jpg"
        thumb_path = MEDIA_DIR / thumb_filename
        thumb_cmd = [
            "ffmpeg", "-y",
            "-ss", "00:00:01",
            "-i", str(temp_final_path),
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path)
        ]
        subprocess.run(thumb_cmd, capture_output=True)

        # 4. Organización por Proyecto si se especifica project_id
        final_video_url = f"/static/media/{temp_final_filename}"
        final_thumb_url = f"/static/media/{thumb_filename}" if thumb_path.exists() else None
        target_path_str = str(temp_final_path)

        if project_id:
            proj_dir = PROYECTOS_DIR / project_id
            if proj_dir.exists():
                proj_videos_dir = proj_dir / "videos"
                proj_videos_dir.mkdir(parents=True, exist_ok=True)

                if chapter_id:
                    clean_name = f"{chapter_id}.mp4"
                else:
                    clean_name = f"video_{render_id}.mp4"

                project_video_file = proj_videos_dir / clean_name
                shutil.copy2(str(temp_final_path), str(project_video_file))
                target_path_str = str(project_video_file)

                # Miniatura en carpeta de vídeos del proyecto
                proj_thumb_file = proj_videos_dir / f"{project_video_file.stem}_thumb.jpg"
                if thumb_path.exists():
                    shutil.copy2(str(thumb_path), str(proj_thumb_file))
                    final_thumb_url = f"/proyectos_data/{project_id}/videos/{proj_thumb_file.name}"

                # Copiar también dentro de la subcarpeta del capítulo si existe
                if chapter_id:
                    cap_dir = proj_dir / "capitulos" / chapter_id
                    if cap_dir.exists():
                        shutil.copy2(str(temp_final_path), str(cap_dir / "video_final.mp4"))

                final_video_url = f"/proyectos_data/{project_id}/videos/{project_video_file.name}"

        return {
            "video_url": final_video_url,
            "thumbnail_url": final_thumb_url,
            "duration": round(total_duration, 2),
            "size_mb": file_size_mb,
            "scenes_count": len(scenes),
            "filename": Path(target_path_str).name,
            "storage_path": target_path_str,
            "project_id": project_id,
            "chapter_id": chapter_id
        }

    finally:
        # Limpieza de archivos temporales de clips intermedios
        try:
            for p in clip_paths:
                if p.exists():
                    p.unlink()
            concat_list = temp_dir / "concat_list.txt"
            if concat_list.exists():
                concat_list.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
        except Exception:
            pass
