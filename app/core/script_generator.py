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
    "cinematic": "cinematic lighting, photorealistic 8k, shot on 35mm lens, atmospheric depth of field, dramatic shadows, no cartoon, no comic outlines, no flat colors",
    "noir_bw": "black and white film noir photography, dramatic high contrast monochrome, sharp shadows, moody lighting, classic monochrome 35mm film, strictly monochrome, no color, no flat daylight",
    "anime": "anime aesthetic, Makoto Shinkai style, vibrant colors, beautiful sky, high quality anime screencap, trending on Pixiv, no 3D CGI, no analog grain, no blurry watercolor",
    "ghibli_anime": "Studio Ghibli aesthetic, Hayao Miyazaki hand-drawn anime, painterly backgrounds, warm nostalgic feel, whimsical art, no plastic 3D render, no photorealism, no cyberpunk",
    "watercolor": "delicate watercolor and ink illustration, soft artistic color washes, storybook illustration, rich paper texture, no 3D CGI, no photorealism, no hard digital edges",
    "storybook_kids": "whimsical children's book illustration, vibrant friendly colors, charming storybook character art, soft lighting, family friendly, highly detailed, no photorealism, no harsh shadows",
    "pixar_3d": "3D animated movie render, Pixar Disney style, soft volumetric subsurface scattering, expressive character facial features, 4k 8k, no flat 2D drawing, no ink outlines, no low-poly",
    "dark_fantasy": "dark fantasy, hyperdetailed, grimdark aesthetic, ominous lighting, mystical atmosphere, concept art, Unreal Engine 5 render, no bright pastel colors, no cartoon",
    "cyberpunk": "cyberpunk style, neon lights, rainy reflection, high tech dystopian, blade runner aesthetic, volumetric glow, no rural daylight, no vintage analog",
    "vintage": "vintage 1970s film grain, warm Kodak Portra color tones, nostalgic, retro photography, authentic cinematic texture, no modern neon, no synthetic 3D render",
    "comic": "graphic novel comic illustration, bold ink lines, dynamic comic book shading, expressive colors, Frank Miller style, no photorealism, no soft watercolor wash"
}

def clean_json_string(raw: str) -> str:
    """Extrae y limpia bloques de código JSON devueltos por LLMs."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw


def _call_llm_chat(
    messages: List[Dict[str, str]],
    temperature: float = 0.4,
    max_tokens: int = 2500,
    api_key: Optional[str] = None,
) -> str:
    """
    Ejecuta una consulta LLM en cascada garantizando disponibilidad:
    1) OpenAI API (gpt-4o-mini) si OPENAI_API_KEY tiene crédito.
    2) Fal.ai Any-LLM (openai/gpt-4o-mini) si FAL_KEY tiene crédito.
    3) Pollinations Text OpenAI-compatible API (gratuita, 0€) como respaldo universal.
    """
    import requests as _req

    openai_key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            txt = (resp.choices[0].message.content or "").strip()
            if txt:
                return txt
        except Exception as e:
            print(f"[LLM] OpenAI no disponible ({e}), probando siguiente proveedor...")

    fal_key = os.getenv("FAL_KEY", "").strip()
    if fal_key:
        try:
            sys_parts = [m["content"] for m in messages if m.get("role") == "system"]
            usr_parts = [m["content"] for m in messages if m.get("role") != "system"]
            r = _req.post(
                "https://fal.run/fal-ai/any-llm",
                headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"},
                json={
                    "model": "openai/gpt-4o-mini",
                    "system_prompt": "\n\n".join(sys_parts) if sys_parts else "You are a helpful assistant.",
                    "prompt": "\n\n".join(usr_parts),
                },
                timeout=35,
            )
            if r.status_code == 200:
                out = (r.json().get("output") or "").strip()
                if out:
                    return out
        except Exception as e:
            print(f"[LLM] Fal any-llm no disponible ({e}), usando proveedor gratuito...")

    r_free = _req.post(
        "https://text.pollinations.ai/openai",
        headers={"Content-Type": "application/json"},
        json={
            "model": "openai",
            "messages": messages,
            "temperature": temperature,
        },
        timeout=45,
    )
    if r_free.status_code == 200:
        data = r_free.json()
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message", {}).get("content") or "").strip()
            if content:
                return content
    raise RuntimeError(f"No se pudo obtener respuesta de ningún proveedor LLM (HTTP {r_free.status_code})")


def _normalize_pdf_line_breaks(text: str) -> str:
    """Normaliza ligaduras tipográficas, saltos de línea rotos de PDF y asegura frases cerradas con puntuación."""
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    # Reemplazar ligaduras comunes de PDFs
    for lig, rep in (("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")):
        t = t.replace(lig, rep)

    # Separar en párrafos reales (líneas en blanco) o detectar saltos de línea duros dentro de un mismo párrafo
    raw_lines = [ln.strip() for ln in t.split("\n")]
    paragraphs: List[str] = []
    cur_parts: List[str] = []

    for ln in raw_lines:
        if not ln:
            if cur_parts:
                paragraphs.append(" ".join(cur_parts))
                cur_parts = []
            continue
        # Si la línea previa terminaba en puntuación fuerte y la nueva empieza por diálogo o mayúscula tras línea corta,
        # puede ser nuevo párrafo; si no, forma parte de la misma frase/párrafo.
        if cur_parts and cur_parts[-1].endswith((".", "!", "?", "…")) and (ln.startswith(("—", "-", "«", "\"")) or len(cur_parts[-1]) < 48):
            paragraphs.append(" ".join(cur_parts))
            cur_parts = [ln]
        else:
            # Unir palabras partidas por guion al final de línea (ej. "al-\ngodón")
            if cur_parts and cur_parts[-1].endswith("-") and not cur_parts[-1].endswith("—"):
                cur_parts[-1] = cur_parts[-1][:-1] + ln
            else:
                cur_parts.append(ln)

    if cur_parts:
        paragraphs.append(" ".join(cur_parts))

    cleaned_paragraphs: List[str] = []
    for p in paragraphs:
        p = re.sub(r"\s{2,}", " ", p).strip()
        if not p:
            continue
        # Suavizar guiones de diálogo al inicio para lectura fluida (ej. "—Tien' asero…" -> "«Tien' asero…»" o coma)
        p = re.sub(r"^—\s*", "", p).strip()
        if not p.endswith((".", "!", "?", "…", ":", "»", "\"")):
            p += "."
        cleaned_paragraphs.append(p)

    return "\n\n".join(cleaned_paragraphs)


def _split_sentences_preserving_punctuation(text: str) -> List[str]:
    """Divide un texto en frases completas conservando siempre su signo de puntuación final."""
    norm = _normalize_pdf_line_breaks(text)
    if not norm:
        return []
    # Separar tras ., !, ?, … (incluyendo cierres de comillas » o ") seguido de espacio o salto de línea
    raw_sents = re.split(r'(?<=[.!?…»"])\s+(?=[A-ZÁÉÍÓÚÑ¿¡«"—0-9])', norm.replace("\n\n", " "))
    out: List[str] = []
    for s in raw_sents:
        s = re.sub(r"\s{2,}", " ", s).strip()
        if not s:
            continue
        if not s.endswith((".", "!", "?", "…", "»", "\"")):
            s += "."
        out.append(s)
    return out


def split_narration_into_scenes(text: str, target_scenes: int) -> List[str]:
    """Reparte un texto en target_scenes respetando frases completas (sin partir ninguna frase)."""
    norm = _normalize_pdf_line_breaks(text)
    if not norm:
        return [""] * max(1, target_scenes)
    sentences = _split_sentences_preserving_punctuation(norm)
    units = sentences if len(sentences) >= target_scenes else [p.strip() for p in norm.split("\n\n") if p.strip()]
    if not units:
        return [norm]

    n = max(1, target_scenes)
    if len(units) <= n:
        return units

    # Reparto equilibrado por longitud en caracteres manteniendo frases completas
    total_chars = sum(len(u) for u in units)
    ideal = total_chars / n
    chunks: List[List[str]] = []
    cur: List[str] = []
    cur_len = 0
    for idx, u in enumerate(units):
        remaining_units = len(units) - idx
        remaining_slots = n - len(chunks)
        # Si ya hay contenido y añadir esta frase alejaría más del tamaño ideal que cerrar aquí, cerramos antes
        if cur and len(chunks) < n - 1 and remaining_units >= remaining_slots:
            if abs((cur_len + len(u)) - ideal) > abs(cur_len - ideal) and cur_len >= ideal * 0.65:
                chunks.append(cur)
                cur = []
                cur_len = 0
        cur.append(u)
        cur_len += len(u)
        if len(chunks) < n - 1 and (cur_len >= ideal or remaining_units - 1 == remaining_slots - 1):
            chunks.append(cur)
            cur = []
            cur_len = 0
    if cur:
        if len(chunks) < n:
            chunks.append(cur)
        else:
            chunks[-1].extend(cur)

    return [" ".join(c).strip() for c in chunks]


def prepare_narration_text(text: str, use_ai: bool = True) -> str:
    """
    Prepara y revisa el texto completo para locución en voz alta:
    - Une líneas partidas de PDF y elimina ligaduras raras.
    - Asegura frases claras, completas, bien puntuadas y terminadas en punto.
    - Respeta fielmente el contenido literario original.
    """
    base_clean = _normalize_pdf_line_breaks(text)
    if not base_clean:
        return ""

    if not use_ai:
        return base_clean

    try:
        sys_msg = (
            "Eres un corrector editorial experto en audiolibros en español. "
            "Tu tarea es revisar el texto proporcionado para que un narrador profesional pueda leerlo en voz alta con total fluidez y naturalidad.\n"
            "REGLAS ESTRICTAS:\n"
            "1. Une todas las líneas partidas de PDF o maquetación en párrafos continuos y limpios.\n"
            "2. Asegúrate de que TODAS las frases estén completas, bien separadas y finalizadas con su signo de puntuación (punto '.', interrogación '?', exclamación '!' o puntos suspensivos '…'). Nunca dejes frases sin punto ni pegadas entre sí.\n"
            "3. Conserva fielmente las palabras y el estilo literario del texto original (no resumas, no inventes ni cambies el sentido; solo corrige puntuación rota, ligaduras o guiones de diálogo sueltos para que suene natural al leerlo).\n"
            "4. Separa párrafos claros con una línea en blanco.\n"
            "5. Devuelve ÚNICAMENTE el texto revisado, sin explicaciones ni comillas envolventes."
        )
        ai_text = _call_llm_chat(
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": base_clean[:12000]},
            ],
            temperature=0.15,
            max_tokens=3000,
        )
        if ai_text and len(ai_text) >= len(base_clean) * 0.65:
            return _normalize_pdf_line_breaks(ai_text)
    except Exception as e:
        print(f"[PREPARE_NARRATION] Fallback local por error LLM: {e}")

    return base_clean

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

def load_environment_bank_for_prompt_generator(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Carga los escenarios recurrentes directamente desde proyecto.json en disco."""
    escenarios: List[Dict[str, Any]] = []
    if not PROYECTOS_DIR.exists() or not project_id:
        return escenarios
    cand = PROYECTOS_DIR / project_id / "proyecto.json"
    if cand.exists():
        try:
            with open(cand, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            if isinstance(p_data.get("escenarios"), list):
                return p_data["escenarios"]
        except Exception:
            pass
    return escenarios


def extract_environment_visual_anchor(escenario: Dict[str, Any], project_id: str = "") -> Dict[str, Any]:
    """Extrae la descripción visual canónica en inglés y la semilla de un escenario recurrente."""
    esc_id = escenario.get("id") or re.sub(r"\W+", "_", escenario.get("nombre", "env").lower()).strip("_")
    esc_name = escenario.get("nombre", "Escenario").strip()
    seed = escenario.get("seed_consistencia") or compute_character_seed(f"env_{esc_id}", project_id)
    esc_txt = (escenario.get("prompt_escenario") or "").strip()
    desc_vis = (escenario.get("descripcion_visual") or "").strip()

    clean_esc = esc_txt
    if clean_esc:
        # Quitar prefijo genérico hasta "Scenic background illustration of <Nombre>: <Nombre>,"
        clean_esc = re.sub(
            r"^.*?Scenic background illustration of [^:]+:\s*(?:[^,]+,\s*)?",
            "",
            clean_esc,
            flags=re.IGNORECASE,
        ).strip()
        # Quitar directivas de escena vacía ("empty scene, no people, no characters, no animals...") y sufijos de estilo
        clean_esc = re.sub(
            r",?\s*(?:empty scene|no people|no characters|no animals|no text|no words|no labels|no watermarks|vertical 9:16).*$",
            "",
            clean_esc,
            flags=re.IGNORECASE,
        ).strip().strip(".,; ")

    if not clean_esc or len(clean_esc) < 20:
        clean_esc = desc_vis

    return {
        "id": esc_id,
        "nombre": esc_name,
        "seed_consistencia": int(seed),
        "clean_description": clean_esc,
        "imagen_url": escenario.get("imagen_url"),
    }


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
    Inyecta los rasgos canónicos inmutables y semillas de los personajes que intervienen en la escena
    y del escenario clave, reforzando la coherencia frente a la IA generativa y evitando deformaciones.
    """
    clean_p = scene_prompt.strip() if scene_prompt else ""

    # 1. Limpiar posibles banderas técnicas previas (--cref, --cw, <lora:...>, [seed_...], [Transición...]) para recomponer limpio
    clean_p = re.sub(r"--cref\s+\S+(?:\s+--cw\s+\d+)?", "", clean_p, flags=re.IGNORECASE).strip()
    clean_p = re.sub(r"<lora:[^>]+>\s*(?:chr_\w+)?", "", clean_p, flags=re.IGNORECASE).strip()
    clean_p = re.sub(r"\[seed_(?:personaje|escenario):[^\]]+\]", "", clean_p, flags=re.IGNORECASE).strip()
    clean_p = re.sub(r"\[(?:Transici[óo]n|Escena)[^\]]+\]", "", clean_p, flags=re.IGNORECASE).strip()

    # 2. Limpiar de clean_p cualquier "set in [Escenario]..." previo para actualizarlo con el nuevo
    clean_p = re.sub(r"\bset in [^:]+:\s*[^,]+(?:,[^,]+)*?(?=\b(?:vertical 9:16|delicate|cinematic|whimsical|$))", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")
    clean_p = re.sub(r"\bset in [^,]+:[^,]+(?=,|$)", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")

    # Limpiar sufijos técnicos repetidos para recomponer ordenadamente
    clean_p = re.sub(r"(?:well-proportioned anatomy|vertical 9:16 portrait composition|masterpiece|no text|no words|no labels).*$", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")
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
        anchor = re.sub(r",?\s*\bno humans\b", ", non-anthropomorphic animal", ref["ancla_visual"], flags=re.IGNORECASE)
        char_name_lower = ref.get("nombre", "").lower()
        char_tokens = {t.lower() for t in re.findall(r"\w+", ref.get("nombre", ""))}
        core_tokens = [w for w in re.findall(r"\w{5,}", anchor.lower()) if w not in ("standing", "character", "natural", "features") and w not in char_tokens]
        already = (char_name_lower in clean_p.lower()) and (any(tok in clean_p.lower() for tok in core_tokens[:3]) if core_tokens else True)
        if not already:
            anchors.append(anchor)

    # 4. Ancla completa de escenario clave con su descripción arquitectónica/ambiental íntegra (sin etiquetas [seed:...])
    effective_escs = list(project_escenarios) if (project_escenarios and len(project_escenarios) > 0) else []
    disk_escs = load_environment_bank_for_prompt_generator(project_id)
    if disk_escs:
        if not effective_escs:
            effective_escs = disk_escs
        else:
            for e in effective_escs:
                d_match = next(
                    (d for d in disk_escs if d.get("id", "").lower() == (e.get("id") or "").lower() or d.get("nombre", "").lower() == (e.get("nombre") or "").lower()),
                    None,
                )
                if d_match:
                    for k, v in d_match.items():
                        if not e.get(k):
                            e[k] = v

    if escenario_clave and effective_escs:
        e_match = next(
            (
                e for e in effective_escs
                if e.get("nombre", "").lower() == escenario_clave.lower()
                or e.get("id", "").lower() == escenario_clave.lower()
                or escenario_clave.lower() in e.get("nombre", "").lower()
                or e.get("nombre", "").lower() in escenario_clave.lower()
            ),
            None
        )
        if e_match:
            env_info = extract_environment_visual_anchor(e_match, project_id=project_id or "")
            if env_info["clean_description"]:
                anchors.append(
                    f"set in {env_info['nombre']}: {env_info['clean_description']}, full-bleed painted sky and background with no white margins"
                )

    # Composición final con salvaguardas anatómicas para evitar deformaciones
    parts = []
    if anchors:
        parts.append(", ".join(anchors))
    if clean_p:
        parts.append(clean_p)
    if style_prompt and style_prompt.lower()[:25] not in clean_p.lower():
        parts.append(style_prompt)
    parts.append("well-proportioned anatomy, distinct separate characters, no deformed limbs, no fused bodies, vertical 9:16 portrait composition, masterpiece, no text, no words, no labels")

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

def _pick_primary_scenario_and_chars(
    text: str,
    chapter_title: str,
    esc_names: List[str],
    char_names: List[str],
) -> tuple[str, List[str]]:
    """Elige un único escenario principal y solo los personajes mencionados en el texto."""
    haystack = f"{chapter_title} {text}".lower()
    stopwords = {"de", "del", "la", "el", "los", "las", "y", "en", "con", "por", "un", "una"}

    chosen_esc = esc_names[0] if esc_names else "el entorno del capítulo"
    best_score = 0
    for esc in esc_names:
        tokens = [w for w in re.findall(r"[a-záéíóúñ]{3,}", esc.lower()) if w not in stopwords]
        score = sum(1 for t in tokens if t in haystack)
        if score > best_score:
            best_score = score
            chosen_esc = esc

    matched_chars = []
    for name in char_names:
        base = name.split("(")[0].strip().lower()
        if base and base in haystack:
            matched_chars.append(name)
    if not matched_chars and char_names:
        matched_chars = [char_names[0]]

    return chosen_esc, matched_chars


def propose_chapter_treatment(
    text: str,
    chapter_title: str = "Capítulo",
    characters: Optional[List[Dict[str, Any]]] = None,
    escenarios: Optional[List[Dict[str, Any]]] = None,
    style_key: str = "cinematic",
    style_details: str = "",
    audiencia: str = "",
    ambiente: str = "",
    target_scenes: int = 4,
    api_key: Optional[str] = None,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera una propuesta general editable (historia, cómo contarla y duración por escena)
    a partir del texto del capítulo y la biblia del proyecto.
    """
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    char_names = [c.get("nombre", "").split("(")[0].strip() for c in (effective_chars or []) if c.get("nombre")]
    esc_names = [e.get("nombre", "").strip() for e in (escenarios or []) if e.get("nombre")]
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style

    # Calcular número óptimo de escenas para que cada escena dure ~10-13s (~24-30 palabras, 1 solo clip I2V de 10s)
    word_count_est = len((text or "").split())
    auto_scenes = max(2, min(8, round(word_count_est / 26))) if word_count_est > 45 else max(1, target_scenes)
    effective_target_scenes = max(int(target_scenes or 4), auto_scenes)

    try:
        sys_msg = f"""Eres director de cine de animación y narrador literario.
A partir del texto del capítulo "{chapter_title}", elabora el PLAN NARRATIVO Y DE PUESTA EN ESCENA en español antes de generar las escenas:
- Público objetivo: {audiencia or "General"}
- Ambiente/universo: {ambiente or "Fiel al texto"}
- Estilo visual: {style_prompt}
- Personajes disponibles en el banco: {", ".join(char_names) or "Según texto"}
- Escenarios disponibles en el banco: {", ".join(esc_names) or "Según texto"}
- Número óptimo de escenas (~10-13 segundos por escena, 1 acción visual clara por escena): {effective_target_scenes}

REGLAS NARRATIVAS ESTRICTAS:
1. `enfoque_general` (HISTORIA GENERAL DEL CAPÍTULO): Explica en 3-4 frases qué historia concreta cuenta este capítulo de principio a fin (inicio/planteamiento, encuentro o acción central y desenlace poético), cuál es su emoción y cómo evoluciona por los escenarios. Prohibido usar frases genéricas vacías.
2. `escenario_clave` y relación con el entorno: Elige para cada escena el escenario de la lista ({", ".join(esc_names) or "del universo"}) que mejor encaje con lo que ocurre en ese fragmento (puedes cambiar de escenario entre escenas si el relato se desplaza del campo a las callejas o a una casucha).
3. `personajes_en_escena`: Incluye TODOS los personajes del banco que intervienen en esa escena (ej. ["Platero", "El Poeta / Yo lírico"] si el narrador va con Platero o habla en primera persona interactuando con él).
4. `que_ocurre` (PUESTA EN ESCENA Y ENTORNO PARA LA FOTO): Describe con todo detalle cómo están situados los personajes dentro del escenario al arrancar la escena, cómo se relacionan con el entorno y qué objetos concretos mencionados en la narración aparecen (flores, frutas, sacas de carbón, farol, cigarro, alforjas, mariposas blancas...).
5. `accion_video` (COREOGRAFÍA FÍSICA EN EL VÍDEO DE 10s): Describe específicamente QUÉ HACEN Y CÓMO SE MUEVEN los personajes (por ejemplo, qué hace el burrito Platero, cómo reacciona al entorno o al otro personaje) y cómo se mueve la cámara durante esos 10 segundos para que el vídeo cuente literalmente lo que dice la voz.
6. `texto_narrado`: Reparte el texto íntegro del capítulo en {effective_target_scenes} bloques de ~20-32 palabras (~10-13s) sin saltos de línea rotos, sin partir ninguna frase a mitad entre escenas y terminando siempre en puntuación final (`.`, `?`, `!` o `…`).

Devuelve ÚNICAMENTE JSON válido con esta estructura:
{{
  "enfoque_general": "Historia general del capítulo: planteamiento, nudo/acción central, desenlace poético y evolución visual por los escenarios.",
  "bloques": [
    {{
      "id": 1,
      "titulo": "Título narrativo de la escena",
      "escenario_clave": "Nombre exacto del escenario de esta escena",
      "personajes_en_escena": ["Platero", "El Poeta / Yo lírico"],
      "transicion_desde_anterior": "Cómo enlaza la acción y el espacio desde la escena anterior (dejar vacío en la escena 1)",
      "que_ocurre": "Puesta en escena detallada: relación de los personajes con el escenario y objetos concretos visibles en la foto inicial.",
      "accion_video": "Movimiento físico exacto durante los 10s de vídeo: qué hacen Platero y los personajes y cómo acompaña la cámara.",
      "texto_narrado": "Fragmento exacto del texto que leerá el narrador en esta escena (frases completas cerradas en punto).",
      "duracion_seg": 10
    }}
  ]
}}"""
        raw_llm = _call_llm_chat(
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": f"Texto del capítulo:\n\n{_normalize_pdf_line_breaks(text)}"}
            ],
            temperature=0.45,
            max_tokens=2200,
            api_key=openai_key,
        )
        data = json.loads(clean_json_string(raw_llm))
        bloques = data.get("bloques") or []
        if isinstance(bloques, list) and len(bloques) > 0:
            total = 0
            for idx, b in enumerate(bloques):
                b["id"] = idx + 1
                b["titulo"] = (b.get("titulo") or f"Escena {idx + 1}").strip()
                b["escenario_clave"] = (b.get("escenario_clave") or (esc_names[0] if esc_names else "")).strip()
                b["personajes_en_escena"] = b.get("personajes_en_escena") if isinstance(b.get("personajes_en_escena"), list) else (char_names[:1] if char_names else ["Platero"])
                b["transicion_desde_anterior"] = (b.get("transicion_desde_anterior") or "").strip() if idx > 0 else ""
                b["que_ocurre"] = (b.get("que_ocurre") or "").strip()
                b["accion_video"] = (b.get("accion_video") or "").strip()
                b["texto_narrado"] = _normalize_pdf_line_breaks(b.get("texto_narrado") or "").replace("\n\n", " ")
                words_b = len(b["texto_narrado"].split())
                est_dur = max(8, min(15, round(words_b / 2.35))) if words_b > 0 else int(b.get("duracion_seg") or 10)
                b["duracion_seg"] = est_dur
                total += est_dur
            return {
                "enfoque_general": (data.get("enfoque_general") or "").strip(),
                "bloques": bloques,
                "duracion_total_seg": total
            }
    except Exception as e:
        print(f"[AI] Error generando propuesta con LLM: {e}. Usando propuesta estructurada.")

    # Fallback heurístico visual (describe puesta en escena sin copiar frases literales de la narración)
    word_count = len((text or "").split())
    max_n = max(1, int(target_scenes or 4))
    if word_count <= 35:
        n = 1
    elif word_count <= 90:
        n = min(max_n, 2)
    else:
        n = min(max_n, 3)

    primary_esc, active_chars = _pick_primary_scenario_and_chars(text, chapter_title, esc_names, char_names)
    char_hint = ", ".join(active_chars) if active_chars else "el protagonista"
    visual_beats = [
        f"Plano general de situación en {primary_esc}: se presenta a {char_hint} en un ambiente tranquilo y cercano, situando al espectador mientras arranca la narración.",
        f"Acercamiento suave sobre {char_hint} en {primary_esc}: se aprecia su expresión, postura y detalles principales en movimiento natural para acompañar el relato.",
        f"Plano de interacción o desplazamiento dentro de {primary_esc}: {char_hint} avanza o realiza un gesto cercano hacia la cámara/luz antes del cierre."
    ]
    transitions = [
        "",
        f"Desde el plano general anterior, la cámara se acerca suavemente sin perder la continuidad dentro de {primary_esc}.",
        f"Continuando desde la escena anterior, el encuadre acompaña el movimiento de {char_hint} hacia la luz de {primary_esc}."
    ]
    sentences_raw = [s.strip() for s in re.split(r'(?<=[.!?])\s+', (text or "").strip()) if s.strip()]
    if not sentences_raw:
        sentences_raw = [(text or "").strip()]
    chunk_len = max(1, (len(sentences_raw) + n - 1) // n)
    bloques = []
    total = 0
    for i in range(n):
        dur = 6 if n <= 2 else 5
        total += dur
        s_idx = i * chunk_len
        e_idx = s_idx + chunk_len if i < n - 1 else len(sentences_raw)
        narr_slice = " ".join(sentences_raw[s_idx:e_idx]).strip() if s_idx < len(sentences_raw) else ""
        bloques.append({
            "id": i + 1,
            "titulo": f"Escena {i + 1}",
            "transicion_desde_anterior": transitions[i % len(transitions)] if i > 0 else "",
            "que_ocurre": visual_beats[i % len(visual_beats)],
            "texto_narrado": narr_slice,
            "duracion_seg": dur
        })

    enfoque = (
        f"Corto narrativo sobre '{chapter_title}' pensado para {audiencia or 'todos los públicos'} "
        f"en {primary_esc} ({style_key}). Mientras la voz en off lee el texto del capítulo, la imagen "
        f"muestra a {char_hint} en {n} {'escena continua' if n == 1 else f'escenas progresivas (~{total}s)'} sin cambiar de lugar."
    )
    return {
        "enfoque_general": enfoque,
        "bloques": bloques,
        "duracion_total_seg": total
    }


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
    project_id: Optional[str] = None,
    propuesta: Optional[Dict[str, Any]] = None
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
    prop_clause = ""
    if propuesta and isinstance(propuesta, dict):
        enfoque = (propuesta.get("enfoque_general") or "").strip()
        bloques = propuesta.get("bloques") or []
        if enfoque or bloques:
            lines = [f"PROPUESTA APROBADA POR EL DIRECTOR (DEBES SEGUIRLA FIELMENTE):"]
            if enfoque:
                lines.append(f"- Enfoque general del vídeo: {enfoque}")
            for idx, b in enumerate(bloques):
                trans = (b.get("transicion_desde_anterior") or "").strip()
                trans_txt = f" [Paso desde la anterior: {trans}]" if (idx > 0 and trans) else ""
                narr_txt = (b.get("texto_narrado") or "").strip()
                narr_note = f" [Texto que leerá el narrador: \"{narr_txt}\"]" if narr_txt else ""
                esc_note = f" [Escenario: {b.get('escenario_clave')}]" if b.get("escenario_clave") else ""
                chars_note = f" [Personajes: {', '.join(b.get('personajes_en_escena', []))}]" if b.get("personajes_en_escena") else ""
                acc_note = f" [Acción en el vídeo 10s: {b.get('accion_video')}]" if b.get("accion_video") else ""
                lines.append(f"- Escena {idx+1} ({b.get('duracion_seg', 10)}s) [{b.get('titulo', '')}]{esc_note}{chars_note}{trans_txt}{narr_note}: {b.get('que_ocurre', '')}{acc_note}")
            prop_clause = "\n" + "\n".join(lines) + "\n"
            if len(bloques) > 0:
                target_scenes = len(bloques)

    system_instruction = f"""Eres un director audiovisual y guionista de vídeos cortos para TikTok, Reels y YouTube Shorts.
Tu trabajo es adaptar el texto del capítulo en exactamente {target_scenes} escenas dinámicas pensadas para formato vertical (9:16), asegurando que la imagen y el movimiento cuenten exactamente la historia de la narración.

{aud_clause}
{amb_clause}
{char_clause}
{esc_clause}
{prop_clause}

Estilo visual global de toda la serie: {style_prompt}.

Reglas de producción:
1. 'descripcion_escena': Descripción detallada en ESPAÑOL de la puesta en escena (cómo están situados los personajes en el escenario, relación con el entorno, objetos concretos del relato que aparecen y cómo continúa desde la escena anterior).
2. 'accion_video': Guion específico en ESPAÑOL de lo que sucede en movimiento durante los ~10 segundos del clip de vídeo (qué hacen físicamente Platero y los personajes en ese entorno mientras habla el narrador y cómo se mueve la cámara).
3. 'narrador': Texto exacto que dirá la voz en off en español para esta escena (frases completas cerradas en punto, respetando fielmente el tramo asignado en la propuesta).
4. 'prompt_imagen': Prompt en INGLÉS en 5 capas (1. Encuadre 9:16, 2. Personajes y postura exacta, 3. Objetos y detalles narrativos del texto, 4. Escenario recurrente con cielo completo sin márgenes blancos, 5. Iluminación y {style_prompt}). Sin textos escritos en la imagen.
5. 'prompt_video': Prompt conciso en INGLÉS (2-3 frases) enfocado EXCLUSIVAMENTE en la acción física de los personajes y el movimiento de cámara para el motor Image-to-Video (Kling), traduciendo 'accion_video'.
6. 'personajes_en_escena': Lista de nombres de los personajes que aparecen en esta escena (ej: ["Platero", "El Poeta / Yo lírico"]).
7. 'escenario_clave': Nombre exacto del escenario recurrente del universo donde ocurre esta escena.
8. 'duracion_estimada': Duración estimada en segundos (~10-13s).

Devuelve ÚNICAMENTE un array JSON válido con la siguiente estructura, sin texto adicional ni markdown:
[
  {{
    "id": 1,
    "descripcion_escena": "...",
    "accion_video": "...",
    "narrador": "...",
    "prompt_imagen": "...",
    "prompt_video": "...",
    "personajes_en_escena": ["..."],
    "escenario_clave": "...",
    "duracion_estimada": 10
  }}
]
"""

    user_prompt = f"Texto del capítulo a adaptar:\n\n{text}"

    # 1. Intentar con cascada LLM (OpenAI -> Fal Any-LLM -> Pollinations OpenAI-compatible)
    try:
        raw_content = _call_llm_chat(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=2200,
            api_key=openai_key,
        )
        cleaned = clean_json_string(raw_content)
        scenes = json.loads(cleaned)
        if isinstance(scenes, list) and len(scenes) > 0:
            prop_bloques = (propuesta.get("bloques") or []) if isinstance(propuesta, dict) else []
            for i, sc in enumerate(scenes):
                b_match = prop_bloques[i] if i < len(prop_bloques) else {}
                sc["id"] = i + 1
                trans_text = (b_match.get("transicion_desde_anterior") or "").strip()
                que_text = (b_match.get("que_ocurre") or "").strip()
                if not (sc.get("descripcion_escena") or "").strip():
                    if i > 0 and trans_text and que_text:
                        sc["descripcion_escena"] = f"Transición desde la escena anterior: {trans_text}\n\nQué ocurre: {que_text}"
                    elif que_text:
                        sc["descripcion_escena"] = que_text
                if not (sc.get("narrador") or "").strip() and (b_match.get("texto_narrado") or "").strip():
                    sc["narrador"] = b_match.get("texto_narrado").strip()
                sc["narrador"] = _normalize_pdf_line_breaks(sc.get("narrador") or "").replace("\n\n", " ")
                if not (sc.get("accion_video") or "").strip() and (b_match.get("accion_video") or "").strip():
                    sc["accion_video"] = b_match.get("accion_video").strip()
                if not (sc.get("escenario_clave") or "").strip() and (b_match.get("escenario_clave") or "").strip():
                    sc["escenario_clave"] = b_match.get("escenario_clave").strip()
                if not sc.get("personajes_en_escena") and b_match.get("personajes_en_escena"):
                    sc["personajes_en_escena"] = b_match.get("personajes_en_escena")
                sc.setdefault("descripcion_escena", "")
                sc.setdefault("accion_video", "")
                sc.setdefault("prompt_imagen", "")
                sc.setdefault("prompt_video", "")
                sc.setdefault("personajes_en_escena", [])
                if b_match.get("duracion_seg"):
                    try:
                        sc["duracion_estimada"] = int(b_match.get("duracion_seg"))
                    except (TypeError, ValueError):
                        sc.setdefault("duracion_estimada", 10)
                else:
                    sc.setdefault("duracion_estimada", 10)
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
        print(f"[AI] Error llamando a cascada LLM en breakdown_storyboard: {e}. Activando fallback heurístico.")

    # 2. Fallback Heurístico
    return generate_fallback_storyboard(
        text=text,
        characters=effective_chars,
        character_desc=character_desc,
        style_prompt=style_prompt,
        target_scenes=target_scenes,
        ambiente=ambiente,
        escenarios=escenarios,
        project_id=project_id,
        propuesta=propuesta
    )

def generate_fallback_storyboard(
    text: str,
    characters: Optional[List[Dict[str, Any]]],
    character_desc: str,
    style_prompt: str,
    target_scenes: int,
    ambiente: str = "",
    escenarios: Optional[List[Dict[str, Any]]] = None,
    project_id: Optional[str] = None,
    propuesta: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Generador heurístico de escenas en caso de no contar con API Key activa."""
    effective_chars = characters if (characters and len(characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    scene_chunks = split_narration_into_scenes(text, target_scenes)
    if not scene_chunks or not any(c.strip() for c in scene_chunks):
        scene_chunks = [
            "En un mundo donde cada segundo cuenta, una decisión puede cambiarlo todo.",
            "Los secretos guardados durante años comienzan a salir a la luz.",
            "El camino hacia la verdad nunca estuvo exento de peligros.",
            "Al final, solo aquellos que se atreven a avanzar logran cruzar el umbral."
        ]

    esc_names_fb = [e.get("nombre", "") for e in (escenarios or []) if e.get("nombre")]
    primary_esc_fb, _ = _pick_primary_scenario_and_chars(text, "", esc_names_fb, [])
    scenes = []

    prop_bloques = (propuesta.get("bloques") or []) if isinstance(propuesta, dict) else []
    for i in range(target_scenes):
        b_match = prop_bloques[i] if i < len(prop_bloques) else {}
        chunk_fb = scene_chunks[i] if i < len(scene_chunks) else scene_chunks[-1]
        narrador = _normalize_pdf_line_breaks((b_match.get("texto_narrado") or "").strip() or chunk_fb).replace("\n\n", " ")
        trans_text_fb = (b_match.get("transicion_desde_anterior") or "").strip()
        que_text_fb = (b_match.get("que_ocurre") or "").strip()
        if i > 0 and trans_text_fb and que_text_fb:
            desc_escena = f"Transición desde la escena anterior: {trans_text_fb}\n\nQué ocurre: {que_text_fb}"
        elif que_text_fb:
            desc_escena = que_text_fb
        else:
            desc_escena = f"Escena {i+1}: {narrador}"
        dur_seg = b_match.get("duracion_seg") or 5

        # Detectar personajes mencionados en el fragmento o en la propuesta o usar el protagonista
        detected_names = []
        que_text_fb = (b_match.get("que_ocurre") or "").strip()
        search_pool = f"{narrador} {que_text_fb}".lower()
        if effective_chars:
            for c in effective_chars:
                c_name = c.get("nombre", "")
                base_token = c_name.split("(")[0].strip().lower()
                if base_token and base_token in search_pool:
                    detected_names.append(c_name)
            if not detected_names:
                detected_names = [effective_chars[0]["nombre"]]

        esc_name = primary_esc_fb if esc_names_fb else None
        desc_escena = generate_scene_description_from_proposal(
            scene_index=i,
            propuesta=propuesta,
            characters_in_scene=detected_names,
            project_characters=effective_chars,
            escenario_clave=esc_name,
            project_escenarios=escenarios,
            narrador=narrador,
            chapter_text=text,
            ambiente=ambiente,
            project_id=project_id,
        )

        base_prompt = _translate_spanish_staging_to_english(
            desc_es=desc_escena,
            selected_names=detected_names,
            esc_name=esc_name or "the main setting",
            scene_index=i,
            transicion_es=trans_text_fb,
        )
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
            "descripcion_escena": desc_escena,
            "narrador": narrador,
            "prompt_imagen": enriched_prompt,
            "personajes_en_escena": detected_names,
            "escenario_clave": esc_name or "General",
            "duracion_estimada": int(dur_seg) if str(dur_seg).isdigit() else 5,
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


def _translate_spanish_staging_to_english(
    desc_es: str,
    selected_names: List[str],
    esc_name: str,
    scene_index: int = 0,
    transicion_es: str = "",
) -> str:
    """Convierte la puesta en escena y transición en español en directivas visuales en inglés claras para FLUX cuando no hay cuota LLM."""
    lower_d = (desc_es or "").lower()
    shot_type = "Medium full vertical shot"
    if "primer plano" in lower_d or "rostro" in lower_d or "cara" in lower_d or "acerca" in lower_d:
        shot_type = "Warm medium close-up shot with gentle camera push-in"
    elif "plano general" in lower_d or "panorámic" in lower_d:
        shot_type = "Wide establishing vertical shot"

    actions = []
    if "camina" in lower_d or "desplaza" in lower_d or "avanza" in lower_d or "mueve" in lower_d or "puerta" in lower_d:
        actions.append("walking gently forward towards the sunlit wooden doorway with natural graceful movement")
    if "acaricia" in lower_d or "junto" in lower_d or "interact" in lower_d or "mirad" in lower_d or "cómplice" in lower_d:
        actions.append("interacting tenderly side by side with affectionate expressions and warm eye contact")
    if "come" in lower_d or "pesebre" in lower_d or "heno" in lower_d:
        actions.append("standing near the rustic wooden manger with golden hay")
    if not actions:
        actions.append("positioned naturally in the scene with expressive storybook posture and warm lighting")

    trans_clause = ""
    if scene_index > 0 and transicion_es:
        trans_clause = f"[Transición Escena {scene_index}→{scene_index + 1}: {transicion_es}] Continuous visual flow from Scene {scene_index}, maintaining identical lighting, environment geometry and character proportions, "
    elif scene_index == 0:
        trans_clause = "[Escena 1: Plano inicial de apertura] Opening scene establishing the setting and characters, "

    subj = " and ".join(selected_names) if selected_names else "the main character"
    return f"{trans_clause}{shot_type} showing {subj} {', '.join(actions)}"


def generate_scene_prompt_from_description(
    descripcion_escena: str,
    characters_in_scene: Optional[List[str]] = None,
    project_characters: Optional[List[Dict[str, Any]]] = None,
    escenario_clave: Optional[str] = None,
    project_escenarios: Optional[List[Dict[str, Any]]] = None,
    style_key: str = "cinematic",
    style_details: str = "",
    ambiente: str = "",
    audiencia: str = "",
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    scene_index: int = 0,
    propuesta: Optional[Dict[str, Any]] = None,
) -> str:
    """Genera un prompt visual en inglés 9:16 a partir de la descripción de la escena, semillas de personajes/escenario y transiciones."""
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style

    effective_chars = project_characters if (project_characters and len(project_characters) > 0) else load_character_bank_for_prompt_generator(project_id)
    selected_names = [n for n in (characters_in_scene or []) if n]
    selected_chars = [
        c for c in (effective_chars or [])
        if any(c.get("nombre", "").lower() == n.lower() or (c.get("id") and c.get("id", "").lower() == n.lower()) for n in selected_names)
    ]
    char_clause = format_character_bible(selected_chars or effective_chars, "", project_id=project_id or "")
    esc_clause = format_environment_bible(project_escenarios)

    prop = propuesta if isinstance(propuesta, dict) else {}
    bloques = prop.get("bloques") or []
    b_match = bloques[scene_index] if (isinstance(bloques, list) and 0 <= scene_index < len(bloques)) else {}
    transicion_es = (b_match.get("transicion_desde_anterior") or "").strip()
    if not transicion_es and scene_index > 0 and descripcion_escena:
        m_tr = re.search(r"(?:Continuidad|Transici[óo]n)[^:]*:\s*([^\n.]+)", descripcion_escena, flags=re.IGNORECASE)
        if m_tr:
            transicion_es = m_tr.group(1).strip()

    raw_desc = (descripcion_escena or "").strip()
    base_english = ""
    if raw_desc:
        try:
            prompt = f"""Eres un director de arte y diseñador de prompts cinematográficos en formato vertical 9:16 (FLUX Kontext / Midjourney).

OBJETIVO:
Redactar en INGLÉS un prompt visual rico en detalles y dividido en 5 capas integradas en un único párrafo fluido para la Escena {scene_index + 1}.

PARÁMETROS DE LA OBRA:
- Estilo visual obligatorio: {style_prompt}
- Ambiente/universo: {ambiente or 'Fiel al libro'}
- Escenario fijado: {escenario_clave or 'General'}
- Personajes en escena: {', '.join(selected_names) if selected_names else 'Según descripción'}
- Continuidad con escena anterior: {transicion_es if (scene_index > 0 and transicion_es) else 'Plano de apertura'}

BIBLIA DE PERSONAJES Y ESCENARIOS:
{char_clause}
{esc_clause}

DESCRIPCIÓN DE LA ESCENA EN ESPAÑOL (QUÉ OCURRE Y QUÉ OBJETOS/DETALLES APARECEN):
"{raw_desc}"

ESTRUCTURA OBLIGATORIA DE LAS 5 CAPAS EN INGLÉS (en un solo párrafo sin encabezados ni corchetes):
1. Shot & Camera: Vertical 9:16 framing, camera angle and depth of field.
2. Characters & Action: Exact physical appearance and concrete action/pose of each character present (anatomically accurate, separate bodies).
3. Narrative Props & Foreground Details: Every specific object, flower, fruit, lantern, insect or detail mentioned in the scene description.
4. Environment & Full Sky: Full-bleed background of {escenario_clave or 'the setting'} with a complete painted sky (never leave blank white sky or margins).
5. Lighting, Color Palette & Artistic Medium: Atmospheric lighting and {style_prompt}, zero text or watermarks.
"""
            generated = _call_llm_chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.45,
                max_tokens=420,
                api_key=openai_key,
            ).strip().strip('"').strip("'")
            if generated:
                base_english = generated
        except Exception as e:
            print(f"[AI] Error generando prompt desde descripción: {e}")

    if not base_english:
        base_english = _translate_spanish_staging_to_english(
            desc_es=raw_desc,
            selected_names=selected_names,
            esc_name=escenario_clave or "the main setting",
            scene_index=scene_index,
            transicion_es=transicion_es,
        )

    return enrich_scene_prompt_with_anchors(
        scene_prompt=base_english or "Vertical 9:16 storybook scene",
        characters_in_scene=selected_names,
        project_characters=effective_chars or [],
        escenario_clave=escenario_clave,
        project_escenarios=project_escenarios or [],
        style_prompt=style_prompt,
        project_id=project_id,
    )


def generate_scene_description_from_proposal(
    scene_index: int = 0,
    propuesta: Optional[Dict[str, Any]] = None,
    characters_in_scene: Optional[List[str]] = None,
    project_characters: Optional[List[Dict[str, Any]]] = None,
    escenario_clave: Optional[str] = None,
    project_escenarios: Optional[List[Dict[str, Any]]] = None,
    narrador: str = "",
    chapter_text: str = "",
    ambiente: str = "",
    audiencia: str = "",
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Genera una descripción detallada en español de todo lo que aparece y sucede en la escena a partir de la propuesta de arriba, personajes y escenario."""
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    effective_chars = project_characters if (project_characters and len(project_characters) > 0) else load_character_bank_for_prompt_generator(project_id)

    prop = propuesta if isinstance(propuesta, dict) else {}
    enfoque = (prop.get("enfoque_general") or "").strip()
    bloques = prop.get("bloques") or []
    b_match = bloques[scene_index] if (isinstance(bloques, list) and 0 <= scene_index < len(bloques)) else {}

    que_ocurre = (b_match.get("que_ocurre") or "").strip()
    transicion = (b_match.get("transicion_desde_anterior") or "").strip()
    texto_narr = (b_match.get("texto_narrado") or narrador or "").strip()
    dur_seg = b_match.get("duracion_seg") or 5

    selected_names = [n for n in (characters_in_scene or []) if n]
    selected_chars = [
        c for c in (effective_chars or [])
        if any(c.get("nombre", "").lower() == n.lower() or (c.get("id") and c.get("id", "").lower() == n.lower()) for n in selected_names)
    ]
    if not selected_chars and effective_chars:
        for c in effective_chars:
            c_name = c.get("nombre", "")
            base_tok = c_name.split("(")[0].strip().lower()
            if base_tok and (base_tok in que_ocurre.lower() or base_tok in texto_narr.lower()):
                selected_chars.append(c)
                if c_name not in selected_names:
                    selected_names.append(c_name)

    esc_obj = None
    for e in (project_escenarios or []):
        if escenario_clave and e.get("nombre", "").lower() == escenario_clave.lower():
            esc_obj = e
            break
    esc_name = (esc_obj.get("nombre") if esc_obj else None) or escenario_clave or "el escenario principal"
    esc_desc = (esc_obj.get("descripcion") or esc_obj.get("prompt_base") or "").strip() if esc_obj else ""

    try:
        char_summary = "\n".join(
            f"- {c.get('nombre')}: {c.get('descripcion_visual') or c.get('descripcion') or 'Personaje de la obra'}"
            for c in selected_chars
        ) or "Según propuesta"
        prompt = f"""Eres un director de animación y realizador audiovisual.
Tu tarea es redactar en ESPAÑOL la DESCRIPCIÓN DETALLADA DE LA ESCENA {scene_index + 1} (duración aprox. {dur_seg}s), desarrollando con todo detalle lo que se ve y se mueve en pantalla mientras el narrador dice su frase.

CONTEXTO DE LA ESCENA:
- Enfoque general: {enfoque or 'Adaptación visual fiel y cálida'}
- Resumen en propuesta: {que_ocurre or 'Acción principal del tramo'}
- Transición desde la escena anterior: {transicion if scene_index > 0 and transicion else 'Inicio del vídeo (Escena 1)'}
- Frase exacta que lee el narrador en esta escena: "{texto_narr}"

ELEMENTOS SELECCIONADOS PARA ESTA ESCENA:
- Escenario: {esc_name} {f'({esc_desc})' if esc_desc else ''}
- Personajes en escena:
{char_summary}
- Ambiente general: {ambiente or 'Fiel al libro'} | Público: {audiencia or 'General'}

INSTRUCCIONES:
Redacta un párrafo rico y visual en español (4 a 6 frases, sin encabezados markdown ni comillas) que describa:
1. El encuadre inicial dentro de {esc_name}, la hora del día y la iluminación.
2. Qué personajes aparecen ({', '.join(selected_names) or 'los protagonistas'}), qué objetos concretos mencionados por el narrador están visibles (flores, frutas, mariposas, faroles, caminos...) y qué acción física realizan.
3. Cómo se mueven los personajes y la cámara durante los {dur_seg} segundos de la escena.
"""
        generated = _call_llm_chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=420,
            api_key=openai_key,
        ).strip()
        if generated:
            return generated
    except Exception as e:
        print(f"[AI] Error generando descripción detallada con LLM: {e}. Usando desarrollo estructurado.")

    # Desarrollo detallado estructurado en español (cuando no hay cuota de OpenAI o sin conexión)
    parts = []
    if scene_index > 0 and transicion:
        parts.append(f"Continuidad desde la escena anterior: {transicion.rstrip('.')}.")
    else:
        parts.append(f"La escena se sitúa en {esc_name}{f' ({esc_desc.rstrip(chr(46))})' if esc_desc else ''}, bajo una atmósfera {ambiente or 'cálida y envolvente'}.")

    if que_ocurre:
        parts.append(f"En pantalla, {que_ocurre[0].lower() + que_ocurre[1:] if len(que_ocurre) > 1 else que_ocurre}")

    if selected_chars:
        char_details = []
        for c in selected_chars:
            c_nom = c.get("nombre", "")
            c_vis = (c.get("descripcion_visual") or c.get("descripcion") or "").strip().rstrip(".")
            if c_vis:
                char_details.append(f"{c_nom} ({c_vis})")
            else:
                char_details.append(c_nom)
        if len(selected_chars) == 1:
            parts.append(
                f"Aparece en primer término {char_details[0]}, desplazándose con naturalidad por {esc_name}, mostrando gestos expresivos y cercanos a cámara."
            )
        else:
            parts.append(
                f"Participan e interactúan en el plano {', '.join(char_details[:-1])} y {char_details[-1]}: se mueven de forma coordinada dentro de {esc_name}, intercambiando miradas y gestos cómplices que transmiten cercanía."
            )
    elif selected_names:
        parts.append(f"Aparecen en escena {', '.join(selected_names)}, moviéndose e interactuando con naturalidad dentro de {esc_name}.")

    if enfoque:
        parts.append(f"El encuadre vertical 9:16 y la iluminación acompañan el tono general ({enfoque.rstrip('.')}) durante los {dur_seg} segundos mientras el narrador recita su tramo.")

    return " ".join(parts)
