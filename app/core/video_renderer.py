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


DEFAULT_SUBTITLE_CONFIG: Dict[str, Any] = {
    "mode": "word_by_word",
    "bg_mode": "transparent",
    "font_family": "sans",
    "font_size": 52,
    "text_color": "#FFFFFF",
    "highlight_color": "#FBBF24",
    "position": "bottom",
    "fade": "fade",
}

_FONT_MAP = {
    "sans": "Arial",
    "serif": "Georgia",
    "mono": "Consolas",
}


def _hex_to_ass_color(hex_color: str, alpha_hex: str = "00") -> str:
    """Convierte #RRGGBB a formato ASS &HAABBGGRR."""
    c = (hex_color or "#FFFFFF").strip().lstrip("#")
    if len(c) != 6:
        c = "FFFFFF"
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alpha_hex}{b}{g}{r}".upper()


def _format_ass_time(seconds: float) -> str:
    """Formatea segundos a H:MM:SS.cc para archivos ASS."""
    s = max(0.0, seconds)
    hrs = int(s // 3600)
    mins = int((s % 3600) // 60)
    secs = s % 60
    return f"{hrs}:{mins:02d}:{secs:05.2f}"


def _escape_ass_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _norm_token(w: str) -> str:
    return re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ]", "", (w or "").lower())


def _align_timings_with_punctuation(raw_text: str, timings: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    """
    Edge-TTS WordBoundary devuelve palabras sin puntuación (sin puntos, comas ni signos).
    Esta función alinea los tokens originales de raw_text (con toda su puntuación)
    sobre los timestamps reales de timings.
    """
    orig_tokens = [w for w in (raw_text or "").strip().split() if w]
    if not orig_tokens or not timings:
        return timings

    aligned: List[Dict[str, Any]] = []
    t_idx = 0
    n_t = len(timings)

    for tok in orig_tokens:
        norm_o = _norm_token(tok)
        matched = None
        if norm_o:
            for look in range(t_idx, min(n_t, t_idx + 5)):
                if _norm_token(timings[look].get("word", "")) == norm_o:
                    matched = timings[look]
                    t_idx = look + 1
                    break
        if matched is not None:
            aligned.append({
                "word": tok,
                "start": float(matched.get("start", 0.0)),
                "duration": float(matched.get("duration", 0.25)),
            })
        else:
            # Si es puntuación suelta (ej. "—") o palabra compuesta, heredar/interpolar tiempo cercano
            prev_end = (aligned[-1]["start"] + aligned[-1]["duration"]) if aligned else 0.0
            next_start = float(timings[t_idx]["start"]) if t_idx < n_t else duration
            est_start = min(prev_end, next_start)
            est_dur = max(0.08, min(0.35, next_start - est_start))
            aligned.append({"word": tok, "start": round(est_start, 3), "duration": round(est_dur, 3)})

    return aligned


def _load_or_estimate_word_timings(audio_path: Path, text: str, duration: float) -> List[Dict[str, Any]]:
    """Carga marcas de tiempo exactas de Edge-TTS (.words.json) restaurando puntuación, o las estima."""
    import json as _json
    words_file = audio_path.with_suffix(".words.json")
    if words_file.exists():
        try:
            data = _json.loads(words_file.read_text(encoding="utf-8"))
            if isinstance(data, list) and len(data) > 0:
                return _align_timings_with_punctuation(text, data, duration)
        except Exception:
            pass

    raw_words = [w for w in text.strip().split() if w]
    if not raw_words:
        return []
    usable_dur = max(0.5, duration - 0.1)
    weights = [max(2, len(w)) for w in raw_words]
    total_w = sum(weights)
    t = 0.05
    estimated = []
    for w, wt in zip(raw_words, weights):
        w_dur = (wt / total_w) * usable_dur
        estimated.append({"word": w, "start": round(t, 3), "duration": round(w_dur, 3)})
        t += w_dur
    return estimated


def _group_words_into_phrases(words: List[Dict[str, Any]], max_words: int = 4, max_chars: int = 24) -> List[List[Dict[str, Any]]]:
    phrases: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    cur_chars = 0
    for w in words:
        txt = w.get("word", "")
        if current and (len(current) >= max_words or cur_chars + len(txt) + 1 > max_chars):
            phrases.append(current)
            current = [w]
            cur_chars = len(txt)
        else:
            current.append(w)
            cur_chars += len(txt) + (1 if current else 0)
    if current:
        phrases.append(current)
    return phrases


def _group_words_into_paragraphs(words: List[Dict[str, Any]], max_words: int = 22, max_chars: int = 135) -> List[List[Dict[str, Any]]]:
    """Agrupa palabras por frases completas (cerrando siempre en punto/signo final) y acotando frases muy largas."""
    paragraphs: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    cur_chars = 0
    for w in words:
        txt = w.get("word", "")
        if current and (len(current) >= max_words or cur_chars + len(txt) + 1 > max_chars):
            paragraphs.append(current)
            current = [w]
            cur_chars = len(txt)
        else:
            current.append(w)
            cur_chars += len(txt) + (1 if len(current) > 1 else 0)

        stripped_end = txt.rstrip("»\"'”)")
        if current and stripped_end.endswith((".", "!", "?", "…")):
            paragraphs.append(current)
            current = []
            cur_chars = 0
        elif current and len(current) >= 10 and cur_chars >= 65 and stripped_end.endswith((";", ":")):
            paragraphs.append(current)
            current = []
            cur_chars = 0
    if current:
        paragraphs.append(current)
    return paragraphs


def _format_phrase_multiline(words: List[Dict[str, Any]], active_idx: int, hi_ass_col: str, primary_ass_tag: str, limit: Optional[int] = None, dim_past: bool = False, max_line_chars: int = 30) -> str:
    """Formatea una frase en múltiples líneas limpias resaltando la palabra activa."""
    items = words[:limit] if limit is not None else words
    lines: List[str] = []
    cur_line: List[str] = []
    cur_len = 0
    for j, pw in enumerate(items):
        raw_w = pw.get("word", "")
        txt = _escape_ass_text(raw_w)
        if j == active_idx:
            tag = f"{{\\c{hi_ass_col}}}{txt}{{\\c{primary_ass_tag}}}"
        elif dim_past and j < active_idx:
            tag = f"{{\\alpha&H55&}}{txt}{{\\alpha&H00&}}"
        else:
            tag = txt
        if cur_line and cur_len + len(raw_w) + 1 > max_line_chars:
            lines.append(" ".join(cur_line))
            cur_line = [tag]
            cur_len = len(raw_w)
        else:
            cur_line.append(tag)
            cur_len += len(raw_w) + (1 if cur_line else 0)
    if cur_line:
        lines.append(" ".join(cur_line))
    return "\\N".join(lines)


def create_ass_subtitles(
    text: str,
    audio_path: Path,
    duration: float,
    output_ass_path: Path,
    subtitle_config: Optional[Dict[str, Any]] = None,
    target_w: int = TARGET_W,
    target_h: int = TARGET_H,
) -> None:
    """Genera un archivo .ass con tipografía, fondo, posición y sincronización palabra a palabra."""
    cfg = {**DEFAULT_SUBTITLE_CONFIG, **(subtitle_config or {})}
    bg_mode = cfg.get("bg_mode", "transparent")
    mode = cfg.get("mode", "word_by_word")
    font_name = _FONT_MAP.get(cfg.get("font_family", "sans"), "Arial")
    font_size = int(cfg.get("font_size") or 52)
    text_hex = cfg.get("text_color") or "#FFFFFF"
    hi_hex = cfg.get("highlight_color") or "#FBBF24"
    position = cfg.get("position", "bottom")
    use_fade = cfg.get("fade", "fade") == "fade"

    # Evitar texto blanco invisible sobre fondo blanco
    if bg_mode == "white" and text_hex.strip().upper() == "#FFFFFF":
        text_hex = "#111827"

    primary_col = _hex_to_ass_color(text_hex, "00")
    hi_ass_col = _hex_to_ass_color(hi_hex, "00")
    primary_ass_tag = _hex_to_ass_color(text_hex, "00")

    if bg_mode == "white":
        border_style = 3
        outline_px = 18
        shadow_px = 0
        outline_col = _hex_to_ass_color("#FFFFFF", "12")
        back_col = _hex_to_ass_color("#FFFFFF", "12")
    elif bg_mode == "dark":
        border_style = 3
        outline_px = 18
        shadow_px = 0
        outline_col = _hex_to_ass_color("#0C1018", "38")
        back_col = _hex_to_ass_color("#0C1018", "38")
    else:  # transparent
        border_style = 1
        outline_px = 4
        shadow_px = 2
        outline_col = _hex_to_ass_color("#000000", "25")
        back_col = _hex_to_ass_color("#000000", "80")

    is_horizontal = target_w > target_h
    if position == "top":
        alignment = 8
        margin_v = 90 if is_horizontal else 220
    elif position == "center":
        alignment = 5
        margin_v = 0
    else:
        alignment = 2
        margin_v = 110 if is_horizontal else 380

    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {target_w}\n"
        f"PlayResY: {target_h}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{font_name},{font_size},{primary_col},{hi_ass_col},{outline_col},{back_col},"
        f"-1,0,0,0,100,100,0,0,{border_style},{outline_px},{shadow_px},{alignment},60,60,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events: List[str] = []
    clean_text = text.strip()
    if not clean_text:
        output_ass_path.write_text(header, encoding="utf-8")
        return

    words = _load_or_estimate_word_timings(audio_path, clean_text, duration)

    if mode == "block" or not words:
        wrapped = "\\N".join(textwrap.wrap(clean_text, width=32))
        fad = "{\\fad(150,220)}" if use_fade else ""
        events.append(f"Dialogue: 0,{_format_ass_time(0)},{_format_ass_time(duration)},Default,,0,0,0,,{fad}{_escape_ass_text(wrapped)}")
    elif mode == "paragraph_preview":
        # Frase completa actual + siguiente frase difuminada debajo (estilo teleprompter/lectura)
        paragraphs = _group_words_into_paragraphs(words, max_words=22, max_chars=135)
        next_font_size = max(24, int(round(font_size * 0.84)))
        for p_idx, para in enumerate(paragraphs):
            p_end = paragraphs[p_idx + 1][0]["start"] if p_idx + 1 < len(paragraphs) else duration
            next_block = ""
            if p_idx + 1 < len(paragraphs):
                next_raw = " ".join(nw.get("word", "") for nw in paragraphs[p_idx + 1])
                next_wrapped = "\\N".join(textwrap.wrap(next_raw, width=36))
                next_block = (
                    f"\\N\\N{{\\fs{next_font_size}\\alpha&H9A&\\blur1.2}}"
                    f"{_escape_ass_text(next_wrapped)}"
                    f"{{\\blur0\\alpha&H00&\\fs{font_size}}}"
                )
            for w_idx, w in enumerate(para):
                w_start = w["start"]
                w_end = para[w_idx + 1]["start"] if w_idx + 1 < len(para) else p_end
                if w_end <= w_start:
                    w_end = w_start + max(0.15, w.get("duration", 0.25))
                cur_body = _format_phrase_multiline(
                    para, w_idx, hi_ass_col, primary_ass_tag,
                    dim_past=True, max_line_chars=34
                )
                fad = "{\\fad(120,0)}" if (use_fade and w_idx == 0) else ("{\\fad(0,180)}" if (use_fade and w_idx == len(para) - 1) else "")
                events.append(f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},Default,,0,0,0,,{fad}{cur_body}{next_block}")
    elif mode in ("scrolling_sentence", "karaoke_chunk"):
        # Frases largas (2-3 líneas completas) señalando la palabra/frase activa
        phrases = _group_words_into_phrases(words, max_words=14, max_chars=72)
        dim_past = mode == "scrolling_sentence"
        for p_idx, phrase in enumerate(phrases):
            p_end = phrases[p_idx + 1][0]["start"] if p_idx + 1 < len(phrases) else duration
            for w_idx, w in enumerate(phrase):
                w_start = w["start"]
                w_end = phrase[w_idx + 1]["start"] if w_idx + 1 < len(phrase) else p_end
                if w_end <= w_start:
                    w_end = w_start + max(0.15, w.get("duration", 0.25))
                body = _format_phrase_multiline(
                    phrase, w_idx, hi_ass_col, primary_ass_tag,
                    dim_past=dim_past, max_line_chars=30
                )
                fad = "{\\fad(100,0)}" if (use_fade and w_idx == 0) else ("{\\fad(0,180)}" if (use_fade and w_idx == len(phrase) - 1) else "")
                events.append(f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},Default,,0,0,0,,{fad}{body}")
    else:  # word_by_word: aparece palabra a palabra acumulando hasta 2 líneas
        phrases = _group_words_into_phrases(words, max_words=10, max_chars=52)
        for p_idx, phrase in enumerate(phrases):
            p_end = phrases[p_idx + 1][0]["start"] if p_idx + 1 < len(phrases) else duration
            for w_idx, w in enumerate(phrase):
                w_start = w["start"]
                w_end = phrase[w_idx + 1]["start"] if w_idx + 1 < len(phrase) else p_end
                if w_end <= w_start:
                    w_end = w_start + max(0.15, w.get("duration", 0.25))
                body = _format_phrase_multiline(
                    phrase, w_idx, hi_ass_col, primary_ass_tag,
                    limit=w_idx + 1, max_line_chars=28
                )
                fad = "{\\fad(0,160)}" if (use_fade and w_idx == len(phrase) - 1) else ""
                events.append(f"Dialogue: 0,{_format_ass_time(w_start)},{_format_ass_time(w_end)},Default,,0,0,0,,{fad}{body}")

    output_ass_path.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

DEFAULT_RENDER_CONFIG: Dict[str, Any] = {
    "aspect_ratio": "9:16",
    "transition": "fade",
    "ken_burns_style": "suave",
    "scene_pause_sec": 0.35,
    "voice_volume": 1.5,
}


def render_scene_clip(
    image_path: Path,
    audio_path: Path,
    output_clip_path: Path,
    scene_index: int,
    narrador_text: str,
    enable_subtitles: bool = True,
    enable_ken_burns: bool = True,
    subtitle_config: Optional[Dict[str, Any]] = None,
    render_config: Optional[Dict[str, Any]] = None,
    video_clip_path: Optional[Path] = None,
) -> float:
    """
    Renderiza un clip individual sincronizado con su locución,
    aplicando movimiento dinámico de cámara, pausa opcional y subtítulos.
    """
    rcfg = {**DEFAULT_RENDER_CONFIG, **(render_config or {})}
    aspect_ratio = rcfg.get("aspect_ratio", "9:16")
    target_w, target_h = (1920, 1080) if aspect_ratio == "16:9" else (TARGET_W, TARGET_H)
    kb_style = rcfg.get("ken_burns_style", "suave")
    if not enable_ken_burns:
        kb_style = "fijo"
    pause_sec = max(0.0, float(rcfg.get("scene_pause_sec") or 0.0))
    voice_vol = max(0.5, min(2.5, float(rcfg.get("voice_volume") or 1.5)))

    audio_dur = get_audio_duration_seconds(str(audio_path))
    duration = round(audio_dur + pause_sec, 2)
    total_frames = int(duration * FPS) + 1

    temp_ass_path = output_clip_path.parent / f"temp_sub_{output_clip_path.stem}.ass"

    use_animated_clip = bool(video_clip_path and video_clip_path.exists())

    # Seleccionar fuente de vídeo: clip animado I2V o imagen estática con Ken Burns
    v_filter_prefix = "[0:v]"
    if use_animated_clip:
        clip_dur = max(1.0, get_audio_duration_seconds(str(video_clip_path)))
        base_scale = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps={FPS}"
        if clip_dur >= duration:
            vf_zoom = base_scale
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_clip_path.resolve()),
                "-i", str(audio_path.resolve()),
            ]
        elif (duration / clip_dur) <= 1.85:
            # Estirar suavemente en una sola pasada (sin repeticiones ni saltos) hasta el último frame
            pts_ratio = round(duration / clip_dur, 4)
            vf_zoom = f"{base_scale},setpts={pts_ratio}*PTS"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_clip_path.resolve()),
                "-i", str(audio_path.resolve()),
            ]
        else:
            # Avance continuo siempre hacia adelante (nunca rebobinar/reverse para que los personajes no caminen hacia atrás)
            pts_ratio = round(duration / clip_dur, 4)
            vf_zoom = f"{base_scale},setpts={pts_ratio}*PTS"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_clip_path.resolve()),
                "-i", str(audio_path.resolve()),
            ]
    else:
        if kb_style != "fijo":
            max_zoom = 1.22 if kb_style == "dinamico" else 1.15
            step_z = 0.0018 if kb_style == "dinamico" else 0.0012
            motion_idx = scene_index % (4 if kb_style == "dinamico" else 3)
            if motion_idx == 0:
                zoom_expr = f"min(zoom+{step_z},{max_zoom})"
                x_expr = "iw/2-(iw/zoom/2)"
                y_expr = "ih/2-(ih/zoom/2)"
            elif motion_idx == 1:
                zoom_expr = f"max({max_zoom}-{step_z}*on,1.0)"
                x_expr = "iw/2-(iw/zoom/2)"
                y_expr = "ih/2-(ih/zoom/2)"
            elif motion_idx == 2:
                zoom_expr = "1.12" if kb_style == "dinamico" else "1.10"
                x_expr = "((iw-iw/zoom)/2)+sin(on/25)*25"
                y_expr = "ih/2-(ih/zoom/2)"
            else:
                # Paneo vertical suave (solo en modo dinámico)
                zoom_expr = "1.14"
                x_expr = "iw/2-(iw/zoom/2)"
                y_expr = "((ih-ih/zoom)/2)+sin(on/30)*22"
            vf_zoom = f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={target_w}x{target_h}:fps={FPS}"
        else:
            vf_zoom = f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps={FPS}"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(image_path.resolve()),
            "-i", str(audio_path.resolve()),
        ]

    if enable_subtitles and narrador_text.strip():
        create_ass_subtitles(
            text=narrador_text,
            audio_path=audio_path,
            duration=audio_dur,
            output_ass_path=temp_ass_path,
            subtitle_config=subtitle_config,
            target_w=target_w,
            target_h=target_h,
        )
        cmd.extend([
            "-filter_complex", f"[0:v]{vf_zoom},ass={temp_ass_path.name}[vfinal]",
            "-map", "[vfinal]",
            "-map", "1:a"
        ])
    else:
        cmd.extend([
            "-filter_complex", f"[0:v]{vf_zoom}[vfinal]",
            "-map", "[vfinal]",
            "-map", "1:a"
        ])

    af_chain = f"volume={voice_vol}"
    if pause_sec > 0:
        af_chain += f",apad=pad_dur={pause_sec}"

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-af", af_chain,
        "-t", str(duration),
        str(output_clip_path.resolve())
    ])

    try:
        res = subprocess.run(cmd, cwd=str(output_clip_path.parent.resolve()), capture_output=True, text=True, check=True)
    finally:
        if temp_ass_path.exists():
            temp_ass_path.unlink()

    return duration

def render_single_scene_preview_clip(
    scene: Dict[str, Any],
    scene_index: int = 0,
    project_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    enable_subtitles: bool = True,
    enable_ken_burns: bool = True,
    subtitle_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Renderiza el clip MP4 individual de una escena antes del ensamblado final
    para su revisión y aprobación Human-in-the-Loop en Telegram / n8n.
    """
    scene_id = scene.get("id") or (scene_index + 1)
    img_url = scene.get("image_url")
    audio_url = scene.get("audio_url")

    if not img_url:
        raise ValueError(f"La escena {scene_id} no tiene imagen generada para crear el clip.")

    img_path = resolve_media_path(img_url)
    if not img_path.exists():
        raise FileNotFoundError(f"Imagen no encontrada en disco para la escena {scene_id}: {img_path}")

    # Determinar carpeta de destino del clip
    if project_id and chapter_id:
        clips_dir = PROYECTOS_DIR / project_id / "capitulos" / chapter_id / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)
        clip_filename = f"clip_escena_{scene_id}.mp4"
        output_clip_path = clips_dir / clip_filename
        clip_url = f"/proyectos_data/{project_id}/capitulos/{chapter_id}/clips/{clip_filename}"
    else:
        clip_filename = f"clip_preview_sc{scene_id}_{uuid.uuid4().hex[:6]}.mp4"
        output_clip_path = MEDIA_DIR / clip_filename
        clip_url = f"/static/media/{clip_filename}"

    temp_silent_audio: Optional[Path] = None
    try:
        if audio_url:
            audio_path = resolve_media_path(audio_url)
        else:
            audio_path = Path("__missing__")

        if not audio_path.exists():
            # Crear pista de audio silenciosa temporal si aún no se ha locutado la escena
            est_dur = float(scene.get("duracion_estimada") or 4.0)
            temp_silent_audio = output_clip_path.parent / f"temp_silent_{scene_id}.mp3"
            silent_cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(est_dur),
                "-q:a", "9",
                "-acodec", "libmp3lame",
                str(temp_silent_audio)
            ]
            subprocess.run(silent_cmd, capture_output=True, text=True, check=True)
            audio_path = temp_silent_audio

        duration = render_scene_clip(
            image_path=img_path,
            audio_path=audio_path,
            output_clip_path=output_clip_path,
            scene_index=scene_index,
            narrador_text=scene.get("narrador", ""),
            enable_subtitles=enable_subtitles,
            enable_ken_burns=enable_ken_burns,
            subtitle_config=subtitle_config,
        )

        size_mb = round(output_clip_path.stat().st_size / (1024 * 1024), 2) if output_clip_path.exists() else 0.0
        return {
            "ok": True,
            "scene_id": scene_id,
            "clip_url": clip_url,
            "clip_path": str(output_clip_path),
            "duration": round(duration, 2),
            "size_mb": size_mb
        }
    finally:
        if temp_silent_audio and temp_silent_audio.exists():
            try:
                temp_silent_audio.unlink()
            except Exception:
                pass


def render_final_video(
    scenes: List[Dict[str, Any]],
    project_title: str = "Video Short",
    enable_subtitles: bool = True,
    enable_ken_burns: bool = True,
    project_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    subtitle_config: Optional[Dict[str, Any]] = None,
    render_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Renderiza todos los clips de las escenas y los concatena (con corte directo
    o transiciones xfade/acrossfade) en el archivo final MP4.
    """
    if not scenes:
        raise ValueError("No hay escenas para renderizar.")

    rcfg = {**DEFAULT_RENDER_CONFIG, **(render_config or {})}
    transition = rcfg.get("transition", "fade")
    if transition not in ("none", "fade", "fadeblack", "slideleft"):
        transition = "fade"

    render_id = uuid.uuid4().hex[:8]
    temp_dir = MEDIA_DIR / f"render_{render_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    clip_durations = []
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

            vclip_url = sc.get("video_clip_url")
            vclip_path = resolve_media_path(vclip_url) if vclip_url else None

            clip_path = temp_dir / f"clip_{i:02d}.mp4"
            dur = render_scene_clip(
                image_path=img_path,
                audio_path=audio_path,
                output_clip_path=clip_path,
                scene_index=i,
                narrador_text=sc.get("narrador", ""),
                enable_subtitles=enable_subtitles,
                enable_ken_burns=enable_ken_burns,
                subtitle_config=subtitle_config,
                render_config=rcfg,
                video_clip_path=vclip_path,
            )
            clip_durations.append(dur)
            clip_paths.append(clip_path)

        # 2. Unir clips en el MP4 definitivo en MEDIA_DIR
        temp_final_filename = f"video_short_{render_id}.mp4"
        temp_final_path = MEDIA_DIR / temp_final_filename

        if transition != "none" and len(clip_paths) > 1:
            td = round(min(0.45, min(clip_durations) / 3.0), 3)
            cmd = ["ffmpeg", "-y"]
            for p in clip_paths:
                cmd.extend(["-i", str(p.resolve())])

            filters = []
            cum_dur = clip_durations[0]
            prev_v = "[0:v]"
            prev_a = "[0:a]"
            for idx in range(1, len(clip_paths)):
                offset = round(max(0.0, cum_dur - td), 3)
                out_v = f"[v{idx}]"
                out_a = f"[a{idx}]"
                filters.append(f"{prev_v}[{idx}:v]xfade=transition={transition}:duration={td}:offset={offset}{out_v}")
                filters.append(f"{prev_a}[{idx}:a]acrossfade=d={td}{out_a}")
                prev_v = out_v
                prev_a = out_a
                cum_dur = cum_dur + clip_durations[idx] - td

            total_duration = round(cum_dur, 2)
            cmd.extend([
                "-filter_complex", ";".join(filters),
                "-map", prev_v,
                "-map", prev_a,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                str(temp_final_path.resolve()),
            ])
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        else:
            total_duration = round(sum(clip_durations), 2)
            concat_list_file = temp_dir / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for p in clip_paths:
                    normalized_path = str(p.resolve()).replace("\\", "/")
                    f.write(f"file '{normalized_path}'\n")

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
