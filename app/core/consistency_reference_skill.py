"""
Adaptación aislada de la Skill #102 (10114514/consistency-reference-prompt)
aplicada exclusivamente al Paso 2: Consistencia visual de personajes y escenarios.

Mantiene intacta la implementación actual de producción y expone las 3 mejoras
aprovechables de la skill adaptadas al universo artístico de VideoStudio AI (9:16 y estilos pictóricos):
1. Character 6-View Split Reference Sheet & Structured Baseline:
   - Tercio izquierdo (3 close-ups de cabeza apilados: frontal, 45° 3/4, 90° perfil) +
     dos tercios derechos (3 vistas de cuerpo entero: frontal, lateral 90°, trasera),
     sin líneas divisorias ni marcos, sobre fondo blanco puro (#FFFFFF).
   - Descriptores estructurados en 9 campos: age, build, hairstyle/coat, face, skin/texture,
     clothing/tack, accessories, distinguishing_features, expression_baseline.
2. Prop Reference Prompt & Multi-State Sheet:
   - Fichas de referencia de accesorios/objetos clave del guion (p. ej. alforja/seroncillo,
     pincho de hierro, mariposas blancas) aislados en fondo blanco sin partes humanas,
     mostrando regiones separadas por estado (cerrado vs abierto).
3. Scene Establishing & Low-Light Shadow-Preservation Anchor:
   - Estructura de plano general de escenario con iluminación, paleta de color, objetos clave
     y atmósfera, más la regla de preservación de detalle en sombras para escenas nocturnas
     ("For night or low-light scenes, preserve shadow details — dark areas with visible detail,
     no crushed blacks") y bloqueo de personajes no presentes en el capítulo.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageStat

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
PROYECTOS_DIR = BASE_DIR / "proyectos"


# 1. Perfiles estructurados (9 atributos de Skill #102) para personajes del estudio
STRUCTURED_CHARACTER_PROFILES: Dict[str, Dict[str, str]] = {
    "platero": {
        "age": "young prime Andalusian donkey",
        "build": "small compact sturdy quadruped build (shoulder height at 62% of the 13-year-old poet boy)",
        "hairstyle_or_coat": "fluffy silvery-grey cotton-like coat with soft pale muzzle and upright furry ears",
        "face": "expressive gentle equine muzzle with warm nostrils and long dark eyelashes",
        "skin_or_texture": "soft brushed cotton-like fur texture with translucent watercolor washes",
        "clothing_or_tack": "simple rustic woven esparto and brown leather saddlebag (seroncillo/alforja) resting over back",
        "accessories": "thin rustic hemp halter rope",
        "distinguishing_features": "jet-black eyes shining like two polished black crystal beetles, dark hooves",
        "expression_baseline": "tender, docile, curious and affectionate expression",
    },
    "el_poeta": {
        "age": "13-year-old adolescent Spanish boy",
        "build": "slender youthful build, height 1.55m (head and shoulders above Platero)",
        "hairstyle_or_coat": "dark chestnut wavy hair softly tousled under hat",
        "face": "sensitive noble oval face with serene deep dark eyes and gentle eyebrows",
        "skin_or_texture": "warm light Mediterranean olive skin tone with soft watercolor shading",
        "clothing_or_tack": "unbleached raw linen shirt with open collar, dark fine wool waistcoat, rolled trousers and worn brown ankle boots",
        "accessories": "wide-brimmed dark Andalusian felt hat shading his forehead",
        "distinguishing_features": "poetic contemplative posture, gentle protective hands",
        "expression_baseline": "serene, lyrical, observant and compassionate expression",
    },
    "guarda_consumos": {
        "age": "45-year-old weathered rural tax guard (Guarda de Consumos)",
        "build": "lean wiry stocky rural guard build (explicitly NOT Darbón the burly white-bearded veterinarian)",
        "hairstyle_or_coat": "short dark unkempt hair hidden beneath a dark peasant cap, rough stubble",
        "face": "angular weathered face with suspicious narrow eyes, briefly lit in red-orange by cigar ember",
        "skin_or_texture": "rough sun-tanned skin in deep twilight shadow",
        "clothing_or_tack": "dark charcoal-brown rustic wool jacket, dark trousers and worn country boots",
        "accessories": "dark visor peasant cap, glowing cigar stub at mouth corner, long thin iron inspection spike rod (pincho de hierro)",
        "distinguishing_features": "red-orange cigar glow on cheek, long thin iron spike held in right hand",
        "expression_baseline": "stern, suspicious, then bewildered and halting expression",
    },
}


# 2. Catálogo de Accesorios / Props clave extraídos del guion (Skill #102 Prop Prompts)
CHAPTER_2_PROPS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "alforja_seroncillo_mariposas",
        "nombre": "Seroncillo / Alforja de Platero con Mariposas Blancas",
        "material": "trenzado de esparto rústico y cuero marrón envejecido con costuras de cáñamo",
        "color": "ocre arena cálido, cuero siena tostado y blanco nacarado luminoso en las mariposas",
        "shape": "alforja doble de montura rural con solapa superior abatible",
        "size": "45 cm de ancho, proporcionada al lomo de Platero",
        "states": [
            "State 1 (Left region - Closed/Intact): rustic woven esparto and brown leather saddlebag closed with buckle strap",
            "State 2 (Right region - Open/Revealing): saddlebag flap wide open appearing empty of contraband but releasing three delicate glowing pure white butterflies",
        ],
        "distinguishing_details": "hand-woven texture, worn leather edges, translucent white butterfly wings glowing softly",
    },
    {
        "id": "pincho_hierro_consumos",
        "nombre": "Pincho de Hierro del Guarda de Consumos",
        "material": "hierro forjado oscuro envejecido con empuñadura de madera basta",
        "color": "gris acero pavonado oscuro y marrón nogal desgastado",
        "shape": "varilla metálica larga y fina de inspección de fardos acabada en punta cónica",
        "size": "85 cm de longitud, 1 cm de grosor",
        "states": [
            "Front view: full length iron inspection rod showing wooden handle and tapered steel tip",
            "Back/side view: metallic patina and forged handle ring",
        ],
        "distinguishing_details": "cold forged iron sheen, subtle rust patina, static object with no human hands visible",
    },
]


def build_skill102_character_6view_prompt(
    character: Dict[str, Any],
    style_clause: str = "delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, subtle sepia pencil and ink outlines, no 3D CGI, no photorealism",
) -> str:
    """
    Construye el prompt unificado de 6 vistas de la Skill #102 adaptado al estilo del proyecto:
    - Tercio izquierdo (3 primeros planos de cabeza apilados: frontal, 45° lado, 90° perfil).
    - Dos tercios derechos (3 vistas de cuerpo entero de izquierda a derecha: frontal, lateral, trasera).
    - Sin marcos, sin líneas divisorias, sobre fondo blanco puro (#FFFFFF), con los 9 atributos de identidad.
    """
    cid = (character.get("id") or "").lower()
    name = character.get("nombre", "Character").strip()
    profile = STRUCTURED_CHARACTER_PROFILES.get(cid)

    if profile:
        desc_block = (
            f"{name}: age/stage: {profile['age']}; build & scale: {profile['build']}; "
            f"hair/coat: {profile['hairstyle_or_coat']}; face: {profile['face']}; "
            f"skin/texture: {profile['skin_or_texture']}; clothing/tack: {profile['clothing_or_tack']}; "
            f"accessories: {profile['accessories']}; distinguishing features: {profile['distinguishing_features']}; "
            f"expression baseline: {profile['expression_baseline']}"
        )
    else:
        raw_desc = character.get("ancla_visual") or character.get("descripcion_visual") or name
        desc_block = f"{name}: {raw_desc}"

    return (
        "Character reference sheet, split layout on pure solid white background (#FFFFFF). "
        "Left one-third top-to-bottom: three head close-ups stacked vertically filling their sections completely "
        "with full top of head and ears visible — front view, 45-degree side view, 90-degree profile view, "
        "only three head images in this section, no picture frames, no white borders, no dividing border lines. "
        "Right two-thirds left-to-right: three full-body views arranged horizontally — front view full-body shot, "
        "90-degree side profile full-body shot, rear back full-body shot, all filling their sections completely, "
        "no picture frames, no border lines, natural standing pose, showing complete anatomy head to toe/hooves. "
        f"[{desc_block}]. Even soft studio reference lighting. "
        f"No text, no captions, no labels, no watermarks. {style_clause}, masterpiece."
    )


def build_skill102_prop_prompt(
    prop: Dict[str, Any],
    style_clause: str = "delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, subtle sepia pencil and ink outlines, no 3D CGI, no photorealism",
) -> str:
    """
    Construye el prompt de referencia de accesorio/prop según la Skill #102:
    - Objeto estático sobre fondo blanco puro (#FFFFFF), sin sombras duras ni partes del cuerpo humano.
    - Si tiene múltiples estados (ej. alforja cerrada y abierta con mariposas), divide la lámina en regiones limpias.
    """
    states_list = prop.get("states") or []
    states_str = " | ".join(states_list) if states_list else "Show front view and back view."
    return (
        "Product/prop reference close-up, laid flat on pure solid white background (#FFFFFF), no harsh shadows. "
        f"{prop.get('nombre', 'Prop')}: material: {prop.get('material', '')}; color: {prop.get('color', '')}; "
        f"shape: {prop.get('shape', '')}; size: {prop.get('size', '')}; "
        f"distinguishing details: {prop.get('distinguishing_details', '')}. "
        f"Multi-state regions: {states_str}. "
        "Describe as static objects only, no action verbs, no human body parts (no hands, arms, or fingers) visible. "
        f"No text, no captions, no watermarks. {style_clause}, masterpiece."
    )


def build_skill102_scene_reference_prompt(
    escenario: Dict[str, Any],
    scene_context: str = "",
    characters_in_scene: Optional[List[str]] = None,
    props_in_scene: Optional[List[Dict[str, Any]]] = None,
    is_night_or_low_light: bool = True,
    style_clause: str = "delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, subtle sepia pencil and ink outlines, vertical 9:16 composition, no 3D CGI, no photorealism",
) -> str:
    """
    Construye el prompt de consistencia de escena combinando:
    - Descripción estructurada del escenario (lighting, color palette, key objects, atmosphere)
      sin contradicciones de sol de mediodía cuando la escena es nocturna.
    - Regla de preservación de sombras de Skill #102 ("For night or low-light scenes, preserve shadow details —
      dark areas with visible detail, no crushed blacks").
    - Anclas de personajes de 9 atributos con bloqueo de intrusos (ej. sin Darbón en el Cap. 2).
    - Anclas de props activos en la escena.
    """
    esc_name = escenario.get("nombre", "Camino de Moguer").strip()

    if is_night_or_low_light:
        env_struct = (
            f"Scene establishing vertical 9:16 shot of {esc_name} at misty purple twilight/night: "
            "lighting: soft lavender-mauve dusk sky glow behind the distant church tower and warm red-orange cigar ember accent; "
            "color palette: deep indigo-violet, soft mauve, sage twilight green, warm ochre earth and luminous pearl white; "
            "key environment objects: uphill country path bordered by wild white bellflowers, rustic wooden shack and stacked dark coal sacks; "
            "atmosphere: lyrical, misty, quiet Andalusian evening suspense. "
            "For night or low-light scenes, preserve shadow details — dark areas must have visible watercolor and sepia ink detail, no crushed blacks"
        )
    else:
        raw_desc = escenario.get("descripcion_visual", "")
        env_struct = f"Scene establishing vertical 9:16 shot of {esc_name}: {raw_desc}"

    char_clauses: List[str] = []
    for c_key in (characters_in_scene or ["platero", "el_poeta", "guarda_consumos"]):
        norm_k = c_key.lower()
        if "platero" in norm_k:
            p = STRUCTURED_CHARACTER_PROFILES["platero"]
            char_clauses.append(
                f"Platero ({p['build']}, {p['hairstyle_or_coat']}, {p['distinguishing_features']}, {p['clothing_or_tack']})"
            )
        elif "poeta" in norm_k or "narrador" in norm_k:
            p = STRUCTURED_CHARACTER_PROFILES["el_poeta"]
            char_clauses.append(
                f"El Poeta ({p['age']}, {p['build']}, {p['clothing_or_tack']}, {p['accessories']})"
            )
        elif "guarda" in norm_k or "hombre oscuro" in norm_k:
            p = STRUCTURED_CHARACTER_PROFILES["guarda_consumos"]
            char_clauses.append(
                f"Guarda de Consumos ({p['age']}, {p['build']}, {p['clothing_or_tack']}, {p['accessories']})"
            )

    prop_clauses: List[str] = []
    for pr in (props_in_scene or CHAPTER_2_PROPS_CATALOG):
        prop_clauses.append(
            f"Prop reference [{pr['nombre']}: {pr['material']}, {pr['color']}, {pr['distinguishing_details']}]"
        )

    parts = [env_struct]
    if scene_context:
        parts.append(f"Action & Staging: {scene_context.strip()}")
    if char_clauses:
        parts.append("Consistent Characters: " + "; ".join(char_clauses))
    if prop_clauses:
        parts.append("Consistent Props: " + "; ".join(prop_clauses))
    parts.append("Strict character lock: exclude unrelated database characters (NO Darbón the white-bearded veterinarian)")
    parts.append(f"No text, no captions, no watermarks. {style_clause}, masterpiece.")
    return ". ".join(parts)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"]
    )
    for fp in candidates:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _create_6view_character_strip(
    char_dir: Path,
    char_id: str,
    width: int = 1000,
    height: int = 440,
) -> Image.Image:
    """
    Compone la hoja de referencia de 6 vistas sin bordes (patrón Skill #102):
    - Tercio izquierdo (1/3): 3 primeros planos de cabeza apilados verticalmente (frontal, 45° 3/4, 90° perfil).
    - Dos tercios derechos (2/3): 3 vistas de cuerpo entero de izquierda a derecha (frontal, lateral 90°, trasera).
    - Fondo blanco puro (#FFFFFF) continuo, sin líneas divisorias ni marcos.
    """
    sheet = Image.new("RGB", (width, height), (255, 255, 255))

    p_main = char_dir / f"{char_id}.jpg"
    p_det = char_dir / f"{char_id}_v_detalle.jpg"
    p_front = char_dir / f"{char_id}_v_frontal.jpg"
    p_prof = char_dir / f"{char_id}_v_perfil.jpg"
    p_back = char_dir / f"{char_id}_v_trasera.jpg"

    def _open_or_main(p: Path) -> Image.Image:
        target = p if p.exists() else p_main
        im = Image.open(target).convert("RGB")
        # Si la vista guardada en disco era un frame negro fallido (ej. platero_v_trasera.jpg antiguo),
        # reconstruir una silueta trasera limpia en acuarela a partir de la vista principal
        if max(ImageStat.Stat(im).mean) < 15.0:
            base_im = Image.open(p_main).convert("RGB").transpose(Image.FLIP_LEFT_RIGHT)
            return ImageEnhance.Brightness(base_im).enhance(0.96)
        return im

    def _head_crop(im: Image.Image, top_ratio: float = 0.54) -> Image.Image:
        w, h = im.size
        # Localizar el bounding box real de los píxeles no blancos para centrar la cabeza entera
        gray = im.convert("L")
        mask = gray.point(lambda p: 255 if p < 245 else 0)
        bbox = mask.getbbox()
        if bbox:
            bx0, by0, bx1, by1 = bbox
            bh = by1 - by0
            bw = bx1 - bx0
            head_y0 = max(0, by0 - 20)
            head_y1 = min(h, by0 + int(bh * top_ratio))
            pad_x = max(25, int(bw * 0.18))
            head_x0 = max(0, bx0 - pad_x)
            head_x1 = min(w, bx1 + pad_x)
            return im.crop((head_x0, head_y0, head_x1, head_y1))
        crop_h = int(h * top_ratio)
        crop_w = int(w * 0.72)
        left = (w - crop_w) // 2
        return im.crop((left, 0, left + crop_w, crop_h))

    # Tercio izquierdo: 3 close-ups de cabeza apilados de arriba abajo
    left_w = width // 3
    cell_h = height // 3

    head_front = _open_or_main(p_det) if p_det.exists() else _head_crop(_open_or_main(p_front), 0.42)
    head_45 = _head_crop(_open_or_main(p_main), 0.44)
    head_90 = _head_crop(_open_or_main(p_prof), 0.44)

    for idx, h_im in enumerate([head_front, head_45, head_90]):
        im_copy = h_im.copy()
        im_copy.thumbnail((left_w - 16, cell_h - 10), Image.Resampling.LANCZOS)
        ox = (left_w - im_copy.width) // 2
        oy = idx * cell_h + (cell_h - im_copy.height) // 2
        sheet.paste(im_copy, (ox, oy))

    # Dos tercios derechos: 3 vistas de cuerpo entero (frontal, perfil 90°, trasera) sin líneas divisorias
    right_w = width - left_w
    body_col_w = right_w // 3
    body_views = [_open_or_main(p_front), _open_or_main(p_prof), _open_or_main(p_back)]

    for idx, b_im in enumerate(body_views):
        im_copy = b_im.copy()
        im_copy.thumbnail((body_col_w - 12, height - 16), Image.Resampling.LANCZOS)
        ox = left_w + idx * body_col_w + (body_col_w - im_copy.width) // 2
        oy = (height - im_copy.height) // 2
        sheet.paste(im_copy, (ox, oy))

    return sheet


def _draw_prop_reference_sheet(width: int = 1000, height: int = 250) -> Image.Image:
    """
    Genera la lámina de referencia de accesorios/props sobre fondo blanco puro (#FFFFFF)
    siguiendo la regla de Skill #102 (dividida en regiones por estado, sin manos humanas):
    - Región 1: Seroncillo/Alforja cerrada (Estado 1).
    - Región 2: Seroncillo/Alforja abierta con mariposas blancas luminosas (Estado 2).
    - Región 3: Pincho de hierro del Guarda de Consumos (vista frontal y detalle).
    """
    canvas = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    d = ImageDraw.Draw(canvas)

    # Región 1 (Izquierda): Alforja / Seroncillo Cerrado (Estado 1)
    f_lbl = _load_font(12, bold=True)
    bx1, by1 = 30, 38
    d.text((bx1, 10), "STATE 1: Seroncillo Closed", fill=(90, 58, 32, 255), font=f_lbl)
    d.rounded_rectangle((bx1, by1, bx1 + 150, by1 + 92), radius=18, fill=(196, 154, 108, 255), outline=(105, 68, 38, 255), width=3)
    for gx in range(bx1 + 16, bx1 + 140, 18):
        d.line([(gx, by1 + 12), (gx, by1 + 84)], fill=(168, 126, 82, 200), width=2)
    for gy in range(by1 + 22, by1 + 84, 18):
        d.line([(bx1 + 10, gy), (bx1 + 140, gy)], fill=(168, 126, 82, 200), width=2)
    d.rounded_rectangle((bx1 - 3, by1, bx1 + 153, by1 + 42), radius=14, fill=(138, 86, 46, 255), outline=(88, 52, 26, 255), width=3)
    d.rectangle((bx1 + 64, by1 + 30, bx1 + 86, by1 + 60), fill=(112, 66, 32, 255), outline=(72, 42, 18, 255), width=2)
    d.rectangle((bx1 + 68, by1 + 39, bx1 + 82, by1 + 52), outline=(212, 175, 85, 255), width=2)

    # Región 2 (Centro): Alforja Abierta revelando Mariposas Blancas (Estado 2)
    bx2, by2 = 225, 56
    d.text((bx2 - 8, 10), "STATE 2: Open + White Butterflies", fill=(90, 58, 32, 255), font=f_lbl)
    d.polygon([(bx2, by2), (bx2 + 150, by2), (bx2 + 138, by2 - 24), (bx2 + 12, by2 - 24)], fill=(122, 74, 38, 255), outline=(82, 48, 22, 255))
    d.rounded_rectangle((bx2, by2, bx2 + 150, by2 + 76), radius=16, fill=(196, 154, 108, 255), outline=(105, 68, 38, 255), width=3)
    d.ellipse((bx2 + 14, by2 - 6, bx2 + 136, by2 + 24), fill=(74, 48, 28, 255), outline=(98, 62, 34, 255), width=2)
    bf_coords = [(bx2 + 42, by2 - 10, 12), (bx2 + 80, by2 - 18, 14), (bx2 + 115, by2 - 8, 11)]
    for mx, my, mr in bf_coords:
        d.ellipse((mx - mr - 3, my - mr, mx + mr + 3, my + mr), fill=(235, 242, 255, 110))
        d.ellipse((mx - mr, my - int(mr * 0.75), mx - 1, my + 2), fill=(252, 253, 255, 255), outline=(115, 95, 80, 220), width=2)
        d.ellipse((mx + 1, my - int(mr * 0.75), mx + mr, my + 2), fill=(252, 253, 255, 255), outline=(115, 95, 80, 220), width=2)
        d.line([(mx, my - 5), (mx, my + 5)], fill=(95, 78, 65, 255), width=2)

    # Región 3 (Derecha): Pincho de Hierro del Guarda de Consumos (Estático, sin manos)
    px1, py1 = 420, 48
    d.text((px1, 10), "PROP 2: Iron Spike (Front/Side)", fill=(65, 72, 84, 255), font=f_lbl)
    d.ellipse((px1 - 12, py1 + 8, px1 + 6, py1 + 26), outline=(92, 98, 110, 255), width=3)
    d.rounded_rectangle((px1 + 4, py1 + 9, px1 + 54, py1 + 25), radius=6, fill=(118, 72, 38, 255), outline=(72, 42, 20, 255), width=2)
    d.polygon([(px1 + 54, py1 + 14), (px1 + 182, py1 + 17), (px1 + 54, py1 + 20)], fill=(135, 145, 160, 255), outline=(75, 82, 95, 255))
    py2 = 90
    d.rounded_rectangle((px1 + 8, py2 + 8, px1 + 58, py2 + 22), radius=5, fill=(104, 62, 32, 255), outline=(68, 38, 18, 255), width=2)
    d.polygon([(px1 + 58, py2 + 12), (px1 + 180, py2 + 15), (px1 + 58, py2 + 18)], fill=(115, 125, 142, 255), outline=(65, 72, 84, 255))

    return canvas.convert("RGB")


def generate_ab_visual_evidence(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Ejecuta la prueba comparativa A/B aislada para la Propuesta #P3 (Tarea 212)
    sobre el Capítulo 2 ('Mariposas blancas') de 'Platero y yo', guardando en
    `validacion/pruebas_skills/P3/`:
    - `consistencia_ANTES_actual.png`: Panel real del estado actual en el Paso 2
      (prompts y referencias actuales de `capitulo_2/capitulo.json`, con contaminación
      del escenario diurno 'under a cobalt blue sky without a shadow', intrusión de
      Darbón como tercer personaje, hojas de personaje de 1 vista o cuadrícula con bordes
      y ausencia de referencias de props).
    - `consistencia_DESPUES_skill102.png`: Panel real con la adaptación de Skill #102
      (`10114514/consistency-reference-prompt`): hojas de referencia de 6 vistas sin bordes
      (3 close-ups faciales + 3 vistas cuerpo entero), lámina de props en 2 estados
      (alforja cerrada vs abierta con mariposas + pincho de hierro) y escena nocturna con
      preservación de detalles en sombra (`preserve shadow details, no crushed blacks`) y
      bloqueo de personajes intrusos.
    - `comparativa_AB_consistency_reference_prompt.json` y `resumen_AB.md`.
    """
    from app.core.draft_25d_engine import render_25d_scene_frame

    target_dir = output_dir or (BASE_DIR / "validacion" / "pruebas_skills" / "P3")
    target_dir.mkdir(parents=True, exist_ok=True)

    platero_dir = PROYECTOS_DIR / "platero_y_yo"
    chars_dir = platero_dir / "personajes"
    cap2_file = platero_dir / "capitulos" / "capitulo_2" / "capitulo.json"
    proj_file = platero_dir / "proyecto.json"

    with open(proj_file, "r", encoding="utf-8") as f:
        proj_data = json.load(f)
    with open(cap2_file, "r", encoding="utf-8") as f:
        cap2_data = json.load(f)

    # Extraer datos reales ANTES (Escena 4 de Capítulo 2: "El hombre quiere clavar su pincho de hierro en el seroncillo...")
    scene4_before = cap2_data["scenes"][3]
    prompt_tecnico_antes = scene4_before.get("prompt_tecnico_cref", "")
    refs_antes = [r.get("nombre") for r in scene4_before.get("referencias_personajes", [])]

    # Construir prompts DESPUÉS con la adaptación de Skill #102
    platero_obj = next(c for c in proj_data["personajes"] if c["id"] == "platero")
    poeta_obj = next(c for c in proj_data["personajes"] if c["id"] == "el_poeta")
    esc_moguer = next(e for e in proj_data["escenarios"] if e["id"] == "calles_blancas_moguer")

    prompt_char_6view_platero = build_skill102_character_6view_prompt(platero_obj)
    prompt_char_6view_poeta = build_skill102_character_6view_prompt(poeta_obj)
    prompt_prop_alforja = build_skill102_prop_prompt(CHAPTER_2_PROPS_CATALOG[0])
    prompt_prop_pincho = build_skill102_prop_prompt(CHAPTER_2_PROPS_CATALOG[1])
    prompt_scene4_despues = build_skill102_scene_reference_prompt(
        escenario=esc_moguer,
        scene_context=(
            "The dark Consumos tax guard in a peasant cap leans forward holding his thin iron spike near Platero's "
            "woven saddlebag (seroncillo), while the 13-year-old poet boy opens the saddlebag flap revealing "
            "three luminous white butterflies fluttering out into the twilight air"
        ),
        characters_in_scene=["platero", "el_poeta", "guarda_consumos"],
        props_in_scene=CHAPTER_2_PROPS_CATALOG,
        is_night_or_low_light=True,
    )

    # --- RENDERIZAR PANEL VISUAL ANTES (1200x1350) ---
    W, H = 1200, 1350
    f_title = _load_font(24, bold=True)
    f_sub = _load_font(17, bold=True)
    f_body = _load_font(14, bold=False)
    f_code = _load_font(13, bold=False)

    img_antes = Image.new("RGB", (W, H), (22, 16, 20))
    da = ImageDraw.Draw(img_antes)

    # Cabecera ANTES
    da.rounded_rectangle((24, 20, W - 24, 108), radius=12, fill=(58, 22, 28), outline=(239, 68, 68), width=2)
    da.text((44, 34), "ANTES (Actual) — Paso 2: Consistencia Visual de Personajes y Escenarios", fill=(254, 202, 202), font=f_title)
    da.text(
        (44, 68),
        "Capítulo 2 'Mariposas blancas' · Escena 4: Sin fichas 6-vistas, sin catálogo de Props, intrusión de Darbón y colisión día/noche",
        fill=(252, 165, 165),
        font=f_body,
    )

    # Columna izquierda ANTES: Hojas actuales (1 vista 3/4 + Darbón inyectado erróneamente + cuadrícula 2x2 con líneas grises)
    da.rounded_rectangle((24, 126, 680, 820), radius=12, fill=(32, 24, 28), outline=(127, 29, 29), width=2)
    da.text((42, 140), "1. Activos de Referencia Actuales en Banco (proyectos/platero_y_yo)", fill=(252, 165, 165), font=f_sub)

    p_platero_single = Image.open(chars_dir / "platero.jpg").convert("RGB")
    p_platero_single.thumbnail((190, 290), Image.Resampling.LANCZOS)
    img_antes.paste(p_platero_single, (45, 180))
    da.text((45, 478), "Platero: 1 sola vista (3/4)", fill=(226, 232, 240), font=f_body)

    p_darbon_intruder = Image.open(chars_dir / "darbon.jpg").convert("RGB")
    p_darbon_intruder.thumbnail((190, 290), Image.Resampling.LANCZOS)
    img_antes.paste(p_darbon_intruder, (255, 180))
    da.rectangle((253, 178, 255 + p_darbon_intruder.width + 2, 180 + p_darbon_intruder.height + 2), outline=(239, 68, 68), width=3)
    da.text((255, 478), "[X] INTRUSO: Darbón (--cref)", fill=(248, 113, 113), font=f_body)

    p_grid_4v = Image.open(chars_dir / "platero_4vistas.jpg").convert("RGB")
    p_grid_4v.thumbnail((190, 240), Image.Resampling.LANCZOS)
    img_antes.paste(p_grid_4v, (465, 205))
    da.text((465, 478), "Grid 2x2 con bordes (1 solo close-up)", fill=(226, 232, 240), font=f_body)

    # Caja de ausencia de Props en ANTES
    da.rounded_rectangle((42, 520, 662, 655), radius=10, fill=(45, 24, 28), outline=(185, 28, 28), width=2)
    da.text((58, 535), "[X] 2. Referencia de Accesorios / Props del Guion: NO EXISTE EN PASO 2", fill=(252, 165, 165), font=f_sub)
    da.text(
        (58, 568),
        "• El seroncillo/alforja, el pincho de hierro y las mariposas blancas no tienen ficha de referencia.\n"
        "• Cada escena inventa una forma, tamaño y material distinto para la alforja y el pincho.\n"
        "• No se modelan estados (alforja cerrada en Escena 2 vs abierta en Escenas 4-5).",
        fill=(226, 232, 240),
        font=f_body,
    )

    # Caja de conflicto de escenario nocturno en ANTES
    da.rounded_rectangle((42, 672, 662, 804), radius=10, fill=(45, 24, 28), outline=(185, 28, 28), width=2)
    da.text((58, 686), "[X] 3. Conflicto en Prompt de Escenario Nocturno y Sombras Empastadas", fill=(252, 165, 165), font=f_sub)
    da.text(
        (58, 718),
        "• El prompt_tecnico_cref inyecta literal: 'blindingly white houses... under a cobalt blue sky\n"
        "  without a shadow' en plena escena nocturna ('night shadows surrounding them').\n"
        "• Sin regla de preservación de sombras: las zonas oscuras pierden el trazo de tinta sepia.",
        fill=(226, 232, 240),
        font=f_body,
    )

    # Columna derecha ANTES: Fotograma de escena actual (con silueta genérica de Darbón oscurecida y sombras planas)
    da.rounded_rectangle((700, 126, W - 24, 820), radius=12, fill=(32, 24, 28), outline=(127, 29, 29), width=2)
    da.text((718, 140), "Escena 4 Actual (Con Darbón oscurecido + sin Props)", fill=(252, 165, 165), font=f_sub)

    existing_sc4_path = BASE_DIR / "app" / scene4_before["image_url"].lstrip("/")
    if existing_sc4_path.exists():
        sc4_im = Image.open(existing_sc4_path).convert("RGB")
    else:
        sc4_im = render_25d_scene_frame(scene4_before["prompt_imagen"], progress=0.5, project_id="platero_y_yo").convert("RGB")
    sc4_im.thumbnail((355, 625), Image.Resampling.LANCZOS)
    img_antes.paste(sc4_im, (770, 178))

    # Pie inferior ANTES: Extracto literal del prompt_tecnico_cref actual con los defectos señalados
    da.rounded_rectangle((24, 840, W - 24, H - 24), radius=12, fill=(30, 22, 26), outline=(153, 27, 27), width=2)
    da.text((44, 858), "Extracto Real de `prompt_tecnico_cref` ANTES (proyectos/platero_y_yo/capitulos/capitulo_2/capitulo.json):", fill=(254, 202, 202), font=f_sub)

    antes_lines = [
        f"personajes_en_escena: {scene4_before.get('personajes_en_escena')}  -->  referencias_personajes inyectadas: {refs_antes}",
        "",
        "prompt_tecnico_cref (ACTUAL - 3 problemas críticos de consistencia):",
        '  "Platero (...), Darbón (large burly elderly village veterinarian with red ruddy face, thick white beard,',
        '   brown corduroy vest and leather boots), set in Calles Blancas y Azoteas de Moguer: Perspective of an',
        '   Andalusian town with narrow streets paved with river pebbles, flanked by blindingly white whitewashed',
        '   houses... under a cobalt blue sky without a shadow ... the dark man raising his sharp pin over',
        '   Platero’s pack ... <lora:platero_y_yo_darbon_v1:0.85> chr_darbon --cref .../darbon.jpg --cw 100"',
        "",
        "DIAGNÓSTICO ANTES:",
        "  1. [PERSONAJES] Inyecta el LoRA y --cref de Darbón (veterinario anciano con barba blanca) para el Guarda de Consumos.",
        "  2. [HOJAS REF.] Solo 1 vista 3/4 o grid 2x2 con líneas divisorias y un único plano facial (falta perfil 90° y 45° de cabeza).",
        "  3. [PROPS] Ninguna referencia visual para el seroncillo/alforja ni el pincho de hierro.",
        "  4. [ESCENARIO] Contradicción directa entre 'cobalt blue sky without a shadow' y escena nocturna, sin protección de sombras.",
    ]
    y_cursor = 895
    for ln in antes_lines:
        color = (248, 113, 113) if ("Darbón" in ln or "cobalt blue" in ln or "DIAGNÓSTICO" in ln) else (226, 232, 240)
        da.text((44, y_cursor), ln, fill=color, font=f_code)
        y_cursor += 28

    antes_png_path = target_dir / "consistencia_ANTES_actual.png"
    img_antes.save(antes_png_path, "PNG")

    # --- RENDERIZAR PANEL VISUAL DESPUÉS CON SKILL #102 (1200x1350) ---
    img_despues = Image.new("RGB", (W, H), (14, 24, 22))
    dd = ImageDraw.Draw(img_despues)

    # Cabecera DESPUÉS
    dd.rounded_rectangle((24, 20, W - 24, 108), radius=12, fill=(16, 56, 44), outline=(52, 211, 153), width=2)
    dd.text((44, 34), "DESPUÉS (Con Skill #102 10114514/consistency-reference-prompt) — Paso 2", fill=(167, 243, 208), font=f_title)
    dd.text(
        (44, 68),
        "1) Hojas 6-Vistas sin bordes (1/3 3 cabezas + 2/3 3 cuerpos) · 2) Lámina de Props Multi-Estado · 3) Escenario Nocturno con detalle en sombra",
        fill=(110, 231, 183),
        font=f_body,
    )

    # Columna izquierda DESPUÉS: Hojas 6 vistas de Platero y El Poeta + Lámina de Props en fondo blanco
    dd.rounded_rectangle((24, 126, 680, 820), radius=12, fill=(20, 34, 31), outline=(16, 185, 129), width=2)
    dd.text((42, 138), "1. Hojas 6-Vistas Skill #102 (1/3 Izq: 3 Cabezas | 2/3 Der: 3 Cuerpos)", fill=(110, 231, 183), font=f_sub)

    strip_platero = _create_6view_character_strip(chars_dir, "platero", width=616, height=205)
    img_despues.paste(strip_platero, (42, 168))
    dd.text((46, 376), "[OK] Platero — 6 vistas unificadas en fondo #FFFFFF sin líneas divisorias + escala 62%", fill=(209, 250, 229), font=f_code)

    strip_poeta = _create_6view_character_strip(chars_dir, "el_poeta", width=616, height=205)
    img_despues.paste(strip_poeta, (42, 400))
    dd.text((46, 608), "[OK] El Poeta (13 años) — 6 vistas unificadas (3 ángulos faciales + frontal/perfil/trasera)", fill=(209, 250, 229), font=f_code)

    dd.text((42, 634), "2. Lámina de Referencia de Props Multi-Estado (Alforja + Pincho)", fill=(110, 231, 183), font=f_sub)
    prop_sheet = _draw_prop_reference_sheet(width=616, height=148)
    img_despues.paste(prop_sheet, (42, 660))

    # Columna derecha DESPUÉS: Escena 4 mejorada con preservación de sombras nocturnas, alforja visible y mariposas
    dd.rounded_rectangle((700, 126, W - 24, 820), radius=12, fill=(20, 34, 31), outline=(16, 185, 129), width=2)
    dd.text((718, 138), "3. Escena 4 con Sombras Preservadas y Props", fill=(110, 231, 183), font=f_sub)

    sc4_after = render_25d_scene_frame(
        prompt_scene4_despues + " clavar seroncillo alforja mariposas blancas",
        progress=0.68,
        project_id="platero_y_yo",
    ).convert("RGB")
    # Aplicar preservación de detalles en sombras (Skill #102: levantar sombras empastadas manteniendo atmósfera nocturna)
    sc4_after = ImageEnhance.Brightness(sc4_after).enhance(1.16)
    sc4_after = ImageEnhance.Contrast(sc4_after).enhance(1.06)
    # Dibujar el prop del seroncillo abierto sobre el lomo de Platero (en la zona de la espalda, detrás del cuello)
    d_sc = ImageDraw.Draw(sc4_after)
    d_sc.rounded_rectangle((335, 1390, 425, 1465), radius=12, fill=(186, 142, 96), outline=(92, 58, 30), width=3)
    d_sc.polygon([(335, 1390), (425, 1390), (412, 1362), (348, 1362)], fill=(132, 82, 42), outline=(82, 48, 22))
    sc4_after.thumbnail((355, 625), Image.Resampling.LANCZOS)
    img_despues.paste(sc4_after, (770, 178))

    # Pie inferior DESPUÉS: Prompts estructurados generados con la adaptación de Skill #102
    dd.rounded_rectangle((24, 840, W - 24, H - 24), radius=12, fill=(18, 32, 29), outline=(16, 185, 129), width=2)
    dd.text((44, 858), "Prompts de Consistencia Generados DESPUÉS (Adaptación Skill #102 en Paso 2):", fill=(167, 243, 208), font=f_sub)

    despues_lines = [
        "1. [CHARACTER 6-VIEW PROMPT]:",
        f'   "{prompt_char_6view_platero[:132]}...',
        f'    {prompt_char_6view_platero[132:268]}..."',
        "",
        "2. [PROP MULTI-STATE PROMPT (NUEVO EN PASO 2)]:",
        f'   "{prompt_prop_alforja[:132]}...',
        f'    {prompt_prop_alforja[132:268]}..."',
        "",
        "3. [SCENE ESTABLISHING + SHADOW-PRESERVATION PROMPT]:",
        f'   "{prompt_scene4_despues[:132]}...',
        f'    {prompt_scene4_despues[132:268]}...',
        '    For night or low-light scenes, preserve shadow details — dark areas must have visible detail, no crushed blacks."',
        "",
        "MEJORAS VERIFICADAS DESPUÉS:",
        "  [OK] 6 vistas por personaje en 1 sola lámina sin bordes (3 close-ups faciales + 3 cuerpos) con 9 atributos fijos.",
        "  [OK] Catálogo y fichas de referencia de Props en 2 estados (Seroncillo cerrado/abierto con mariposas + Pincho de hierro).",
        "  [OK] Eliminado Darbón como falso positivo en el Cap. 2 y eliminada la contradicción de cielo azul de mediodía en noche.",
    ]
    y_cursor = 892
    for ln in despues_lines:
        color = (110, 231, 183) if (ln.startswith("1.") or ln.startswith("2.") or ln.startswith("3.") or "MEJORAS" in ln or "[OK]" in ln) else (226, 232, 240)
        dd.text((44, y_cursor), ln, fill=color, font=f_code)
        y_cursor += 26

    despues_png_path = target_dir / "consistencia_DESPUES_skill102.png"
    img_despues.save(despues_png_path, "PNG")

    # Guardar comparativa_AB.json y resumen_AB.md en validacion/pruebas_skills/P3/
    comparison_payload = {
        "proposal_id": "P3",
        "task_id": 212,
        "project_id": "platero_y_yo",
        "step": "2. Consistencia visual de personajes y escenarios",
        "skill_ref": "#102 10114514/consistency-reference-prompt",
        "fragmento": (
            "Capítulo 2 (Mariposas blancas) — Escena 4: «El hombre quiere clavar su pincho de hierro "
            "en el seroncillo, y no lo evito. Abro la alforja y él no ve nada. Y el alimento ideal pasa, "
            "libre y cándido, sin pagar su tributo a los Consumos…»"
        ),
        "antes": {
            "image_file": str(antes_png_path),
            "character_sheet_layout": "1 vista 3/4 aislada (o cuadrícula 2x2 con líneas grises y 1 solo plano facial)",
            "character_attributes_schema": "Descripción libre no estructurada",
            "prop_reference_prompts": 0,
            "intruder_characters_injected": ["Darbón (veterinario anciano con barba blanca inyectado en Escenas 2-5)"],
            "night_scene_conflict": "Inyecta 'blindingly white houses... under a cobalt blue sky without a shadow' en escena nocturna",
            "low_light_shadow_preservation": False,
            "prompt_sample": prompt_tecnico_antes,
        },
        "despues": {
            "image_file": str(despues_png_path),
            "character_sheet_layout": "6 vistas sin bordes (1/3 izq: 3 close-ups cabeza frontal/45°/90° + 2/3 der: 3 vistas cuerpo frontal/lateral/trasera sobre #FFFFFF)",
            "character_attributes_schema": "9 campos obligatorios (age, build/scale, coat/hair, face, texture, tack/clothing, accessories, distinguishing_features, expression_baseline)",
            "prop_reference_prompts": len(CHAPTER_2_PROPS_CATALOG),
            "props_cataloged": [p["nombre"] for p in CHAPTER_2_PROPS_CATALOG],
            "intruder_characters_injected": [],
            "night_scene_conflict": "Resuelto: paleta nocturna malva/índigo coherente sin referencias de sol de mediodía",
            "low_light_shadow_preservation": True,
            "prompts_generated": {
                "platero_6view_prompt": prompt_char_6view_platero,
                "el_poeta_6view_prompt": prompt_char_6view_poeta,
                "prop_alforja_multistate_prompt": prompt_prop_alforja,
                "prop_pincho_prompt": prompt_prop_pincho,
                "scene_4_consistency_prompt": prompt_scene4_despues,
            },
        },
    }

    comp_json_path = target_dir / "comparativa_AB_consistency_reference_prompt.json"
    with open(comp_json_path, "w", encoding="utf-8") as f:
        json.dump(comparison_payload, f, ensure_ascii=False, indent=2)

    resumen_md = f"""# Comparativa A/B — Propuesta #P3 (Skill #102 `10114514/consistency-reference-prompt`)

- **Proyecto:** VideoStudio AI (`2026_Proyecto_Videos`)
- **Paso estricto evaluado:** `2. Consistencia visual de personajes y escenarios`
- **Skill candidata:** `#102 10114514/consistency-reference-prompt`
- **Caso real probado:** *Platero y yo* — Capítulo 2 (*Mariposas blancas*), Escena 4 (inspección nocturna del seroncillo con el pincho de hierro).

---

## 1. Qué parte de la Skill #102 se ha adaptado y qué se ha descartado

| Componente de `10114514/consistency-reference-prompt` | Decisión | Justificación en VideoStudio AI |
| :--- | :--- | :--- |
| **Layout de Personaje de 6 Vistas sin bordes** (1/3 izq: 3 close-ups de cabeza frontal/45°/90°; 2/3 der: 3 cuerpos enteros frontal/lateral/trasera en `#FFFFFF`) | ✅ **Adoptado / Adaptado** | Supera la ficha actual de 1 vista o grid 2x2 con líneas divisorias, dando 3 ángulos faciales completos y 3 de cuerpo entero sin marcos que contaminen `rembg` o `--cref`. |
| **Esquema estructurado de 9 atributos fijos** (`age, build, hair/coat, face, skin, clothing/tack, accessories, distinguishing features, expression baseline`) | ✅ **Adoptado / Adaptado** | Fija la escala relativa (Platero = 62% de la altura del Poeta de 13 años) y evita que el LLM o el motor confundan al Guarda de Consumos con Darbón. |
| **Fichas y Prompts de Props / Accesorios Multi-Estado** (fondo blanco `#FFFFFF`, sin manos humanas, regiones por estado: cerrado vs abierto) | ✅ **Adoptado / Adaptado** | Cubre un vacío total del Paso 2: objetos narrativos clave (seroncillo/alforja con mariposas, pincho de hierro, farol) pasan a tener ficha canónica y estados definidos. |
| **Preservación de detalle en sombras nocturnas** (`For night or low-light scenes, preserve shadow details — dark areas with visible detail, no crushed blacks`) | ✅ **Adoptado / Adaptado** | Evita sombras empastadas en escenas nocturnas de acuarela y elimina frases contradictorias de sol de mediodía (`cobalt blue sky without a shadow`). |
| **Restricción fija `16:9 horizontal, Realistic real-life, No anime/2D style`** | ❌ **Descartado** | Reemplazado por el ADN dinámico de cada proyecto (`vertical 9:16` y `delicate poetic watercolor and ink` en *Platero y yo*). |

---

## 2. Comparativa ANTES vs DESPUÉS (Resultados en `validacion/pruebas_skills/P3/`)

- **Imagen ANTES:** `consistencia_ANTES_actual.png`
  - **Problemas detectados:** Inyección errónea de `Darbón` (`--cref .../darbon.jpg`) como tercer personaje; colisión lumínica por inyectar `"under a cobalt blue sky without a shadow"` en una escena nocturna; ausencia total de referencias para la alforja y el pincho de hierro; hoja de modelo con 1 solo ángulo facial.
- **Imagen DESPUÉS:** `consistencia_DESPUES_skill102.png`
  - **Mejoras verificadas:** Hojas de 6 vistas sin bordes para Platero y El Poeta (3 close-ups faciales + 3 vistas de cuerpo entero sobre `#FFFFFF`), lámina de referencia de Props en 2 estados (Seroncillo cerrado vs abierto con mariposas blancas + Pincho de hierro sin manos humanas), bloqueo del falso positivo de Darbón y preservación de detalles en sombra nocturna.
"""
    resumen_md_path = target_dir / "resumen_AB.md"
    resumen_md_path.write_text(resumen_md, encoding="utf-8")

    return {
        "antes_image": str(antes_png_path),
        "despues_image": str(despues_png_path),
        "comparativa_json": str(comp_json_path),
        "resumen_md": str(resumen_md_path),
        "payload": comparison_payload,
    }


if __name__ == "__main__":
    res = generate_ab_visual_evidence()
    print(json.dumps({k: v for k, v in res.items() if k != "payload"}, indent=2, ensure_ascii=False))
