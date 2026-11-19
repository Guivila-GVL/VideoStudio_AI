import math
import uuid
import subprocess
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROYECTOS_DIR = BASE_DIR / "proyectos"
MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

_SPRITE_CACHE: Dict[str, Image.Image] = {}


def _extract_transparent_sprite(img_path: Path, flip_x: bool = False, dark_silhouette: bool = False) -> Image.Image:
    """
    Extrae el personaje de una hoja sobre fondo blanco (#FFFFFF) mediante flood-fill exterior
    desde los bordes (preservando el blanco interior del hocico, ojos y camisa) y limpiando la peana de arena.
    """
    cache_key = f"{img_path.resolve()}::{flip_x}::{dark_silhouette}"
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key].copy()

    im = Image.open(img_path).convert("RGBA")
    w, h = im.size
    px = im.load()

    visited = bytearray(w * h)
    is_bg = bytearray(w * h)
    q: deque[Tuple[int, int]] = deque()

    def _is_removable_bg(x: int, y: int) -> bool:
        r, g, b, _ = px[x, y]
        # Fondo blanco/gris muy claro exterior
        if r > 224 and g > 222 and b > 218 and abs(r - g) < 16 and abs(g - b) < 18:
            return True
        # Peana de arena/hierba suelta en el 14% inferior de la ficha
        if y > int(h * 0.855):
            # Mantener únicamente las botas oscuras del poeta o las pezuñas/patas oscuras de Platero
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            is_boot_or_hoof = (lum < 145) or (r < 155 and g < 140 and b < 135)
            if not is_boot_or_hoof:
                return True
        return False

    for bx in range(w):
        for by in (0, h - 1):
            idx = by * w + bx
            if not visited[idx] and _is_removable_bg(bx, by):
                visited[idx] = 1
                is_bg[idx] = 1
                q.append((bx, by))
    for by in range(h):
        for bx in (0, w - 1):
            idx = by * w + bx
            if not visited[idx] and _is_removable_bg(bx, by):
                visited[idx] = 1
                is_bg[idx] = 1
                q.append((bx, by))

    while q:
        cx, cy = q.popleft()
        for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                nidx = ny * w + nx
                if not visited[nidx]:
                    visited[nidx] = 1
                    if _is_removable_bg(nx, ny):
                        is_bg[nidx] = 1
                        q.append((nx, ny))

    alpha = Image.new("L", (w, h), 255)
    apx = alpha.load()
    for y in range(h):
        row_off = y * w
        for x in range(w):
            if is_bg[row_off + x]:
                apx[x, y] = 0

    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1.0))
    im.putalpha(alpha)

    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)

    if dark_silhouette:
        # Convertir en figura nocturna sombreada (guarda oscuro en la noche morada)
        r_ch, g_ch, b_ch, a_ch = im.split()
        r_ch = ImageEnhance.Brightness(r_ch).enhance(0.28)
        g_ch = ImageEnhance.Brightness(g_ch).enhance(0.22)
        b_ch = ImageEnhance.Brightness(b_ch).enhance(0.36)
        im = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))

    if flip_x:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)

    _SPRITE_CACHE[cache_key] = im
    return im.copy()


def _resolve_project_assets(project_id: str, prompt_text: str) -> Dict[str, Path]:
    """Localiza las rutas físicas de cuerpo entero de Platero, El Poeta, figura secundaria y escenarios."""
    p_dir = PROYECTOS_DIR / (project_id or "platero_y_yo")
    chars_dir = p_dir / "personajes"
    escs_dir = p_dir / "escenarios"

    p_low = (prompt_text or "").lower()
    is_walking = any(k in p_low for k in ("camina", "sube", "avanza", "sendero", "walk", "uphill", "trot"))

    # Usar siempre vistas de cuerpo entero (nunca _v_detalle cortado por la cintura)
    platero_view = "platero_v_perfil.jpg" if is_walking else "platero.jpg"
    poeta_view = "el_poeta_v_perfil.jpg" if is_walking else "el_poeta.jpg"

    platero_path = chars_dir / platero_view
    if not platero_path.exists():
        platero_path = chars_dir / "platero.jpg"

    poeta_path = chars_dir / poeta_view
    if not poeta_path.exists():
        poeta_path = chars_dir / "el_poeta.jpg"

    guard_base_path = chars_dir / "darbon_v_perfil.jpg"
    if not guard_base_path.exists():
        guard_base_path = chars_dir / "darbon.jpg"

    if any(k in p_low for k in ("colina", "molino", "prado", "florecilla", "camino sube", "uphill", "country path", "hillside", "meadow")):
        esc_path = escs_dir / "colinas_molino_viento.jpg"
    elif any(k in p_low for k in ("establo", "corral", "pesebre", "stable")):
        esc_path = escs_dir / "establo_platero.jpg"
    elif any(k in p_low for k in ("pozo", "huerto", "naranj", "well", "orchard")):
        esc_path = escs_dir / "pozo_viejo_huerto.jpg"
    else:
        esc_path = escs_dir / "calles_blancas_moguer.jpg"

    if not esc_path.exists():
        cands = list(escs_dir.glob("*.jpg"))
        esc_path = cands[0] if cands else platero_path

    return {
        "platero": platero_path,
        "poeta": poeta_path,
        "guard_base": guard_base_path,
        "escenario": esc_path,
    }


def _prepare_styled_background(esc_path: Path, prompt_text: str, w: int = 1080, h: int = 1920) -> Image.Image:
    """
    Prepara el escenario 1080x1920 aplicando un degradado nocturno continuo y suave
    (sin cortes horizontales bruscos) cuando la escena transcurre al anochecer/noche.
    """
    bg = Image.open(esc_path).convert("RGB")
    bw, bh = bg.size
    target_ratio = w / h
    cur_ratio = bw / bh
    if cur_ratio > target_ratio:
        new_w = int(bh * target_ratio)
        left = (bw - new_w) // 2
        bg = bg.crop((left, 0, left + new_w, bh))
    else:
        new_h = int(bw / target_ratio)
        top = (bh - new_h) // 2
        bg = bg.crop((0, top, bw, top + new_h))
    bg = bg.resize((w, h), Image.Resampling.LANCZOS)

    p_low = (prompt_text or "").lower()
    is_night = any(
        k in p_low
        for k in ("noche", "morad", "malva", "brumosa", "sombra", "estrell", "night", "purple", "mauve", "twilight", "dusk", "shadow", "dark", "starry")
    )

    if is_night:
        bg = ImageEnhance.Brightness(bg).enhance(0.52)
        bg = ImageEnhance.Contrast(bg).enhance(1.08)
        bg_rgba = bg.convert("RGBA")

        # Degradado continuo suave de cielo nocturno índigo-malva a suelo en penumbra
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for y in range(h):
            t = y / h
            # Curva coseno suave sin escalón
            blend = 0.5 * (1.0 + math.cos(min(1.0, t * 1.35) * math.pi))
            alpha = int(115 + 105 * blend)
            r_c = int(42 + (1.0 - blend) * 18)
            g_c = int(26 + (1.0 - blend) * 12)
            b_c = int(86 + blend * 22)
            odraw.line([(0, y), (w, y)], fill=(r_c, g_c, b_c, alpha))

        bg_rgba = Image.alpha_composite(bg_rgba, overlay)

        sdraw = ImageDraw.Draw(bg_rgba)
        star_coords = [
            (140, 110, 2), (280, 75, 2), (460, 150, 3), (620, 95, 2), (810, 130, 2),
            (940, 85, 2), (190, 230, 2), (530, 210, 2), (740, 245, 2), (890, 195, 3),
        ]
        for sx, sy, sr in star_coords:
            sdraw.ellipse((sx - sr - 2, sy - sr - 2, sx + sr + 2, sy + sr + 2), fill=(230, 220, 255, 55))
            sdraw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(255, 252, 240, 210))

        # Luna suave al fondo
        sdraw.ellipse((825, 95, 915, 185), fill=(235, 220, 255, 38))
        sdraw.ellipse((843, 113, 897, 167), fill=(250, 245, 255, 185))
        return bg_rgba

    return bg.convert("RGBA")


def _place_guard_character(
    canvas: Image.Image,
    guard_path: Path,
    x_center: int,
    y_feet: int,
    target_h: int = 720,
    raise_spike: float = 0.0,
    cigar_glow: float = 1.0,
) -> None:
    """
    Coloca la figura ilustrada del guarda en silueta nocturna con el resplandor rojizo
    del cigarro y el pincho de hierro fino apuntando hacia la alforja.
    """
    guard_sp = _extract_transparent_sprite(guard_path, flip_x=False, dark_silhouette=True)
    gw = int(guard_sp.width * (target_h / guard_sp.height))
    guard_r = guard_sp.resize((gw, target_h), Image.Resampling.LANCZOS)
    gx = x_center - gw // 2
    gy = y_feet - target_h

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Sombra bajo los pies
    d.ellipse((x_center - int(gw * 0.42), y_feet - 18, x_center + int(gw * 0.42), y_feet + 14), fill=(12, 8, 22, 125))
    layer.alpha_composite(guard_r, (gx, gy))

    # Brasa roja del cigarro junto al rostro del guarda e iluminación cálida sobre su cara
    cigar_x = gx + int(gw * 0.24)
    cigar_y = gy + int(target_h * 0.21)
    halo = int(28 + 16 * cigar_glow)
    d.ellipse((cigar_x - halo, cigar_y - halo, cigar_x + halo, cigar_y + halo), fill=(255, 68, 18, int(85 * cigar_glow)))
    d.ellipse((cigar_x - 5, cigar_y - 5, cigar_x + 5, cigar_y + 5), fill=(255, 175, 65, 255))

    # Pincho de hierro fino en su mano extendida hacia el seroncillo
    hand_x = gx + int(gw * 0.20)
    hand_y = gy + int(target_h * (0.48 - 0.06 * raise_spike))
    tip_x = hand_x - int(165 + 45 * raise_spike)
    tip_y = hand_y - int(25 + 55 * raise_spike)
    d.line([(hand_x + 25, hand_y + 12), (tip_x, tip_y)], fill=(195, 208, 225, 235), width=4)

    canvas.alpha_composite(layer)


def _draw_butterflies_flock(
    canvas: Image.Image,
    origin_x: int,
    origin_y: int,
    num_butterflies: int = 0,
    progress: float = 0.5,
) -> None:
    """
    Dibuja mariposas blancas delicadas y orgánicas con alas curvas luminosas elevándose en la noche.
    """
    if num_butterflies <= 0:
        return
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    for i in range(num_butterflies):
        angle = i * 1.65 + progress * 4.0
        rise = int((progress * 620) + i * 48)
        bx = origin_x + int(math.sin(angle) * (38 + i * 20))
        by = origin_y - 25 - rise
        if by < 85:
            by = 85 + (by % 160)

        flap = 0.42 + 0.58 * abs(math.sin(progress * 16.0 + i * 1.9))
        rw = max(6, int((18 + (i % 3) * 4) * flap))
        rh = 12 + (i % 3) * 3

        # Resplandor suave lunar alrededor de cada mariposa
        d.ellipse((bx - 22, by - 18, bx + 22, by + 18), fill=(240, 240, 255, 48))
        # Alas superiores e inferiores redondeadas (óvalos superpuestos)
        d.ellipse((bx - rw - 2, by - rh, bx - 1, by + 2), fill=(252, 252, 255, 238))
        d.ellipse((bx + 1, by - rh, bx + rw + 2, by + 2), fill=(246, 248, 255, 238))
        d.ellipse((bx - int(rw * 0.75), by - 2, bx - 1, by + int(rh * 0.85)), fill=(245, 245, 255, 220))
        d.ellipse((bx + 1, by - 2, bx + int(rw * 0.75), by + int(rh * 0.85)), fill=(242, 245, 255, 220))
        d.line([(bx, by - 6), (bx, by + 7)], fill=(110, 105, 125, 225), width=2)

    canvas.alpha_composite(layer)


def render_25d_scene_frame(
    prompt_text: str,
    progress: float = 0.35,
    project_id: str = "platero_y_yo",
) -> Image.Image:
    """
    Renderiza un fotograma 1080x1920 en instante t=progress (0.0 a 1.0) colocando los
    sprites reales de cuerpo entero de Platero y El Poeta y animando la acción de la escena.
    """
    W, H = 1080, 1920
    assets = _resolve_project_assets(project_id, prompt_text)
    canvas = _prepare_styled_background(assets["escenario"], prompt_text, W, H)

    p_low = (prompt_text or "").lower()
    has_guard = any(k in p_low for k in ("hombre oscuro", "gorra", "pincho", "cigarro", "guard", "dark man", "spike", "cigar"))
    has_spike_attack = any(k in p_low for k in ("clavar", "atacar", "seroncillo", "alforja", "levantando su pincho", "raising his sharp pin", "opens the leather"))
    has_butterflies_finale = any(k in p_low for k in ("alimento ideal", "pasa, libre", "vuelan", "volando libres", "white butterflies flutters", "flying white butterflies", "noche estrellada"))
    has_butterflies_dialog = any(k in p_low for k in ("¿va argo", "vea usted", "mariposas blancas", "scared eyes", "ojos asustados")) and not has_butterflies_finale

    platero_sp = _extract_transparent_sprite(assets["platero"], flip_x=False)
    poeta_sp = _extract_transparent_sprite(assets["poeta"], flip_x=True)

    # Sombra suave bajo los personajes para asentarlos en el suelo del escenario
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow_layer)

    if has_butterflies_finale:
        # ESCENA 5: El guarda se detiene, Platero y el Poeta avanzan aliviados y las mariposas blancas ascienden al cielo nocturno
        walk_dx = int(progress * 55)
        bob = int(math.sin(progress * math.pi * 4) * 5)

        p_h = 720
        p_w = int(poeta_sp.width * (p_h / poeta_sp.height))
        poeta_r = poeta_sp.resize((p_w, p_h), Image.Resampling.LANCZOS)
        po_x, po_y = 75 + walk_dx // 2, 1650 - p_h + bob // 2

        pl_h = 560
        pl_w = int(platero_sp.width * (pl_h / platero_sp.height))
        platero_r = platero_sp.resize((pl_w, pl_h), Image.Resampling.LANCZOS)
        pl_x, pl_y = 330 + walk_dx, 1675 - pl_h + bob

        sdraw.ellipse((po_x + 20, 1635, po_x + p_w - 20, 1665), fill=(12, 8, 22, 115))
        sdraw.ellipse((pl_x + 25, 1655, pl_x + pl_w - 25, 1690), fill=(12, 8, 22, 125))
        canvas.alpha_composite(shadow_layer)

        canvas.alpha_composite(poeta_r, (po_x, po_y))
        canvas.alpha_composite(platero_r, (pl_x, pl_y))
        _place_guard_character(canvas, assets["guard_base"], x_center=905, y_feet=1610, target_h=650, raise_spike=0.0, cigar_glow=0.65)
        _draw_butterflies_flock(canvas, origin_x=pl_x + int(pl_w * 0.45), origin_y=pl_y + int(pl_h * 0.42), num_butterflies=12, progress=progress)

    elif has_spike_attack:
        # ESCENA 4: El guarda levanta su pincho de hierro hacia el seroncillo; Platero se encoge y el Poeta abre la alforja
        recoil = int(math.sin(progress * math.pi) * 35)

        p_h = 735
        p_w = int(poeta_sp.width * (p_h / poeta_sp.height))
        poeta_r = poeta_sp.resize((p_w, p_h), Image.Resampling.LANCZOS)
        po_x, po_y = 80, 1655 - p_h

        pl_h = 560
        pl_w = int(platero_sp.width * (pl_h / platero_sp.height))
        platero_r = platero_sp.resize((pl_w, pl_h), Image.Resampling.LANCZOS)
        pl_x, pl_y = 310 - recoil // 2, 1675 - pl_h

        sdraw.ellipse((po_x + 20, 1640, po_x + p_w - 20, 1670), fill=(12, 8, 22, 115))
        sdraw.ellipse((pl_x + 25, 1655, pl_x + pl_w - 25, 1690), fill=(12, 8, 22, 125))
        canvas.alpha_composite(shadow_layer)

        canvas.alpha_composite(poeta_r, (po_x, po_y))
        canvas.alpha_composite(platero_r, (pl_x, pl_y))
        guard_x = 875 - int(progress * 65)
        _place_guard_character(canvas, assets["guard_base"], x_center=guard_x, y_feet=1665, target_h=725, raise_spike=min(1.0, progress * 1.35), cigar_glow=1.0)
        if progress > 0.45:
            _draw_butterflies_flock(canvas, origin_x=pl_x + int(pl_w * 0.45), origin_y=pl_y + int(pl_h * 0.42), num_butterflies=3, progress=(progress - 0.45) * 0.5)

    elif has_butterflies_dialog:
        # ESCENA 3: «¿Va argo?… Vea usted… Mariposas blancas…»
        tremble = int(math.sin(progress * math.pi * 10) * 3)

        p_h = 750
        p_w = int(poeta_sp.width * (p_h / poeta_sp.height))
        poeta_r = poeta_sp.resize((p_w, p_h), Image.Resampling.LANCZOS)
        po_x, po_y = 75, 1665 - p_h

        pl_h = 580
        pl_w = int(platero_sp.width * (pl_h / platero_sp.height))
        platero_r = platero_sp.resize((pl_w, pl_h), Image.Resampling.LANCZOS)
        pl_x, pl_y = 315 + tremble, 1685 - pl_h

        sdraw.ellipse((po_x + 20, 1650, po_x + p_w - 20, 1680), fill=(12, 8, 22, 115))
        sdraw.ellipse((pl_x + 25, 1665, pl_x + pl_w - 25, 1700), fill=(12, 8, 22, 125))
        canvas.alpha_composite(shadow_layer)

        canvas.alpha_composite(poeta_r, (po_x, po_y))
        canvas.alpha_composite(platero_r, (pl_x, pl_y))
        _place_guard_character(canvas, assets["guard_base"], x_center=865, y_feet=1670, target_h=735, raise_spike=0.35, cigar_glow=0.85 + 0.15 * math.sin(progress * 12))
        _draw_butterflies_flock(canvas, origin_x=pl_x + int(pl_w * 0.45), origin_y=pl_y + int(pl_h * 0.42), num_butterflies=3, progress=progress * 0.35)

    elif has_guard:
        # ESCENA 2: El hombre oscuro con gorra, pincho y cigarro baja de la casucha; Platero retrocede amedrentado
        step_back = int(progress * 65)
        guard_x = 935 - int(progress * 105)
        guard_y = 1570 + int(progress * 95)

        p_h = 720
        p_w = int(poeta_sp.width * (p_h / poeta_sp.height))
        poeta_r = poeta_sp.resize((p_w, p_h), Image.Resampling.LANCZOS)
        po_x, po_y = 115 - step_back // 3, 1650 - p_h

        pl_h = 560
        pl_w = int(platero_sp.width * (pl_h / platero_sp.height))
        platero_r = platero_sp.resize((pl_w, pl_h), Image.Resampling.LANCZOS)
        pl_x, pl_y = 355 - step_back, 1675 - pl_h

        sdraw.ellipse((po_x + 20, 1635, po_x + p_w - 20, 1665), fill=(12, 8, 22, 115))
        sdraw.ellipse((pl_x + 25, 1655, pl_x + pl_w - 25, 1690), fill=(12, 8, 22, 125))
        canvas.alpha_composite(shadow_layer)

        canvas.alpha_composite(poeta_r, (po_x, po_y))
        canvas.alpha_composite(platero_r, (pl_x, pl_y))
        _place_guard_character(canvas, assets["guard_base"], x_center=guard_x, y_feet=guard_y, target_h=int(640 + 75 * progress), raise_spike=0.2, cigar_glow=0.8 + 0.2 * math.sin(progress * 15))

    else:
        # ESCENA 1: Platero y el Poeta suben caminando por el sendero de Moguer al caer la noche morada
        walk_dx = int(progress * 125)
        bob_pl = int(abs(math.sin(progress * math.pi * 6)) * 12)
        bob_po = int(abs(math.cos(progress * math.pi * 6)) * 9)

        p_h = 730
        p_w = int(poeta_sp.width * (p_h / poeta_sp.height))
        poeta_r = poeta_sp.resize((p_w, p_h), Image.Resampling.LANCZOS)
        po_x, po_y = 120 + walk_dx, 1645 - p_h - bob_po

        pl_h = 570
        pl_w = int(platero_sp.width * (pl_h / platero_sp.height))
        platero_r = platero_sp.resize((pl_w, pl_h), Image.Resampling.LANCZOS)
        pl_x, pl_y = 360 + walk_dx, 1675 - pl_h - bob_pl

        sdraw.ellipse((po_x + 20, 1630, po_x + p_w - 20, 1660), fill=(12, 8, 22, 115))
        sdraw.ellipse((pl_x + 25, 1655, pl_x + pl_w - 25, 1690), fill=(12, 8, 22, 125))
        canvas.alpha_composite(shadow_layer)

        canvas.alpha_composite(poeta_r, (po_x, po_y))
        canvas.alpha_composite(platero_r, (pl_x, pl_y))

    return canvas.convert("RGB")


def generate_25d_draft_image(
    prompt: str,
    final_path: Path,
    web_url: str,
    project_id: str = "platero_y_yo",
) -> Dict[str, Any]:
    """Genera la imagen clave 9:16 de la escena con los personajes y escenarios reales del proyecto (0€)."""
    frame = render_25d_scene_frame(prompt_text=prompt, progress=0.45, project_id=project_id)
    frame.save(final_path, format="JPEG", quality=92)
    return {
        "url": web_url,
        "provider": "draft_25d_canon_compositor (0€)",
        "file_path": str(final_path),
    }


def generate_25d_draft_video(
    prompt: str,
    target_duration_sec: float = 10.0,
    project_id: str = "platero_y_yo",
) -> Dict[str, Any]:
    """
    Genera un clip MP4 animado por capas (2.5D Puppet Animation, 0€) donde los personajes
    reales del proyecto se mueven físicamente dentro del escenario según la acción de la escena.
    """
    dur = max(4.5, min(25.0, float(target_duration_sec or 10.0)))
    fps = 12
    total_frames = max(24, int(round(dur * fps)))

    filename = f"anim_draft_{uuid.uuid4().hex[:10]}.mp4"
    out_path = MEDIA_DIR / filename

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-vf", "fps=25",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "20",
        str(out_path.resolve()),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert proc.stdin is not None
    try:
        for f_idx in range(total_frames):
            prog = f_idx / max(1, total_frames - 1)
            frame_rgb = render_25d_scene_frame(prompt_text=prompt, progress=prog, project_id=project_id)
            proc.stdin.write(frame_rgb.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()

    size_mb = round(out_path.stat().st_size / (1024 * 1024), 2) if out_path.exists() else 0.0
    return {
        "video_clip_url": f"/static/media/{filename}",
        "provider": "draft_25d_puppet_animation (0€)",
        "duration": round(dur, 1),
        "segments": 1,
        "linked_next": False,
        "size_mb": size_mb,
    }
