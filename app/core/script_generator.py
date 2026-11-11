import os
import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROYECTOS_DIR = BASE_DIR / "proyectos"

STYLE_PRESETS = {
    "cinematic": "cinematic lighting, photorealistic 8k, shot on 35mm lens, atmospheric depth of field, dramatic shadows",
    "noir_bw": "black and white film noir photography, dramatic high contrast monochrome, sharp shadows, moody lighting, classic monochrome 35mm film",
    "anime": "anime aesthetic, Makoto Shinkai style, vibrant colors, beautiful sky, high quality anime screencap, trending on Pixiv",
    "ghibli_anime": "Studio Ghibli aesthetic, Hayao Miyazaki hand-drawn anime, painterly backgrounds, warm nostalgic feel, whimsical art",
    "watercolor": "delicate watercolor and ink illustration, soft artistic color washes, storybook illustration, rich paper texture",
    "storybook_kids": "whimsical children's book illustration, vibrant friendly colors, charming storybook character art, soft lighting, family friendly, highly detailed",
    "pixar_3d": "3D animated movie render, Pixar Disney style, soft volumetric subsurface scattering, expressive character facial features, 4k 8k",
    "dark_fantasy": "dark fantasy, hyperdetailed, grimdark aesthetic, ominous lighting, mystical atmosphere, concept art, Unreal Engine 5 render",
    "cyberpunk": "cyberpunk style, neon lights, rainy reflection, high tech dystopian, blade runner aesthetic, volumetric glow",
    "vintage": "vintage 1970s film grain, warm Kodak Portra color tones, nostalgic, retro photography, authentic cinematic texture",
    "comic": "graphic novel comic illustration, bold ink lines, dynamic comic book shading, expressive colors, Frank Miller style"
}

def clean_json_string(raw: str) -> str:
    """Extrae y limpia bloques de código JSON devueltos por LLMs."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw

def compute_character_seed(char_id: str, project_id: str = "") -> int:
    """Calcula una semilla determinista estable para un personaje del banco de consistencia."""
    raw_key = f"{project_id}:{char_id}".lower().strip(":")
    digest = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
    return (int(digest[:8], 16) % 900000) + 100000

def load_character_bank_for_prompt_generator(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Permite al generador de prompts acceder directamente a las hojas de referencia guardadas
    en el Banco de Consistencia de Personajes (por proyecto o en el banco global en disco).
    """
    characters: List[Dict[str, Any]] = []
    if not PROYECTOS_DIR.exists():
        return characters

    target_dirs = []
    if project_id:
        cand = PROYECTOS_DIR / project_id
        if cand.exists() and cand.is_dir():
            target_dirs.append(cand)
        else:
            for d in PROYECTOS_DIR.iterdir():
                if d.is_dir() and d.name.lower() == project_id.lower():
                    target_dirs.append(d)
                    break
    else:
        target_dirs = [d for d in PROYECTOS_DIR.iterdir() if d.is_dir()]

    for folder in target_dirs:
        cat_file = folder / "personajes" / "catalogo_consistencia.json"
        meta_file = folder / "proyecto.json"
        if cat_file.exists():
            try:
                with open(cat_file, "r", encoding="utf-8") as f:
                    cat_data = json.load(f)
                if isinstance(cat_data.get("personajes"), list) and len(cat_data["personajes"]) > 0:
                    characters.extend(cat_data["personajes"])
                    continue
            except Exception:
                pass
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                for c in p_data.get("personajes", []):
                    c_copy = dict(c)
                    c_id = c_copy.get("id") or "char"
                    personajes_dir = folder / "personajes"
                    img_jpg = personajes_dir / f"{c_id}.jpg"
                    img_png = personajes_dir / f"{c_id}.png"
                    if not c_copy.get("imagen_url"):
                        if img_jpg.exists():
                            c_copy["imagen_url"] = f"/proyectos_data/{folder.name}/personajes/{img_jpg.name}"
                        elif img_png.exists():
                            c_copy["imagen_url"] = f"/proyectos_data/{folder.name}/personajes/{img_png.name}"
                    characters.append(c_copy)
            except Exception:
                pass
    return characters

def extract_character_visual_anchor(character: Dict[str, Any]) -> str:
    """
    Extrae la cápsula de identidad física inmutable en inglés de un personaje
    para anclar firmemente la coherencia visual de la escena, sin incluir
    instrucciones de hoja de modelo (turnaround/views/background).
    """
    name = character.get("nombre", "Character").strip()
    tipo = character.get("tipo", "humano").lower().strip()
    desc = character.get("descripcion_visual", "").strip()
    prompt_ret = character.get("prompt_retrato", "").strip()

    if character.get("ancla_visual") and str(character.get("ancla_visual")).strip():
        anchor_text = str(character["ancla_visual"]).strip()
        if anchor_text.lower().startswith(name.lower()):
            return anchor_text
        return f"{name} ({anchor_text})"

    lower_name = name.lower()
    lower_desc = desc.lower()

    # Anclas canónicas predefinidas de máxima fidelidad para los universos del estudio
    if "platero" in lower_name or "burro" in lower_desc or "donkey" in lower_desc:
        return f"{name} (small fluffy silver-grey Andalusian donkey with gentle dark crystal black eyes and soft cotton-like coat, quadruped donkey on all four legs, authentic donkey anatomy, no humans)"
    elif "poeta" in lower_name or ("narrador" in lower_name and "moguer" in lower_desc):
        return f"{name} (young contemplative 13-year-old Spanish writer from Moguer, sensitive noble face, dark wavy hair, wearing a rustic raw linen shirt, dark wool waistcoat, and wide-brim Andalusian hat)"
    elif "diana" in lower_name:
        return f"{name} (agile slender graceful pure white Andalusian dog resembling a crescent moon, pure white silky coat, lively alert ears, amber eyes, quadruped on all four legs)"
    elif "darbon" in lower_name or "darbón" in lower_name:
        return f"{name} (large burly elderly village veterinarian with red ruddy face, thick white beard, brown corduroy vest and leather boots)"
    elif "lord" in lower_name:
        return f"{name} (old noble English greyhound dog, melancholic wise eyes, lean ribs visible beneath an aged brindle grey coat, grey fur around muzzle, quadruped canine on all four legs)"
    elif "canario" in lower_name:
        return f"{name} (tiny singing canary bird, radiant emerald green plumage with fresh lemon-yellow highlights, small shiny seed-like eyes, delicate beak, winged avian bird anatomy)"
    elif "niña chica" in lower_name or "nina chica" in lower_name:
        return f"{name} (petite angelic young Andalusian girl from Moguer, rosy cheeks, braided blonde hair with ribbons, wearing rustic percale dress and white ruffled apron)"
    elif "anilla" in lower_name:
        return f"{name} (Andalusian flamenco dancer woman, warm tanned skin, sparkling dark ember eyes, wavy black hair with comb, colorful ruffled layered flamenco dress and Manila shawl)"
    elif "principito" in lower_name or "little prince" in lower_desc:
        return f"{name} (small young boy with tousled golden blonde hair, long flowing golden-yellow scarf in the wind, teal-blue prince coat with red lapels and soft boots)"
    elif "zorro" in lower_name:
        return f"{name} (slender graceful desert fox with vibrant golden-orange fur, fluffy white chest and white-tipped bushy tail, expressive wise almond eyes, standing on all four paws)"
    elif "aviador" in lower_name:
        return f"{name} (1930s pioneering desert aviator in worn brown leather flight jacket, canvas aviator cap with brass goggles on forehead, warm compassionate gaze)"
    elif "lucas" in lower_name:
        return f"{name} (25-year-old handsome coastal lighthouse keeper, wind-tousled brown hair, determined gaze, wearing a bright yellow waterproof slicker raincoat and holding a vintage brass lantern)"
    elif "marina" in lower_name:
        return f"{name} (ethereal ocean guardian maiden, long wavy sea-blue hair, deep turquoise eyes, wearing a flowing translucent sea-green dress with luminescent oceanic accents)"

    if prompt_ret:
        cleaned = re.sub(
            r"^(?:Character turnaround model sheet|Turnaround model sheet|Character model sheet|Full body character turnaround model sheet|Character concept art of|Full body character design of)[^,.:]+[,.:]\s*",
            "",
            prompt_ret,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"(?:four distinct full-body turnaround views|four distinct views|multiple views|front view|three-quarters|rear back view|rear view|isolated on solid|completely isolated on solid|isolated on plain|standing pose).*$",
            "",
            cleaned,
            flags=re.IGNORECASE
        ).strip().strip(",; ")
        if len(cleaned) > 20:
            return f"{name} ({cleaned[:180]})"

    if tipo == "animal":
        return f"{name} ({desc[:90]}, standing naturally on all four legs, authentic animal anatomy)"
    else:
        return f"{name} ({desc[:90]}, consistent character appearance)"

def get_character_consistency_tokens(
    character: Dict[str, Any],
    project_id: str = "",
    include_cref: bool = True,
    include_lora: bool = True
) -> Dict[str, Any]:
    """
    Construye los descriptores y directivas técnicas del Banco de Consistencia (--cref / LoRA)
    para un personaje catalogado.
    """
    char_id = character.get("id") or re.sub(r"\W+", "_", character.get("nombre", "char").lower()).strip("_")
    char_name = character.get("nombre", char_id).strip()
    img_url = character.get("imagen_url") or character.get("cref_url")
    clean_img_url = img_url.split("?")[0] if img_url else None

    # Verificar ruta física en disco si pertenece a /proyectos_data/
    file_path = character.get("hoja_referencia_path")
    file_exists = False
    if clean_img_url and clean_img_url.startswith("/proyectos_data/"):
        rel_part = clean_img_url[len("/proyectos_data/"):]
        abs_candidate = PROYECTOS_DIR / rel_part
        if abs_candidate.exists():
            file_exists = True
            file_path = f"proyectos/{rel_part}"
    elif file_path:
        abs_candidate = BASE_DIR / file_path
        if abs_candidate.exists():
            file_exists = True
            if not clean_img_url:
                rel_p = str(file_path).replace("\\", "/")
                if rel_p.startswith("proyectos/"):
                    clean_img_url = f"/proyectos_data/{rel_p[len('proyectos/'):]}"

    cref_url = character.get("cref_url") or clean_img_url
    if cref_url and "?" in cref_url:
        cref_url = cref_url.split("?")[0]
    cref_weight = int(character.get("cref_weight") if character.get("cref_weight") is not None else 100)

    lora_model = (character.get("lora_model") or f"{project_id}_{char_id}_v1".strip("_")).strip()
    lora_weight = float(character.get("lora_weight") if character.get("lora_weight") is not None else 0.85)
    lora_trigger = (character.get("lora_trigger") or f"chr_{char_id}").strip()

    seed = character.get("seed_consistencia") or compute_character_seed(char_id, project_id)
    visual_anchor = extract_character_visual_anchor(character)

    cref_directive = f"--cref {cref_url} --cw {cref_weight}" if (include_cref and cref_url) else ""
    lora_directive = f"<lora:{lora_model}:{lora_weight:.2f}> {lora_trigger}" if (include_lora and lora_model) else ""

    return {
        "id": char_id,
        "nombre": char_name,
        "rol": character.get("rol", ""),
        "tipo": character.get("tipo", "humano"),
        "imagen_url": img_url or clean_img_url,
        "clean_image_url": clean_img_url,
        "hoja_referencia_path": file_path,
        "reference_exists": file_exists,
        "cref_url": cref_url,
        "cref_weight": cref_weight,
        "cref_directive": cref_directive,
        "lora_model": lora_model,
        "lora_weight": lora_weight,
        "lora_trigger": lora_trigger,
        "lora_directive": lora_directive,
        "ancla_visual": visual_anchor,
        "seed_consistencia": seed
    }

def resolve_scene_character_references(
    characters_in_scene: Optional[List[str]] = None,
    project_characters: Optional[List[Dict[str, Any]]] = None,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Resuelve para una escena todas las hojas de referencia y parámetros (--cref / LoRA)
    de los personajes que intervienen, consultando el listado aportado o directamente
    el Banco de Consistencia de Personajes en disco.
    """
    if not characters_in_scene:
        return []

    source_chars = list(project_characters) if project_characters else []
    bank_chars = load_character_bank_for_prompt_generator(project_id)

    # Enriquecer source_chars con datos del banco en disco (ej: imagen_url si faltaba en el request)
    merged_pool: List[Dict[str, Any]] = []
    seen_ids = set()

    for c in source_chars:
        c_copy = dict(c)
        c_id = (c_copy.get("id") or "").lower()
        c_name = (c_copy.get("nombre") or "").lower()
        b_match = next(
            (b for b in bank_chars if (b.get("id", "").lower() == c_id and c_id) or (b.get("nombre", "").lower() == c_name and c_name)),
            None
        )
        if b_match:
            for k, v in b_match.items():
                if c_copy.get(k) is None or c_copy.get(k) == "":
                    c_copy[k] = v
        merged_pool.append(c_copy)
        seen_ids.add(c_id or c_name)

    for b in bank_chars:
        b_key = (b.get("id") or b.get("nombre") or "").lower()
        if b_key and b_key not in seen_ids:
            merged_pool.append(b)
            seen_ids.add(b_key)

    resolved: List[Dict[str, Any]] = []
    for target_name in characters_in_scene:
        t_clean = str(target_name).strip().lower()
        if not t_clean:
            continue
        c_match = next(
            (
                c for c in merged_pool
                if c.get("nombre", "").lower() == t_clean
                or c.get("id", "").lower() == t_clean
                or t_clean in c.get("nombre", "").lower()
                or c.get("nombre", "").lower() in t_clean
            ),
            None
        )
        if c_match:
            tokens = get_character_consistency_tokens(c_match, project_id=project_id or "")
            resolved.append(tokens)

    return resolved

def build_technical_prompt_with_cref_and_lora(
    base_prompt: str,
    character_refs: List[Dict[str, Any]]
) -> str:
    """
    Construye la versión técnica del prompt incluyendo etiquetas <lora:...> y banderas --cref / --cw
    de las hojas de referencia del Banco de Consistencia de Personajes.
    """
    clean_base = (base_prompt or "").strip()
    if not character_refs:
        return clean_base

    lora_parts = []
    cref_parts = []
    for ref in character_refs:
        if ref.get("lora_directive") and ref["lora_directive"] not in clean_base:
            lora_parts.append(ref["lora_directive"])
        if ref.get("cref_directive") and ref["cref_directive"] not in clean_base:
            cref_parts.append(ref["cref_directive"])

    segments = [clean_base]
    if lora_parts:
        segments.append(" ".join(lora_parts))
    if cref_parts:
        segments.append(" ".join(cref_parts))

    return " ".join([s for s in segments if s]).strip()

def format_character_bible(characters: Optional[List[Dict[str, Any]]], fallback_desc: str = "", project_id: str = "") -> str:
    """Construye las instrucciones del Banco de Consistencia y Biblia de Personajes para el LLM."""
    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    if effective_chars and len(effective_chars) > 0:
        lines = ["BANCO DE CONSISTENCIA Y BIBLIA DE PERSONAJES RECURRENTES (--cref / LoRA):"]
        for c in effective_chars:
            tokens = get_character_consistency_tokens(c, project_id=project_id)
            nom = c.get("nombre", "Personaje")
            rol = c.get("rol", "")
            desc = c.get("descripcion_visual", "")
            ref_info = f" [Ref: {tokens['clean_image_url']} | Trigger: {tokens['lora_trigger']}]" if tokens.get("clean_image_url") else f" [Trigger: {tokens['lora_trigger']}]"
            lines.append(f"- {nom} ({rol}){ref_info}: Rasgos visuales inmutables: {desc} | Ancla: {tokens['ancla_visual']}")
        lines.append("\nINSTRUCCIÓN CRUCIAL DE CONSISTENCIA:")
        lines.append("Cada vez que un personaje intervenga en una escena, debes incluir OBLIGATORIAMENTE su nombre exacto en 'personajes_en_escena' y sus rasgos visuales inmutables en 'prompt_imagen' para vincular su hoja de referencia (--cref / LoRA).")
        return "\n".join(lines)
    elif fallback_desc.strip():
        return f"Protagonista recurrente de la serie (mantén su apariencia idéntica en cada escena): '{fallback_desc}'."
    else:
        return "Mantén coherencia en el sujeto visual de la historia a lo largo de las escenas."

def format_environment_bible(escenarios: Optional[List[Dict[str, Any]]]) -> str:
    """Construye las instrucciones de la biblia de escenarios recurrentes para el LLM."""
    if escenarios and len(escenarios) > 0:
        lines = ["BIBLIA DE ESCENARIOS Y LOCALIZACIONES RECURRENTES DEL UNIVERSO:"]
        for e in escenarios:
            nom = e.get("nombre", "Lugar")
            tipo = e.get("tipo", "")
            desc = e.get("descripcion_visual", "")
            lines.append(f"- {nom} ({tipo}): Elementos visuales clave: {desc}")
        lines.append("\nINSTRUCCIÓN CRUCIAL DE LOCALIZACIÓN:")
        lines.append("Para cada escena, identifica el escenario recurrente donde transcurre la acción e incluye OBLIGATORIAMENTE sus rasgos visuales exactos en el 'prompt_imagen' para mantener consistencia espacial.")
        return "\n".join(lines)
    return ""

def enrich_scene_prompt_with_anchors(
    scene_prompt: str,
    characters_in_scene: Optional[List[str]] = None,
    project_characters: Optional[List[Dict[str, Any]]] = None,
    escenario_clave: Optional[str] = None,
    project_escenarios: Optional[List[Dict[str, Any]]] = None,
    style_prompt: str = "",
    project_id: Optional[str] = None,
    include_technical_flags: bool = False
) -> str:
    """
    Inyecta los rasgos canónicos inmutables de los personajes que intervienen en la escena
    (consultando el Banco de Consistencia de Personajes) y el escenario clave,
    reforzando la coherencia frente a la IA generativa y evitando deriva.
    """
    clean_p = scene_prompt.strip() if scene_prompt else ""

    # 1. Limpiar posibles banderas técnicas previas (--cref, --cw, <lora:...>) para recomponer limpio
    clean_p = re.sub(r"--cref\s+\S+(?:\s+--cw\s+\d+)?", "", clean_p, flags=re.IGNORECASE).strip()
    clean_p = re.sub(r"<lora:[^>]+>\s*(?:chr_\w+)?", "", clean_p, flags=re.IGNORECASE).strip()

    # 2. Limpiar de clean_p cualquier "set in [Escenario]..." previo para actualizarlo con el nuevo
    clean_p = re.sub(r"\bset in [^,]+:[^,]+(?=,|$)", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")

    # Limpiar sufijos técnicos repetidos para recomponer ordenadamente
    clean_p = re.sub(r"(?:vertical 9:16 portrait composition|masterpiece|no text|no words|no labels).*$", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")
    if style_prompt:
        clean_p = clean_p.replace(style_prompt, "").strip().strip(",; ")

    anchors = []

    # 3. Resolver personajes desde project_characters o desde el Banco de Consistencia en disco
    effective_chars = project_characters if (project_characters and len(project_characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    resolved_refs = resolve_scene_character_references(
        characters_in_scene=characters_in_scene,
        project_characters=effective_chars,
        project_id=project_id
    )

    for ref in resolved_refs:
        anchor = ref["ancla_visual"]
        char_name_lower = ref.get("nombre", "").lower()
        char_tokens = {t.lower() for t in re.findall(r"\w+", ref.get("nombre", ""))}
        core_tokens = [w for w in re.findall(r"\w{5,}", anchor.lower()) if w not in ("standing", "character", "natural", "features") and w not in char_tokens]
        already = (char_name_lower in clean_p.lower()) and (any(tok in clean_p.lower() for tok in core_tokens[:3]) if core_tokens else True)
        if not already:
            anchors.append(anchor)

    # 4. Ancla de escenario clave
    if escenario_clave and project_escenarios:
        e_match = next(
            (e for e in project_escenarios if e.get("nombre", "").lower() == escenario_clave.lower() or e.get("id", "").lower() == escenario_clave.lower()),
            None
        )
        if e_match:
            esc_txt = e_match.get("prompt_escenario") or e_match.get("descripcion_visual") or ""
            clean_esc = re.sub(r"(?:vertical 9:16 background art|masterpiece|empty scene|no people|no words|no text).*$", "", esc_txt, flags=re.IGNORECASE).strip().strip(",; ")
            if clean_esc:
                anchors.append(f"set in {e_match.get('nombre')}: {clean_esc[:95]}")

    # Composición final
    parts = []
    if anchors:
        parts.append(", ".join(anchors))
    if clean_p:
        parts.append(clean_p)
    if style_prompt and style_prompt.lower()[:25] not in clean_p.lower():
        parts.append(style_prompt)
    parts.append("vertical 9:16 portrait composition, masterpiece, no text, no words, no labels")

    final_result = ", ".join([p.strip().strip(",;") for p in parts if p.strip()])
    final_result = re.sub(r"\s*,\s*", ", ", final_result)

    if include_technical_flags and resolved_refs:
        final_result = build_technical_prompt_with_cref_and_lora(final_result, resolved_refs)

    return final_result

def attach_consistency_metadata_to_scene(
    scene: Dict[str, Any],
    characters: Optional[List[Dict[str, Any]]] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Adjunta a una escena las referencias del Banco de Consistencia de Personajes:
    - referencias_personajes: metadatos completos (--cref, LoRA, imagen_url, ruta física, seed)
    - reference_image: URL de la hoja de referencia principal para Image-to-Image / Control
    - prompt_tecnico_cref: prompt enriquecido con directivas --cref y <lora:...>
    """
    chars_in_scene = scene.get("personajes_en_escena") or []
    refs = resolve_scene_character_references(
        characters_in_scene=chars_in_scene,
        project_characters=characters,
        project_id=project_id
    )
    scene["referencias_personajes"] = refs
    primary_ref = next((r["imagen_url"] for r in refs if r.get("imagen_url")), None)
    scene["reference_image"] = primary_ref
    scene["seed_consistencia"] = refs[0]["seed_consistencia"] if refs else None
    scene["prompt_tecnico_cref"] = build_technical_prompt_with_cref_and_lora(
        scene.get("prompt_imagen", ""),
        refs
    )
    return scene

def breakdown_storyboard(
    text: str,
    character_desc: str = "",
    characters: Optional[List[Dict[str, Any]]] = None,
    escenarios: Optional[List[Dict[str, Any]]] = None,
    style_key: str = "cinematic",
    style_details: str = "",
    audiencia: str = "",
    ambiente: str = "",
    target_scenes: int = 4,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Desglosa un texto o capítulo en un conjunto ordenado de escenas con
    guion de locución y prompt visual coherente basado en el Banco de Consistencia de Personajes,
    la Biblia de Escenarios Recurrentes, el público objetivo y la ambientación del universo.
    """
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style

    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)

    char_clause = format_character_bible(effective_chars, character_desc, project_id=project_id or "")
    esc_clause = format_environment_bible(escenarios)
    aud_clause = f"Público objetivo y tono de la serie: {audiencia}. (Adapta el vocabulario, cadencia y tono emocional especialmente para esta audiencia)." if audiencia else ""
    amb_clause = f"Ambiente y universo del libro: {ambiente}. (Sitúa las acciones y escenarios dentro de este mundo)." if ambiente else ""

    system_instruction = f"""Eres un director audiovisual y guionista de vídeos cortos para TikTok, Reels y YouTube Shorts.
Tu trabajo es adaptar el texto del capítulo en exactamente {target_scenes} escenas dinámicas pensadas para formato vertical (9:16).

{aud_clause}
{amb_clause}
{char_clause}
{esc_clause}

Estilo visual global de toda la serie: {style_prompt}.

Reglas de producción:
1. 'narrador': Texto exacto que dirá la voz en off en español para esta escena (15 a 25 palabras). Debe tener gancho y ritmo ágil para retención de audiencia, con tono acorde al público objetivo.
2. 'prompt_imagen': Prompt en INGLÉS detallado para generar la imagen vertical 9:16 de esta escena. Debe describir la composición vertical, la acción, la iluminación, el escenario recurrente según la Biblia de Escenarios y los rasgos físicos EXACTOS de los personajes que aparezcan (según el Banco de Consistencia de Personajes), rematando con el estilo global ({style_prompt}). No pongas textos escritos dentro de la imagen.
3. 'personajes_en_escena': Lista de nombres de los personajes que aparecen en esta escena (ej: ["Platero"]).
4. 'escenario_clave': Nombre del escenario recurrente del universo donde ocurre la escena si corresponde, o 'Escenario específico'.
5. 'duracion_estimada': Duración estimada en segundos (ej. 4 a 7 segundos).

Devuelve ÚNICAMENTE un array JSON válido con la siguiente estructura, sin texto adicional ni markdown:
[
  {{
    "id": 1,
    "narrador": "...",
    "prompt_imagen": "...",
    "personajes_en_escena": ["..."],
    "escenario_clave": "...",
    "duracion_estimada": 5
  }}
]
"""

    user_prompt = f"Texto del capítulo a adaptar:\n\n{text}"

    # 1. Intentar con OpenAI si hay clave
    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1800
            )
            raw_content = response.choices[0].message.content or ""
            cleaned = clean_json_string(raw_content)
            scenes = json.loads(cleaned)
            if isinstance(scenes, list) and len(scenes) > 0:
                for i, sc in enumerate(scenes):
                    sc["id"] = i + 1
                    sc.setdefault("narrador", "")
                    sc.setdefault("prompt_imagen", "")
                    sc.setdefault("personajes_en_escena", [])
                    sc.setdefault("duracion_estimada", 5)
                    # Enriquecer e inyectar anclas de personajes y escenarios aprobados
                    sc["prompt_imagen"] = enrich_scene_prompt_with_anchors(
                        scene_prompt=sc["prompt_imagen"],
                        characters_in_scene=sc.get("personajes_en_escena", []),
                        project_characters=effective_chars or [],
                        escenario_clave=sc.get("escenario_clave"),
                        project_escenarios=escenarios or [],
                        style_prompt=style_prompt,
                        project_id=project_id
                    )
                    attach_consistency_metadata_to_scene(sc, effective_chars, project_id=project_id)
                    sc["audio_url"] = None
                    sc["image_url"] = None
                    sc["duracion_real"] = None
                return scenes
        except Exception as e:
            print(f"[AI] Error llamando a OpenAI: {e}. Activando fallback heurístico.")

    # 2. Fallback Heurístico
    return generate_fallback_storyboard(
        text=text,
        characters=effective_chars,
        character_desc=character_desc,
        style_prompt=style_prompt,
        target_scenes=target_scenes,
        ambiente=ambiente,
        escenarios=escenarios,
        project_id=project_id
    )

def generate_fallback_storyboard(
    text: str,
    characters: Optional[List[Dict[str, Any]]],
    character_desc: str,
    style_prompt: str,
    target_scenes: int,
    ambiente: str = "",
    escenarios: Optional[List[Dict[str, Any]]] = None,
    project_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Generador heurístico de escenas en caso de no contar con API Key activa."""
    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if not sentences:
        sentences = [
            "En un mundo donde cada segundo cuenta, una decisión puede cambiarlo todo.",
            "Los secretos guardados durante años comienzan a salir a la luz.",
            "El camino hacia la verdad nunca estuvo exento de peligros.",
            "Al final, solo aquellos que se atreven a avanzar logran cruzar el umbral."
        ]

    chunk_size = max(1, len(sentences) // target_scenes)
    scenes = []

    for i in range(target_scenes):
        start = i * chunk_size
        end = start + chunk_size if i < target_scenes - 1 else len(sentences)
        scene_sentences = sentences[start:end] if start < len(sentences) else [sentences[-1]]
        narrador = " ".join(scene_sentences)

        # Detectar personajes mencionados en el fragmento o usar el protagonista
        detected_names = []
        if effective_chars:
            for c in effective_chars:
                c_name = c.get("nombre", "")
                base_token = c_name.split("(")[0].strip().lower()
                if base_token and base_token in narrador.lower():
                    detected_names.append(c_name)
            if not detected_names:
                detected_names = [effective_chars[0]["nombre"]]

        esc_name = escenarios[i % len(escenarios)]["nombre"] if (escenarios and len(escenarios) > 0) else None

        base_prompt = f"Scene {i+1}: action portraying {narrador[:80]}"
        enriched_prompt = enrich_scene_prompt_with_anchors(
            scene_prompt=base_prompt,
            characters_in_scene=detected_names,
            project_characters=effective_chars or [],
            escenario_clave=esc_name,
            project_escenarios=escenarios or [],
            style_prompt=style_prompt,
            project_id=project_id
        )

        sc_obj = {
            "id": i + 1,
            "narrador": narrador,
            "prompt_imagen": enriched_prompt,
            "personajes_en_escena": detected_names,
            "escenario_clave": esc_name or "General",
            "duracion_estimada": 5,
            "audio_url": None,
            "image_url": None,
            "duracion_real": None
        }
        attach_consistency_metadata_to_scene(sc_obj, effective_chars, project_id=project_id)
        scenes.append(sc_obj)

    return scenes

def rewrite_scene(
    scene_data: Dict[str, Any],
    feedback: str,
    characters: Optional[List[Dict[str, Any]]] = None,
    character_desc: str = "",
    style_key: str = "cinematic",
    style_details: str = "",
    escenarios: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """Reescribe una escena específica según las indicaciones de feedback del usuario."""
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style
    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    char_clause = format_character_bible(effective_chars, character_desc, project_id=project_id or "")

    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            prompt = f"""Escena actual:
Narrador: {scene_data.get('narrador', '')}
Prompt Imagen: {scene_data.get('prompt_imagen', '')}

Feedback del usuario para mejorarla:
"{feedback}"

{char_clause}
Estilo visual de la serie: {style_prompt}

Devuelve ÚNICAMENTE un JSON con este formato exacto:
{{
  "narrador": "nuevo texto en español (15-25 palabras)",
  "prompt_imagen": "nuevo prompt en inglés con la descripción visual respetando la biblia de personajes y {style_prompt}"
}}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            raw = clean_json_string(response.choices[0].message.content or "")
            updated = json.loads(raw)
            scene_data["narrador"] = updated.get("narrador", scene_data["narrador"])
            new_prompt = updated.get("prompt_imagen", scene_data["prompt_imagen"])
            scene_data["prompt_imagen"] = enrich_scene_prompt_with_anchors(
                scene_prompt=new_prompt,
                characters_in_scene=scene_data.get("personajes_en_escena", []),
                project_characters=effective_chars or [],
                escenario_clave=scene_data.get("escenario_clave"),
                project_escenarios=escenarios or [],
                style_prompt=style_prompt,
                project_id=project_id
            )
            attach_consistency_metadata_to_scene(scene_data, effective_chars, project_id=project_id)
            scene_data["audio_url"] = None
            scene_data["image_url"] = None
            return scene_data
        except Exception as e:
            print(f"[AI] Error reescribiendo escena: {e}")

    scene_data["narrador"] = f"{scene_data['narrador']} ({feedback})"
    scene_data["prompt_imagen"] = enrich_scene_prompt_with_anchors(
        scene_prompt=f"{scene_data['prompt_imagen']}, {feedback}",
        characters_in_scene=scene_data.get("personajes_en_escena", []),
        project_characters=effective_chars or [],
        style_prompt=style_prompt,
        project_id=project_id
    )
    attach_consistency_metadata_to_scene(scene_data, effective_chars, project_id=project_id)
    return scene_data
