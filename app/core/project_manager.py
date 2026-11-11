import os
import json
import time
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from app.core.document_parser import parse_document
from app.core.image_engine import generate_image, crop_and_resize_to_vertical, remove_image_background
from app.core.script_generator import (
    STYLE_PRESETS,
    clean_json_string,
    extract_character_visual_anchor,
    get_character_consistency_tokens,
    compute_character_seed
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROYECTOS_DIR = BASE_DIR / "proyectos"
PROYECTOS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR = BASE_DIR / "app" / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ENV_PATH = BASE_DIR / ".env"

def slugify(text: str) -> str:
    """Genera un slug limpio y seguro para nombres de carpetas y archivos en Windows."""
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('ascii').lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text)
    return text.strip('_') or f"proyecto_{int(time.time())}"

def get_project_folder(project_id: str) -> Path:
    """Obtiene o crea la carpeta física de un proyecto asegurando la estructura de capas."""
    # Buscar si ya existe una carpeta coincidente (incluso con acentos antiguos)
    target = PROYECTOS_DIR / project_id
    if not target.exists():
        for d in PROYECTOS_DIR.iterdir():
            if d.is_dir() and (d.name == project_id or slugify(d.name) == slugify(project_id)):
                target = d
                break

    target.mkdir(parents=True, exist_ok=True)
    (target / "documentos").mkdir(parents=True, exist_ok=True)
    (target / "capitulos").mkdir(parents=True, exist_ok=True)
    (target / "personajes").mkdir(parents=True, exist_ok=True)
    (target / "escenarios").mkdir(parents=True, exist_ok=True)
    return target

def format_file_size(size_bytes: int) -> str:
    """Convierte bytes a formato legible (KB, MB)."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.0f} KB"
    return f"{size_bytes} B"

def list_all_projects() -> List[Dict[str, Any]]:
    """Lista todos los proyectos / libros registrados en el disco con estadísticas ricas para el selector."""
    projects = []
    for item in sorted(PROYECTOS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if item.is_dir():
            meta_file = item / "proyecto.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue
            else:
                data = {
                    "id": item.name,
                    "titulo": item.name.replace("_", " ").title(),
                    "descripcion": "",
                    "audiencia": "Todos los públicos",
                    "ambiente": "",
                    "estilo_visual": "cinematic",
                    "estilo_detalles": "",
                    "voz_defecto": "eleven_george",
                    "personajes": [],
                    "escenarios": [],
                    "creado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "actualizado_en": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            data.setdefault("id", item.name)
            data.setdefault("audiencia", "Todos los públicos")
            data.setdefault("ambiente", "")
            data.setdefault("personajes", [])
            data.setdefault("escenarios", [])

            # Capítulos
            capitulos_dir = item / "capitulos"
            caps_count = len([c for c in capitulos_dir.iterdir() if c.is_dir()]) if capitulos_dir.exists() else 0
            data["capitulos_count"] = caps_count

            # Documentos en la carpeta documentos/
            docs_dir = item / "documentos"
            docs_files = sorted(docs_dir.glob("*.*"), key=os.path.getmtime, reverse=True) if docs_dir.exists() else []
            data["documentos_count"] = len(docs_files)
            if docs_files:
                first_doc = docs_files[0]
                data["documento_activo"] = {
                    "nombre": first_doc.name,
                    "tamano": format_file_size(first_doc.stat().st_size)
                }
            else:
                data["documento_activo"] = None

            # Miniaturas de personajes
            personajes_dir = item / "personajes"
            char_thumbs = []
            for p in data.get("personajes", []):
                p_id = p.get("id") or slugify(p.get("nombre", ""))
                png = personajes_dir / f"{p_id}.png"
                jpg = personajes_dir / f"{p_id}.jpg"
                if png.exists():
                    char_thumbs.append(f"/proyectos_data/{item.name}/personajes/{png.name}?t={int(png.stat().st_mtime)}")
                elif jpg.exists():
                    char_thumbs.append(f"/proyectos_data/{item.name}/personajes/{jpg.name}?t={int(jpg.stat().st_mtime)}")
            data["personajes_count"] = len(data.get("personajes", []))
            data["personajes_thumbnails"] = char_thumbs[:4]

            # Miniaturas de escenarios
            escenarios_dir = item / "escenarios"
            esc_thumbs = []
            for esc in data.get("escenarios", []):
                e_id = esc.get("id") or slugify(esc.get("nombre", ""))
                png = escenarios_dir / f"{e_id}.png"
                jpg = escenarios_dir / f"{e_id}.jpg"
                if png.exists():
                    esc_thumbs.append(f"/proyectos_data/{item.name}/escenarios/{png.name}?t={int(png.stat().st_mtime)}")
                elif jpg.exists():
                    esc_thumbs.append(f"/proyectos_data/{item.name}/escenarios/{jpg.name}?t={int(jpg.stat().st_mtime)}")
            data["escenarios_count"] = len(data.get("escenarios", []))
            data["escenarios_thumbnails"] = esc_thumbs[:3]

            projects.append(data)
    return projects

def get_project(project_id: str) -> Dict[str, Any]:
    """Obtiene los detalles completos de un proyecto, documentos, capítulos y biblia de personajes."""
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Proyecto con ID '{project_id}' no encontrado.")
    with open(meta_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.setdefault("audiencia", "Todos los públicos")
    data.setdefault("ambiente", "")
    data.setdefault("personajes", [])
    data.setdefault("personajes_recurrentes_texto", "")
    data.setdefault("escenarios", [])

    # Verificar si existen imágenes físicas para cada personaje y enriquecer con Banco de Consistencia (--cref / LoRA)
    personajes_dir = folder / "personajes"
    for p in data["personajes"]:
        p_id = p.get("id") or slugify(p.get("nombre", "char"))
        p["id"] = p_id
        p.setdefault("tipo", "humano")
        p.setdefault("prompt_retrato", "")
        p.setdefault("estado_aprobacion", "aprobado" if p.get("imagen_url") else "pendiente")
        p.setdefault("motivo_rechazo", "")
        p.setdefault("telegram_message_id", None)
        p.setdefault("aprobado_en", None)
        p.setdefault("propuesta_enviada_en", None)

        resolved_img_url = None
        resolved_file_path = None

        # Si ya tiene una imagen_url válida registrada y el archivo físico existe, respetarla
        if p.get("imagen_url"):
            clean_url = p["imagen_url"].split("?")[0]
            if clean_url.startswith(f"/proyectos_data/{folder.name}/personajes/"):
                fname = clean_url.split("/")[-1]
                target_f = personajes_dir / fname
                if target_f.exists() and target_f.stat().st_size > 2000:
                    resolved_img_url = f"/proyectos_data/{folder.name}/personajes/{fname}?t={int(target_f.stat().st_mtime)}"
                    resolved_file_path = f"proyectos/{folder.name}/personajes/{fname}"

        if not resolved_img_url:
            img_png = personajes_dir / f"{p_id}.png"
            img_jpg = personajes_dir / f"{p_id}.jpg"
            if img_jpg.exists() and img_jpg.stat().st_size > 2000:
                resolved_img_url = f"/proyectos_data/{folder.name}/personajes/{img_jpg.name}?t={int(img_jpg.stat().st_mtime)}"
                resolved_file_path = f"proyectos/{folder.name}/personajes/{img_jpg.name}"
            elif img_png.exists() and img_png.stat().st_size > 2000:
                resolved_img_url = f"/proyectos_data/{folder.name}/personajes/{img_png.name}?t={int(img_png.stat().st_mtime)}"
                resolved_file_path = f"proyectos/{folder.name}/personajes/{img_png.name}"

        p["imagen_url"] = resolved_img_url or p.get("imagen_url")
        p["hoja_referencia_path"] = resolved_file_path or p.get("hoja_referencia_path")
        tokens = get_character_consistency_tokens(p, project_id=folder.name)
        p["cref_url"] = tokens["cref_url"]
        p["cref_weight"] = tokens["cref_weight"]
        p["cref_directive"] = tokens["cref_directive"]
        p["lora_model"] = tokens["lora_model"]
        p["lora_weight"] = tokens["lora_weight"]
        p["lora_trigger"] = tokens["lora_trigger"]
        p["lora_directive"] = tokens["lora_directive"]
        p["ancla_visual"] = tokens["ancla_visual"]
        p["seed_consistencia"] = tokens["seed_consistencia"]

    # Verificar si existen imágenes físicas para escenarios en la carpeta escenarios/
    escenarios_dir = folder / "escenarios"
    escenarios_dir.mkdir(parents=True, exist_ok=True)
    for esc in data["escenarios"]:
        e_id = esc.get("id") or slugify(esc.get("nombre", "escenario"))
        esc["id"] = e_id
        esc.setdefault("tipo", "exterior_urbano")
        esc.setdefault("prompt_escenario", "")
        esc.setdefault("estado_aprobacion", "aprobado" if esc.get("imagen_url") else "pendiente")
        esc.setdefault("motivo_rechazo", "")
        esc.setdefault("telegram_message_id", None)
        esc.setdefault("aprobado_en", None)
        esc.setdefault("propuesta_enviada_en", None)
        img_png = escenarios_dir / f"{e_id}.png"
        img_jpg = escenarios_dir / f"{e_id}.jpg"
        if img_png.exists():
            esc["imagen_url"] = f"/proyectos_data/{folder.name}/escenarios/{img_png.name}?t={int(img_png.stat().st_mtime)}"
        elif img_jpg.exists():
            esc["imagen_url"] = f"/proyectos_data/{folder.name}/escenarios/{img_jpg.name}?t={int(img_jpg.stat().st_mtime)}"
        elif not esc.get("imagen_url"):
            esc["imagen_url"] = None

    data["capitulos"] = list_project_chapters(folder.name)

    # Detalle de documentos en documentos/
    docs_dir = folder / "documentos"
    doc_list = []
    doc_activo = None
    if docs_dir.exists():
        for d in sorted(docs_dir.glob("*.*"), key=os.path.getmtime, reverse=True):
            sz = d.stat().st_size
            d_obj = {
                "nombre": d.name,
                "tamano_bytes": sz,
                "tamano_formateado": format_file_size(sz),
                "mtime": int(d.stat().st_mtime)
            }
            doc_list.append(d_obj)
            if doc_activo is None:
                doc_activo = d_obj

    data["documentos"] = [d["nombre"] for d in doc_list]
    data["documentos_detalle"] = doc_list
    data["documento_activo"] = doc_activo

    # Auditoría visual de carpetas del proyecto
    videos_dir = folder / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    video_files = list(videos_dir.glob("*.mp4"))

    data["carpetas_estructura"] = {
        "raiz": str(folder),
        "documentos": {"ruta": str(docs_dir), "archivos": len(doc_list)},
        "personajes": {"ruta": str(personajes_dir), "total": len(data["personajes"])},
        "escenarios": {"ruta": str(escenarios_dir), "total": len(data["escenarios"])},
        "capitulos": {"ruta": str(folder / "capitulos"), "total": len(data["capitulos"])},
        "videos": {"ruta": str(videos_dir), "total": len(video_files)}
    }
    return data

def get_project_document_content(project_id: str, filename: Optional[str] = None) -> Dict[str, Any]:
    """Lee y analiza el documento guardado en la carpeta documentos/ del proyecto."""
    folder = get_project_folder(project_id)
    docs_dir = folder / "documentos"
    if not docs_dir.exists():
        raise FileNotFoundError("La carpeta documentos/ no existe en este proyecto.")

    if filename:
        target = docs_dir / filename
    else:
        files = sorted(docs_dir.glob("*.*"), key=os.path.getmtime, reverse=True)
        if not files:
            raise FileNotFoundError("No se encontró ningún documento guardado en este proyecto.")
        target = files[0]

    if not target.exists():
        raise FileNotFoundError(f"Archivo '{target.name}' no encontrado.")

    with open(target, "rb") as f:
        file_bytes = f.read()

    parsed = parse_document(file_bytes, target.name)
    parsed["saved_path"] = str(target)
    parsed["size_formatted"] = format_file_size(len(file_bytes))
    return parsed

def delete_project(project_id: str) -> bool:
    """Elimina permanentemente la carpeta de un proyecto."""
    folder = PROYECTOS_DIR / project_id
    if not folder.exists():
        for d in PROYECTOS_DIR.iterdir():
            if d.is_dir() and (d.name == project_id or slugify(d.name) == slugify(project_id)):
                folder = d
                break
    if folder.exists() and folder.is_dir():
        shutil.rmtree(folder)
        return True
    return False

def save_or_update_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea o actualiza la configuración global del proyecto en su carpeta."""
    title = project_data.get("titulo", "Nuevo Libro").strip()
    proj_id = project_data.get("id") or slugify(title)
    folder = get_project_folder(proj_id)
    meta_file = folder / "proyecto.json"

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    existing = {}
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    # Normalizar personajes asegurando que tengan un ID seguro, tipo y metadatos del Banco de Consistencia (--cref / LoRA)
    clean_characters = []
    personajes_dir = folder / "personajes"
    for idx, c in enumerate(project_data.get("personajes", existing.get("personajes", []))):
        c_id = c.get("id") or slugify(c.get("nombre") or f"char_{idx+1}")
        img_url = c.get("imagen_url")
        ref_path = c.get("hoja_referencia_path")
        if not img_url:
            if (personajes_dir / f"{c_id}.jpg").exists():
                img_url = f"/proyectos_data/{folder.name}/personajes/{c_id}.jpg?t={int((personajes_dir / f'{c_id}.jpg').stat().st_mtime)}"
                ref_path = f"proyectos/{folder.name}/personajes/{c_id}.jpg"
            elif (personajes_dir / f"{c_id}.png").exists():
                img_url = f"/proyectos_data/{folder.name}/personajes/{c_id}.png?t={int((personajes_dir / f'{c_id}.png').stat().st_mtime)}"
                ref_path = f"proyectos/{folder.name}/personajes/{c_id}.png"

        char_entry = {
            "id": c_id,
            "nombre": c.get("nombre", f"Personaje {idx+1}").strip(),
            "rol": c.get("rol", "").strip(),
            "tipo": c.get("tipo", "humano").strip().lower(),
            "descripcion_visual": c.get("descripcion_visual", "").strip(),
            "imagen_url": img_url,
            "hoja_referencia_path": ref_path,
            "prompt_retrato": c.get("prompt_retrato", "").strip(),
            "sin_fondo": c.get("sin_fondo", True) if c.get("sin_fondo") is not None else True,
            "formato_vista": c.get("formato_vista", "giro_360"),
            "cref_url": c.get("cref_url"),
            "cref_weight": int(c.get("cref_weight") if c.get("cref_weight") is not None else 100),
            "lora_model": c.get("lora_model"),
            "lora_weight": float(c.get("lora_weight") if c.get("lora_weight") is not None else 0.85),
            "lora_trigger": c.get("lora_trigger"),
            "ancla_visual": c.get("ancla_visual"),
            "seed_consistencia": c.get("seed_consistencia"),
            "estado_aprobacion": c.get("estado_aprobacion", "aprobado" if img_url else "pendiente"),
            "motivo_rechazo": c.get("motivo_rechazo", ""),
            "telegram_message_id": c.get("telegram_message_id"),
            "aprobado_en": c.get("aprobado_en"),
            "propuesta_enviada_en": c.get("propuesta_enviada_en")
        }
        tokens = get_character_consistency_tokens(char_entry, project_id=folder.name)
        char_entry["hoja_referencia_path"] = tokens["hoja_referencia_path"]
        char_entry["cref_url"] = tokens["cref_url"]
        char_entry["cref_weight"] = tokens["cref_weight"]
        char_entry["cref_directive"] = tokens["cref_directive"]
        char_entry["lora_model"] = tokens["lora_model"]
        char_entry["lora_weight"] = tokens["lora_weight"]
        char_entry["lora_trigger"] = tokens["lora_trigger"]
        char_entry["lora_directive"] = tokens["lora_directive"]
        char_entry["ancla_visual"] = tokens["ancla_visual"]
        char_entry["seed_consistencia"] = tokens["seed_consistencia"]
        clean_characters.append(char_entry)

    # Normalizar escenarios recurrentes
    clean_environments = []
    for idx, e in enumerate(project_data.get("escenarios", existing.get("escenarios", []))):
        e_id = e.get("id") or slugify(e.get("nombre") or f"esc_{idx+1}")
        clean_environments.append({
            "id": e_id,
            "nombre": e.get("nombre", f"Escenario {idx+1}").strip(),
            "tipo": e.get("tipo", "exterior_urbano").strip(),
            "descripcion_visual": e.get("descripcion_visual", "").strip(),
            "imagen_url": e.get("imagen_url"),
            "prompt_escenario": e.get("prompt_escenario", "").strip(),
            "estado_aprobacion": e.get("estado_aprobacion", "pendiente" if e.get("imagen_url") else "pendiente"),
            "motivo_rechazo": e.get("motivo_rechazo", ""),
            "telegram_message_id": e.get("telegram_message_id"),
            "aprobado_en": e.get("aprobado_en"),
            "propuesta_enviada_en": e.get("propuesta_enviada_en")
        })

    # Perfil del narrador
    default_narrator = {
        "nombre": "El Poeta / Muchacho de Moguer (Narrador Lírico)" if "platero" in proj_id.lower() else "Narrador Principal",
        "genero": "masculino",
        "edad_aprox": "12-14 años (Joven / Adolescente)" if "platero" in proj_id.lower() else "Adulto (30-40 años)",
        "rango_edad": "joven" if "platero" in proj_id.lower() else "adulto",
        "tono": "Lírico, contemplativo, tierno, pausado y reflexivo" if "platero" in proj_id.lower() else "Cálido y literario",
        "justificacion": "En Platero y yo el narrador es una voz lírica joven (el autor recordando su adolescencia en Moguer) en complicidad sensible con su borriquillo." if "platero" in proj_id.lower() else "Narrador general del universo.",
        "voz_recomendada": "openai_fable" if "platero" in proj_id.lower() else "eleven_george",
        "texto_muestra": "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro." if "platero" in proj_id.lower() else "Había una vez un lugar donde las historias cobraban vida."
    }
    incoming_narrator = project_data.get("perfil_narrador")
    existing_narrator = existing.get("perfil_narrador")
    final_narrator = incoming_narrator if incoming_narrator is not None else (existing_narrator or default_narrator)

    merged = {
        "id": folder.name,
        "titulo": title,
        "descripcion": project_data.get("descripcion", existing.get("descripcion", "")),
        "audiencia": project_data.get("audiencia", existing.get("audiencia", "Todos los públicos")),
        "ambiente": project_data.get("ambiente", existing.get("ambiente", "")),
        "estilo_visual": project_data.get("estilo_visual", existing.get("estilo_visual", "cinematic")),
        "estilo_detalles": project_data.get("estilo_detalles", existing.get("estilo_detalles", "")),
        "voz_defecto": project_data.get("voz_defecto", existing.get("voz_defecto", final_narrator.get("voz_recomendada", "openai_fable"))),
        "perfil_narrador": final_narrator,
        "personajes_recurrentes_texto": project_data.get("personajes_recurrentes_texto", existing.get("personajes_recurrentes_texto", "")),
        "personajes": clean_characters,
        "escenarios": clean_environments,
        "creado_en": existing.get("creado_en", now),
        "actualizado_en": now
    }

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return merged

def upload_project_document(project_id: str, file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Guarda un archivo Word/PDF en la carpeta documentos/ del proyecto y extrae su texto."""
    folder = get_project_folder(project_id)
    docs_dir = folder / "documentos"
    dest_path = docs_dir / filename

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    parsed = parse_document(file_bytes, filename)
    parsed["saved_path"] = str(dest_path)
    return parsed

def get_project_style_dna(project_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Devuelve las directivas canónicas de estilo inmutables para el proyecto.
    Garantiza que ningún prompt de personaje o escenario carezca de los términos clave
    de la técnica artística seleccionada.
    """
    style_key = project_data.get("estilo_visual", "watercolor")
    style_det = (project_data.get("estilo_detalles") or "").strip()

    if style_key == "watercolor":
        char_style = "delicate poetic watercolor and ink storybook illustration, soft artistic translucent color washes, rich textured paper grain, subtle sepia pencil and ink outlines, warm Mediterranean sunlight"
        scen_prefix = "Children's book watercolor illustration of"
        scen_style = "delicate poetic watercolor and ink storybook scenery, hand-painted watercolor art on textured paper, soft artistic translucent washes, subtle ink outlines, warm Mediterranean sunlight"
    elif style_key == "pixar_3d":
        char_style = "3D animated movie render, Pixar Disney animation style, soft volumetric subsurface scattering, expressive features, 4k 8k"
        scen_prefix = "3D animation movie background scenery of"
        scen_style = "Pixar Disney 3D animation style, volumetric soft lighting, rich stylized 3D textures, 4k render"
    elif style_key == "ghibli_anime":
        char_style = "Studio Ghibli aesthetic, Hayao Miyazaki hand-drawn anime character sheet, painterly details, warm nostalgic feel"
        scen_prefix = "Studio Ghibli style painterly anime background scenery of"
        scen_style = "Hayao Miyazaki anime aesthetic, lush painterly background art, soft nostalgic lighting, hand-drawn anime screencap"
    elif style_key == "noir_bw":
        char_style = "classic black and white film noir character sheet, dramatic high contrast monochrome, sharp Rembrandt chiaroscuro shadows, 35mm film grain"
        scen_prefix = "Black and white film noir background scenery of"
        scen_style = "classic monochrome 35mm film noir photography, dramatic high contrast chiaroscuro, deep Venetian blind shadows, foggy atmosphere"
    elif style_key == "comic":
        char_style = "graphic novel comic illustration, bold ink lines, dynamic comic book shading, expressive colors, Frank Miller style"
        scen_prefix = "Graphic novel comic background scenery of"
        scen_style = "bold ink outlines, dynamic comic book halftones, rich graphic novel palette, atmospheric comic scenery"
    else:
        # Default cinematic
        char_style = "cinematic 35mm character design, authentic film lighting, shallow depth of field, sharp photorealistic details"
        scen_prefix = "Cinematic 35mm film still scenic background of"
        scen_style = "cinematic atmospheric lighting, 35mm anamorphic lens, shallow depth of field, authentic film grain"

    if style_det and style_det.lower() not in char_style.lower():
        char_style = f"{char_style}, {style_det}"
        scen_style = f"{scen_style}, {style_det}"

    return {
        "style_key": style_key,
        "character_art_style": char_style,
        "scenery_prefix": scen_prefix,
        "scenery_art_style": scen_style
    }

_PROMPT_TRANSLATION_CACHE: Dict[str, str] = {}

def translate_visual_description_to_english(
    name: str,
    role_or_type: str,
    desc_es: str,
    category: str = "character",
    tipo: str = "humano",
    force_refresh: bool = False
) -> str:
    """
    Traduce e integra fielmente la descripción visual en español (del libro o del usuario)
    a descriptores visuales en inglés de alta calidad para modelos de difusión de imagen.
    - Preserva edad exacta (ej: 13 años), rasgos fisonómicos, vestimenta, colores y texturas.
    - Aísla la figura eliminando menciones a otros personajes o fondos externos en personajes.
    """
    if not desc_es or not desc_es.strip():
        if category == "character":
            return f"{name}, authentic {tipo} anatomy"
        return f"{name}, picturesque scenery"

    # Limpiar añadidos sobre fondo en español que el usuario pueda escribir manualmente
    clean_desc_es = re.sub(r'(?i)\b(sobre\s+)?fondo\s+(en\s+)?blanco\b', '', desc_es).strip(' ,.')

    cache_key = f"{category}:{name.strip().lower()}:{clean_desc_es.strip()}"
    if not force_refresh and cache_key in _PROMPT_TRANSLATION_CACHE:
        return _PROMPT_TRANSLATION_CACHE[cache_key]

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)

            if category == "character":
                system_content = (
                    "You are an expert prompt engineer for AI image generators. "
                    "Convert this Spanish visual character description into a concise, vivid English character appearance description "
                    "(age, physical features, anatomy, clothing/fur/plumage, colors, materials, props held).\n\n"
                    "CRITICAL RULES:\n"
                    "1. Describe ONLY this single character isolated by themselves. Strip out any mentions of other characters, companions, or outdoor scenery (e.g. donkeys, horses, dogs, fields, streets).\n"
                    "2. Faithfully preserve their exact age (e.g. 13 years old, child, teen), facial features, hair, clothing, and colors.\n"
                    "3. Do NOT mention camera views, background colors, aspect ratios, or artistic styles.\n"
                    "4. Output ONLY 1-2 concise, vivid sentences in English describing their physical appearance."
                )
                user_content = f"Character: {name}\nRole/Type: {role_or_type} ({tipo})\nDescription: {clean_desc_es}"
            else:
                system_content = (
                    "You are an expert prompt engineer for AI image generators. "
                    "Convert this Spanish scenery/environment description into a concise, vivid English location description "
                    "(architecture, foliage, materials, lighting, colors).\n\n"
                    "CRITICAL RULES:\n"
                    "1. Describe ONLY the physical place/environment. Ensure NO people or animals are mentioned.\n"
                    "2. Do NOT mention camera views, aspect ratios, or artistic styles.\n"
                    "3. Output ONLY 1-2 concise, vivid sentences in English describing the location."
                )
                user_content = f"Location: {name}\nType: {role_or_type}\nDescription: {clean_desc_es}"

            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                max_tokens=140
            )
            result = resp.choices[0].message.content.strip().replace('"', '')
            _PROMPT_TRANSLATION_CACHE[cache_key] = result
            return result
        except Exception as e:
            print(f"[PROMPT_TRANSLATE] Error traduciendo descripción con IA: {e}")

    # Fallback si no hay conexión o API
    clean_desc = clean_desc_es.strip()[:180].replace('"', '')
    if category == "character":
        return f"{name}, {clean_desc}, authentic {tipo} anatomy"
    return f"{name}, {clean_desc}"

def craft_character_portrait_prompt(
    character: Dict[str, Any],
    project_data: Dict[str, Any],
    formato_vista: str = "giro_360",
    sin_fondo: bool = True,
    force_refresh: bool = False
) -> str:
    """
    Genera un prompt de concepto de personaje en inglés optimizado y blindado con el ADN de estilo.
    - Traduce e integra la descripción visual en español del personaje (edad, fisionomía, ropas, colores).
    - Garantiza cuerpo completo visible de pies a cabeza (head to toe).
    - Si sin_fondo=True, garantiza fondo blanco puro (#FFFFFF) sin texturas de papel ni tintes amarillentos.
    - Hoja de giro 360 con 4 vistas completas en cuadrícula 2x2.
    """
    name = character.get("nombre", "Character").strip()
    role = character.get("rol", "").strip()
    desc = character.get("descripcion_visual", "").strip()
    tipo = character.get("tipo", "humano").lower().strip()

    # 1. Traducir fielmente la descripción visual en español a descriptores visuales en inglés
    translated_subject = translate_visual_description_to_english(
        name=name,
        role_or_type=role,
        desc_es=desc,
        category="character",
        tipo=tipo,
        force_refresh=force_refresh
    )

    lower_name = name.lower()
    lower_desc = desc.lower()
    lower_trans = translated_subject.lower()
    is_bird = "canario" in lower_name or "pájaro" in lower_desc or "bird" in lower_desc

    # 2. Guardas anatómicas y de cuerpo completo según especie y edad
    if is_bird:
        guard = "winged avian bird anatomy with fine beak, plumage and claws, full body standing perched head to claws, no humans, no quadrupeds"
    elif tipo == "animal" or any(w in f"{lower_name} {lower_desc}" for w in ["burro", "donkey", "perro", "dog", "galgo", "gato", "caballo", "animal"]):
        guard = "full body standing naturally on all four legs, authentic quadruped animal anatomy from hooves/paws to ears, complete animal body visible head to tail, no humans, no bipedal figures, no clothing"
    else:
        is_child = any(w in f"{lower_name} {lower_desc} {lower_trans}" for w in ["niño", "niña", "child", "boy", "girl", "joven", "young", "adolescente", "teen", "10", "11", "12", "13", "14", "15"])
        human_anatomy = "authentic human child/adolescent anatomy" if is_child else "authentic human anatomy"
        guard = f"{human_anatomy}, single individual, full body standing head to toe, entire body completely visible from shoes/feet to head, no cropped feet, no cropped head, complete standing posture, no other characters, no animals"

    subject = f"{translated_subject}, {guard}"

    # 3. ADN de estilo visual del universo
    dna = get_project_style_dna(project_data)
    art_clause = dna["character_art_style"]

    # 4. Cláusula de fondo: SI TIENE 'SIN FONDO' MARCADO (POR DEFECTO TRUE), FONDO BLANCO PURO AISLADO (#FFFFFF)
    if sin_fondo:
        # Asegurar que el estilo no introduzca grano de papel amarillento ni luz de fondo en el lienzo
        clean_art_clause = art_clause
        for paper_term in [
            "rich textured paper grain", "textured paper grain", "textured paper",
            "visible cold-press paper texture", "paper texture",
            "warm Mediterranean sunlight", "warm sunlight"
        ]:
            clean_art_clause = clean_art_clause.replace(paper_term, "").strip(", ")
        clean_art_clause = ", ".join([p.strip() for p in clean_art_clause.split(",") if p.strip()])
        art_clause = clean_art_clause

        bg_clause = (
            "centered composition with wide safety margins so no figures touch the borders, "
            "completely isolated on solid plain pure white background (#FFFFFF), "
            "stark white empty background, solid pure white canvas, blank white void, "
            "no paper texture, no parchment texture, no yellow tint, no shadows, no background elements, zero scenery, "
            "no text, no words, no labels, no title, no arrows, vertical composition, masterpiece, no 3D CGI, no photorealism"
        )
    else:
        bg_clause = (
            "centered composition, clean minimal neutral background, "
            "no text, no words, no labels, no title, no arrows, vertical composition, masterpiece"
        )

    # 5. Distribución en cuadrícula 2x2 para las 4 vistas completas (frente, perfil, girado y parte de atrás estilo La Niña)
    if formato_vista == "giro_360":
        if is_bird:
            views_clause = (
                "four distinct full-body turnaround views arranged neatly in a balanced 2x2 grid layout: "
                "top row showing front view perched facing forward and side profile view perched; "
                "bottom row showing three-quarters angle view perched and rear back view showing folded wings and tail feathers"
            )
        else:
            views_clause = (
                "four distinct full-body turnaround views arranged neatly in a balanced 2x2 grid layout: "
                "top row showing front view and side profile view; "
                "bottom row showing three-quarters angle view and rear back view, "
                "complete figures standing head to toe with boots resting on the floor in all four views"
            )
    elif formato_vista == "cuerpo_entero":
        views_clause = "full body standing portrait, complete figure standing head to toe, entire shoes and feet visible on the ground, full length shot, no cropped feet"
    else:
        views_clause = "character portrait, upper body bust view"

    return f"Character turnaround model sheet of {subject}, {views_clause}, {art_clause}, {bg_clause}"

def analyze_book_with_ai(
    text: str,
    project_id: Optional[str] = None,
    recurrent_chars_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analiza con IA el manuscrito/libro completo y deduce la Capa Genérica del Proyecto:
    - Audiencia recomendada
    - Ambiente / Universo del libro
    - Estilo visual sugerido y técnica de dibujo
    - Lista y biblia de personajes principales y recurrentes (con vistas completas y fondos aislados)
    - Lista y biblia de escenarios clave del entorno (localizaciones recurrentes sin personajes)
    - Tono de voz sugerido
    """
    openai_key = os.getenv("OPENAI_API_KEY")

    # Muestreo inteligente a lo largo de todo el manuscrito para captar personajes y escenarios de todo el libro
    if len(text) > 30000:
        step = len(text) // 5
        sample_text = (
            text[:10000] + "\n\n[...]\n\n" +
            text[step : step + 5000] + "\n\n[...]\n\n" +
            text[2 * step : 2 * step + 5000] + "\n\n[...]\n\n" +
            text[3 * step : 3 * step + 5000] + "\n\n[...]\n\n" +
            text[-5000:]
        ).strip()
    else:
        sample_text = text[:30000].strip()

    hint_clause = ""
    if recurrent_chars_hint and recurrent_chars_hint.strip():
        hint_clause = f"\n\nIMPORTANTE - PERSONAJES RECURRENTES PRIORITARIOS INDICADOS POR EL USUARIO:\n'{recurrent_chars_hint.strip()}'\nAsegúrate de incluir y caracterizar a todos estos personajes en el listado de 'personajes'."

    system_prompt = f"""Eres un director de producción artística y cinematográfica de élite para adaptaciones audiovisuales.
Analiza con máxima exhaustividad el manuscrito para extraer la 'BIBLIA GENERAL DEL UNIVERSO' (Capa Genérica de la obra):
{hint_clause}

REGLAS DE PROFUNDIDAD Y DETALLE OBLIGATORIAS:
1. AMBIENTE: No te limites a 1 o 2 frases. Redacta una descripción sensorial, profunda y evocadora (2 a 3 párrafos ricos) que defina la geografía, época, arquitectura, luz y cromatismo, sonidos, aromas del campo o ciudad, clima y tono emocional del universo narrativo.
2. PERSONAJES: Extrae entre 6 y 10 personajes recurrentes y figuras icónicas presentes en el manuscrito (protagonistas, compañeros animales, figuras del pueblo o secundarios memorables).
   Para cada personaje, redacta una 'descripcion_visual' en español exhaustiva (de 3 a 5 frases completas): fisonomía detallada, pelaje o indumentaria histórica, mirada, complexión física inmutable, rasgos de personalidad y citas o metáforas textuales directas del libro que lo definan con precisión artística.
   El 'prompt_retrato' debe ser en INGLÉS (máx 260 caracteres), describiendo al personaje de cuerpo entero en hoja de modelo aislada sobre fondo blanco puro: 'isolated on plain solid pure white background, vertical 9:16, masterpiece'.
3. ESCENARIOS: Extrae entre 5 y 8 escenarios principales y localizaciones recurrentes de la obra (calles, plazas, colinas, interiores, riberas, huertos).
   Para cada escenario, redacta una 'descripcion_visual' en español rica (2 a 4 frases completas): arquitectura, materiales, vegetación autóctona, tipo de luz y paleta de colores, sin personas.
   El 'prompt_escenario' debe ser en INGLÉS (máx 260 caracteres) para fondo escénico sin personas: 'scenic background art of ..., empty scene, no people, vertical 9:16 background scenery, masterpiece'.
4. DIRECCIÓN DE NARRACIÓN Y CASTING DE VOZ:
   Analiza en profundidad la voz que narra la obra (perspectiva literaria, edad, género y tono emocional).
   - En 'Platero y yo', el narrador es un joven/muchacho de Moguer de 12-14 años (o el poeta recordando su temprana adolescencia), con tono lírico, contemplativo, tierno y pausado. Exige una voz masculina juvenil (como 'openai_fable' o 'eleven_TX3LPaxmHKxFdv7VOQHJ'), NUNCA una voz adulta grave o dramática.
   - En cuentos infantiles o fantásticos: narrador juvenil, afectuoso y dinámico.
   - En novelas de misterio/thriller: narrador adulto, pausado o solemne.
   Deduce un objeto 'perfil_narrador' con:
     - "nombre": Nombre o denominación (ej: "El Poeta / Muchacho de Moguer (Narrador Lírico)")
     - "genero": "masculino" | "femenino" | "neutro"
     - "edad_aprox": ej: "12-14 años (Joven / Adolescente)"
     - "rango_edad": "infantil" | "joven" | "adulto" | "maduro"
     - "tono": Inflexión y estilo (ej: "Lírico, contemplativo, tierno, pausado y reflexivo")
     - "justificacion": Explicación literaria y psicológica razonada de por qué este narrador encaja con la obra (2-3 frases)
     - "voz_recomendada": ID de voz ideal (ej: "openai_fable", "eleven_TX3LPaxmHKxFdv7VOQHJ", "eleven_george", "eleven_sarah")
     - "texto_muestra": El fragmento más emblemático y conmovedor del libro (50 a 80 palabras) para audicionar la voz en el estudio interactivo.

Debes responder ÚNICAMENTE con un JSON válido con la siguiente estructura:
{{
  "titulo_sugerido": "Título sugerido para el proyecto",
  "descripcion_sugerida": "Sinopsis general del libro en 2 o 3 frases",
  "audiencia": "Una de: 'Infantil (Cuentos)' | 'Juvenil (Aventuras)' | 'Adultos (Thriller / Misterio)' | 'Todos los públicos'",
  "ambiente": "Descripción exhaustiva y sensorial del universo narrativo en 2-3 párrafos",
  "estilo_visual": "Clave: 'ghibli_anime' | 'watercolor' | 'storybook_kids' | 'cinematic' | 'anime' | 'pixar_3d' | 'noir_bw' | 'comic' | 'dark_fantasy' | 'vintage'",
  "estilo_detalles": "Detalles específicos de la técnica plástica, iluminación y paleta de colores",
  "voz_defecto": "openai_fable o eleven_TX3LPaxmHKxFdv7VOQHJ o eleven_george",
  "perfil_narrador": {{
    "nombre": "Nombre o denominación del narrador",
    "genero": "masculino o femenino o neutro",
    "edad_aprox": "ej: 12-14 años (Joven / Adolescente)",
    "rango_edad": "infantil o joven o adulto o maduro",
    "tono": "Tono e inflexión emocional",
    "justificacion": "Justificación literaria y psicológica del narrador",
    "voz_recomendada": "openai_fable",
    "texto_muestra": "Fragmento representativo del libro para prueba de voz"
  }},
  "personajes_recurrentes_texto": "Nombres y roles resumidos de los personajes recurrentes",
  "personajes": [
    {{
      "id": "slug_del_personaje",
      "nombre": "Nombre del personaje",
      "rol": "Rol (ej: Protagonista, Amigo y Narrador, Veterinario del pueblo, Galgo leal)",
      "tipo": "Uno de: 'humano' | 'animal' | 'criatura' | 'objeto'",
      "descripcion_visual": "Descripción literaria y visual profunda (3 a 5 frases completas con fisonomía, vestimenta/pelaje y citas del texto)",
      "prompt_retrato": "Prompt en INGLÉS para hoja de modelo aislada en fondo blanco puro ('isolated on plain solid pure white background, vertical 9:16, masterpiece')"
    }}
  ],
  "escenarios": [
    {{
      "id": "slug_del_escenario",
      "nombre": "Nombre del lugar (ej: Calles Blancas de Moguer, Colina del Molino de Viento)",
      "tipo": "Uno de: 'exterior_urbano' | 'naturaleza' | 'interior' | 'panoramica'",
      "descripcion_visual": "Descripción visual y arquitectónica detallada (2 a 4 frases completas con materiales, luz y vegetación sin personas)",
      "prompt_escenario": "Prompt en INGLÉS para fondo escénico sin personas ('scenic background art of ..., empty scene, no people, vertical 9:16 background scenery, masterpiece')"
    }}
  ]
}}
No incluyas texto explicativo fuera del bloque JSON."""

    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Texto del manuscrito:\n\n{sample_text}"}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            raw = response.choices[0].message.content or ""
            cleaned = clean_json_string(raw)
            result = json.loads(cleaned)
            if not result.get("personajes_recurrentes_texto") and result.get("personajes"):
                result["personajes_recurrentes_texto"] = ", ".join([f"{p['nombre']} ({p.get('rol', '')})" for p in result["personajes"]])
            return result
        except Exception as e:
            print(f"[AI] Error en análisis con OpenAI: {e}. Activando fallback heurístico.")

    # Fallback Heurístico con biblia rica y profunda
    lower = sample_text.lower()
    is_platero = "platero" in lower or "moguer" in lower or "borriquillo" in lower
    is_kids = is_platero or any(w in lower for w in ["niño", "niña", "burro", "bosque", "cuento", "pequeño"])
    
    if is_platero:
        audiencia = "Todos los públicos"
        estilo = "watercolor"
        estilo_det = "Acuarela poética con pigmentos transparentes, aguadas luminosas, contornos sutiles de lápiz y luz solar mediterránea"
        ambiente = (
            "Moguer y la campiña andaluza a comienzos del siglo XX, envueltos en una luz dorada y deslumbrante que baña las fachadas encaladas y las azoteas de cal blanca. "
            "El aire está impregnado de aromas campesinos: el azahar de los naranjales, el aroma resinoso de los pinares de Mazagón, la tierra seca al mediodía y el mosto dulce de las bodegas al caer la tarde.\n\n"
            "Un universo poético donde la sencillez rústica y el aislamiento provinciano conviven con una profunda contemplación lírica de la vida. "
            "Los caminos polvorientos, los olivares plateados bajo la brisa atlántica y el silencio solemne de las siestas crean una atmósfera nostálgica, tierna y teñida de serena melancolía."
        )
        personajes = [
            {
                "id": "platero",
                "nombre": "Platero",
                "rol": "Protagonista",
                "tipo": "animal",
                "descripcion_visual": "Platero es pequeño, peludo, suave; tan blando por fuera que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro. Anda con trotecillo alegre haciendo tintinear sus alforjas, acariciando con su belfo tibio las florecillas del camino. Es tierno y mimoso como un niño, pero recio y resistente por dentro como de piedra.",
                "prompt_retrato": "Full body character turnaround model sheet of Platero, small fluffy silver-grey Andalusian donkey with tender dark crystal eyes and soft cotton-like fur, four distinct views: front view, profile, 3/4 angle, and rear view, standing on all four legs, poetic watercolor illustration style, isolated on plain solid pure white background, vertical 9:16, masterpiece, no humans"
            },
            {
                "id": "el_poeta",
                "nombre": "El Poeta (Narrador)",
                "rol": "Compañero y Narrador Lírico",
                "tipo": "humano",
                "descripcion_visual": "Joven escritor y paseante solitario de Moguer, de mirada serena, profunda y melancólica. Viste camisa de lino crudo desabrochada al cuello, chaleco oscuro de paño fino y sombrero de ala ancha que le sombrea los ojos. Camina con paso tranquilo junto a Platero, observando con asombro reverente los detalles del campo andaluz y dialogando en silencios cómplices con su fiel borriquillo.",
                "prompt_retrato": "Full body character turnaround model sheet of young Spanish poet, contemplative sensitive face, worn dark waistcoat, rustic linen shirt, wide-brim Andalusian hat, four distinct views: front, side, 3/4 angle, rear, standing pose head to toe, poetic watercolor style, isolated on plain solid pure white background, vertical 9:16, masterpiece"
            },
            {
                "id": "diana",
                "nombre": "Diana",
                "rol": "Perrita Blanca Alegre",
                "tipo": "animal",
                "descripcion_visual": "La bella perra blanca que se parece a la luna creciente, ágil, estilizada y graciosa. De pelaje níveo inmaculado y orejas despiertas y móviles, corretea alocada entre las patas de Platero simulando mordisquearle con infinita ternura. Sus ojos castaños brillan con lealtad y viveza contagiosa ante cualquier paseo matinal.",
                "prompt_retrato": "Full body character turnaround model sheet of Diana, graceful slender white village dog like a crescent moon, pure white clean fur, alert posture, four distinct views, standing naturally, poetic watercolor style, isolated on plain solid pure white background, vertical 9:16, masterpiece, no humans"
            },
            {
                "id": "darbon",
                "nombre": "Darbón",
                "rol": "Médico Veterinario",
                "tipo": "humano",
                "descripcion_visual": "Darbón, el médico de Platero, es grande como el buey pío y rojo como una sandía madura. Pesa siete arrobas y cuando habla con su vozarrón cascado parece que se le van a caer las muelas. Viste jubón de pana parda, delantal manchado de ungüentos y botas de cuero de montar; bajo su corpulencia desmedida guarda un corazón tan tierno como una hogaza de pan recién horneada.",
                "prompt_retrato": "Full body character turnaround model sheet of Darbon, large burly elderly village veterinarian with red ruddy face, thick white beard, brown corduroy vest, four distinct views: front, side, 3/4 angle, back, poetic watercolor illustration, isolated on plain solid pure white background, vertical 9:16, masterpiece"
            },
            {
                "id": "lord",
                "nombre": "Lord",
                "rol": "Viejo Galgo Noble",
                "tipo": "animal",
                "descripcion_visual": "Viejo galgo inglés de porte aristocrático y mirada triste y sabia. De costillas marcadas bajo un pelaje atigrado y canoso alrededor del hocico, camina con lentitud solemne rememorando antiguas jornadas de caza. Acepta con dignidad paciente las caricias de Platero y busca los rincones más soleados del corral para sestear.",
                "prompt_retrato": "Full body character turnaround model sheet of Lord, dignified elderly brindle greyhound dog with white muzzle and wise gentle eyes, slender lean physique, four distinct views on all four legs, poetic watercolor style, isolated on plain solid pure white background, vertical 9:16, masterpiece, no humans"
            },
            {
                "id": "canario_verde",
                "nombre": "El Canario Verde",
                "rol": "Pájaro Cantor Libre",
                "tipo": "animal",
                "descripcion_visual": "Pajarillo menudo y vivaz de plumaje verde esmeralda con reflejos amarillos como limón fresco. Posee una mirada diminuta y vivaz como una semilla brillante y un pico fino siempre listo para desplegar un trino cristalino. Su presencia evoca la pureza del aire libre y el canto inocente ante los amaneceres primaverales.",
                "prompt_retrato": "Full body character turnaround model sheet of small emerald green canary bird with vibrant yellow plumage accents, perched posture, four distinct angles, poetic watercolor illustration, isolated on plain solid pure white background, vertical 9:16, masterpiece, no humans"
            },
            {
                "id": "la_nina_chica",
                "nombre": "La Niña Chica",
                "rol": "Amiga Angelical del Pueblo",
                "tipo": "humano",
                "descripcion_visual": "Niña menuda y angelical de Moguer, de mejillas sonrosadas, cabello rubio trenzado con cintas y ojos claros llenos de asombro infantil. Viste un sencillo vestidito de percal con delantal blanco de volantes y zapatitos gastados. Adora a Platero con devoción cándida, coronándole las orejas con guirnaldas de margaritas y dándole uvas frescas en la palma de su mano.",
                "prompt_retrato": "Full body character turnaround model sheet of La Nina Chica, sweet little Spanish girl with blonde braids, vintage percal dress with white pinafore apron, gentle smile, four distinct views head to toe, poetic watercolor style, isolated on plain solid pure white background, vertical 9:16, masterpiece"
            },
            {
                "id": "anilla_la_hungara",
                "nombre": "Anilla la Húngara",
                "rol": "Bailarina y Gitana Alegre",
                "tipo": "humano",
                "descripcion_visual": "Mujer de tez morena y ojos de brasa chispeante, llena de salero y vitalidad callejera. Luce faldas amplias de múltiples volantes de colores vivos, mantón de manila sobre los hombros y peineta de carey en el pelo negro ondulado. Al pasar por las esquinas hace sonar sus panderetas y castañuelas, provocando el trote curioso de Platero.",
                "prompt_retrato": "Full body character turnaround model sheet of Anilla, vibrant Andalusian gypsy dancer with dark expressive eyes, colorful flamenco ruffled skirt and shawl, tortoiseshell hair comb, four distinct views head to toe, poetic watercolor style, isolated on plain solid pure white background, vertical 9:16, masterpiece"
            }
        ]
        escenarios = [
            {
                "id": "calles_blancas_moguer",
                "nombre": "Calles Blancas y Azoteas de Moguer",
                "tipo": "exterior_urbano",
                "descripcion_visual": "Calles estrechas empedradas con guijarros de río, flanqueadas por casas encaladas de un blanco cegador con zócalos de azulejos andaluces. Balcones con rejas de hierro forjado repletos de geranios rojos, buganvillas moradas y macetas de albahaca, bajo un cielo azul cobalto sin una sola nube.",
                "prompt_escenario": "Scenic background art of cobblestone white village street in Moguer Andalusia, whitewashed houses, black wrought-iron balconies with red geraniums and purple bougainvillea, golden Mediterranean sunlight, empty street, no people, vertical 9:16 background scenery, masterpiece"
            },
            {
                "id": "colinas_molino_viento",
                "nombre": "Las Colinas y el Molino de Viento",
                "tipo": "naturaleza",
                "descripcion_visual": "Lomas onduladas tostadas por el estío y salpicadas de olivos plateados y viñas verdes. En la cumbre se alza un molino de viento tradicional de paredes redondas de piedra encalada y aspas de madera, recortándose solitario y majestuoso contra la inmensidad del horizonte.",
                "prompt_escenario": "Scenic background art of Andalusian rolling hills with silver olive trees and golden dry grass, an iconic whitewashed stone windmill with wooden blades on the crest, warm sunset horizon, empty landscape, no people, vertical 9:16 background scenery, masterpiece"
            },
            {
                "id": "pozo_viejo_huerto",
                "nombre": "El Pozo Viejo y el Huerto de los Frailes",
                "tipo": "naturaleza",
                "descripcion_visual": "Rincón umbrío y fresco de tapial antiguo cubierto de hiedra y madreselva. Un brocal de pozo de piedra gastada con su arco de hierro y cubo de zinc, rodeado por higueras centenarias, granados de frutos abiertos y una alberca de aguas verdes donde danzan los zapateros.",
                "prompt_escenario": "Scenic background art of an ancient rustic stone water well surrounded by lush fig trees, ivy-covered stone walls, wild oleanders, soft dappled garden sunlight, tranquil atmosphere, empty scene, no people, vertical 9:16 background scenery, masterpiece"
            },
            {
                "id": "establo_platero",
                "nombre": "El Establo y el Corral de Platero",
                "tipo": "interior",
                "descripcion_visual": "Cuadra rústica andaluza techada con tejas árabes y vigas de castaño oscurecido. El pesebre de pino gastado huele a heno fresco, alfalfa y paja dorada; rayos de luz solar entran por las hendiduras de la puerta de madera dibujando polvo brillante en el aire tibio.",
                "prompt_escenario": "Scenic background art of a cozy rustic Andalusian barn and donkey stable, wooden hay manger, golden clean straw, warm wooden beams, sunlight shafts piercing the dusty gentle shadow, empty stable, no people, vertical 9:16 background scenery, masterpiece"
            },
            {
                "id": "ribera_rio_tinto",
                "nombre": "La Ribera del Río Tinto y los Marjales",
                "tipo": "panoramica",
                "descripcion_visual": "Orillas misteriosas del río de aguas rojizas y cobrizas que reflejan el cielo atardecido con destellos de fuego y púrpura. Tierras bajas de marismas salpicadas de cañaverales mecidos por la brisa marina, con barcas pescadoras varadas en la arena fangosa.",
                "prompt_escenario": "Scenic background art of the Rio Tinto riverbank at dusk, deep reddish wine-colored water reflections, marshland reeds swaying in Atlantic breeze, distant dunes, evocative purple twilight sky, empty scenic landscape, no people, vertical 9:16 background scenery, masterpiece"
            }
        ]
        titulo_sug = "Platero y Yo"
        desc_sug = "Crónica lírica y entrañable de la vida en el pueblo andaluz de Moguer a través de las andanzas del poeta y su fiel burrito Platero."
        voz_sug = "openai_fable"
        perfil_narrador = {
            "nombre": "El Poeta / Muchacho de Moguer (Narrador Lírico)",
            "genero": "masculino",
            "edad_aprox": "12-14 años (Joven / Adolescente)",
            "rango_edad": "joven",
            "tono": "Lírico, contemplativo, tierno, pausado y reflexivo",
            "justificacion": "En Platero y yo el narrador es una voz lírica joven (el autor recordando su adolescencia en Moguer) en diálogo íntimo y confidente con su burrillo Platero. Requiere una voz juvenil masculina, melancólica y pausada, alejada de la pesadez o impostación de un narrador adulto convencional.",
            "voz_recomendada": "openai_fable",
            "texto_muestra": "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro."
        }
    elif is_kids:
        audiencia = "Infantil (Cuentos)"
        estilo = "ghibli_anime"
        estilo_det = "Ilustración suave de cuento con tonos cálidos, trazos orgánicos y estilo acuarela Studio Ghibli"
        ambiente = "Un mundo entrañable y pacífico de pueblos tradicionales rodeados de valles verdes, bosques misteriosos y cielos luminosos, donde la inocencia y el compañerismo guían cada aventura cotidiana."
        personajes = [
            {
                "id": "protagonista",
                "nombre": "Protagonista",
                "rol": "Aventurero Principal",
                "tipo": "humano",
                "descripcion_visual": "Joven curioso y vivaz con ropa práctica de viajero, ojos brillantes de asombro y sonrisa entusiasta.",
                "prompt_retrato": "Full body character turnaround of a cheerful young adventurer, Studio Ghibli style, pure plain white background, vertical 9:16, masterpiece"
            }
        ]
        escenarios = [
            {
                "id": "valle_verde",
                "nombre": "El Valle Verde",
                "tipo": "naturaleza",
                "descripcion_visual": "Praderas onduladas bañadas por el sol con arroyos cantarines y arboledas frondosas.",
                "prompt_escenario": "Studio Ghibli scenery, rolling green meadows, sparkling stream, sunny warm day, vertical 9:16, masterpiece, no people"
            }
        ]
        titulo_sug = "Aventuras en el Valle"
        desc_sug = "Un viaje entrañable de descubrimiento y amistad."
        voz_sug = "eleven_TX3LPaxmHKxFdv7VOQHJ"
        perfil_narrador = {
            "nombre": "Cuentacuentos Juvenil",
            "genero": "masculino",
            "edad_aprox": "14-16 años (Joven Aventurero)",
            "rango_edad": "joven",
            "tono": "Entusiasta, curioso, alegre y cercano",
            "justificacion": "Voz juvenil y vivaz que conecta de inmediato con la curiosidad y el sentido de maravilla infantil.",
            "voz_recomendada": "eleven_TX3LPaxmHKxFdv7VOQHJ",
            "texto_muestra": "En lo alto de la colina verde, donde la brisa soplaba entre las flores, comenzaba nuestra mayor aventura."
        }
    else:
        audiencia = "Todos los públicos"
        estilo = "cinematic"
        estilo_det = "Fotografía cinematográfica 35mm con iluminación natural de alto contraste y detalle granular"
        ambiente = "Un entorno cinematográfico de atmósferas envolventes, donde las luces y sombras marcan el paso de una historia intensa y visualmente impactante."
        personajes = [
            {
                "id": "personaje_principal",
                "nombre": "Personaje Principal",
                "rol": "Protagonista",
                "tipo": "humano",
                "descripcion_visual": "Figura carismática con mirada decidida, atuendo característico de su época y porte seguro.",
                "prompt_retrato": "Full body character turnaround, cinematic 35mm style, plain solid white background, vertical 9:16, masterpiece"
            }
        ]
        escenarios = [
            {
                "id": "escenario_principal",
                "nombre": "Localización Principal",
                "tipo": "exterior_urbano",
                "descripcion_visual": "Arquitectura emblemática con iluminación atmosférica y texturas realistas.",
                "prompt_escenario": "Cinematic 35mm scenic background art, architectural setting, empty scene, no people, vertical 9:16, masterpiece"
            }
        ]
        titulo_sug = "Historia sin título"
        desc_sug = "Adaptación narrativa en formato vertical basada en el manuscrito aportado."
        voz_sug = "eleven_george"
        perfil_narrador = {
            "nombre": "Narrador Cinematográfico",
            "genero": "masculino",
            "edad_aprox": "Adulto (35-45 años)",
            "rango_edad": "adulto",
            "tono": "Solemne, envolvente y cinematográfico",
            "justificacion": "Narrador clásico con timbre envolvente y gran calidez narrativa.",
            "voz_recomendada": "eleven_george",
            "texto_muestra": "La niebla cubría la ciudad cuando el último tren abandonó la estación en silencio."
        }

    return {
        "titulo_sugerido": titulo_sug,
        "descripcion_sugerida": desc_sug,
        "audiencia": audiencia,
        "ambiente": ambiente,
        "estilo_visual": estilo,
        "estilo_detalles": estilo_det,
        "voz_defecto": voz_sug,
        "perfil_narrador": perfil_narrador,
        "personajes_recurrentes_texto": ", ".join([f"{p['nombre']} ({p.get('rol', '')})" for p in personajes]),
        "personajes": personajes,
        "escenarios": escenarios
    }

def recommend_narrator_with_ai(project_id: str) -> Dict[str, Any]:
    """
    Analiza el proyecto y su manuscrito para recomendar con IA el perfil del narrador y la voz idónea.
    """
    proj = get_project(project_id)
    text_content = ""
    try:
        doc_data = get_project_document_content(project_id)
        text_content = doc_data.get("texto", "") or ""
    except Exception:
        pass

    if not text_content:
        text_content = f"{proj.get('titulo', '')}\n\n{proj.get('descripcion', '')}\n\n{proj.get('ambiente', '')}"

    analysis = analyze_book_with_ai(text_content, project_id=project_id)
    narrator = analysis.get("perfil_narrador")
    if not narrator:
        # Fallback inteligente si la IA devolvió solo voz_defecto
        is_platero = "platero" in proj.get("id", "").lower() or "platero" in text_content.lower()
        if is_platero:
            narrator = {
                "nombre": "El Poeta / Muchacho de Moguer (Narrador Lírico)",
                "genero": "masculino",
                "edad_aprox": "12-14 años (Joven / Adolescente)",
                "rango_edad": "joven",
                "tono": "Lírico, contemplativo, tierno, pausado y reflexivo",
                "justificacion": "En Platero y yo el narrador es una voz lírica joven (el autor recordando su adolescencia en Moguer) en diálogo íntimo y confidente con su burrillo Platero. Requiere una voz juvenil masculina, melancólica y pausada, alejada de la pesadez o impostación de un narrador adulto convencional.",
                "voz_recomendada": "openai_fable",
                "texto_muestra": "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro."
            }
        else:
            narrator = {
                "nombre": "Narrador Principal",
                "genero": "masculino",
                "edad_aprox": "Adulto (30-40 años)",
                "rango_edad": "adulto",
                "tono": "Cálido, envolvente y literario",
                "justificacion": "Narrador omnisciente estándar para relatos narrativos.",
                "voz_recomendada": "openai_fable",
                "texto_muestra": "Había una vez un lugar donde las historias cobraban vida."
            }
    return narrator

def generate_character_portrait(
    project_id: str,
    character_id: str,
    prompt_override: Optional[str] = None,
    sin_fondo: bool = True,
    formato_vista: str = "giro_360",
    descripcion_visual: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera el retrato o concepto completo de un personaje del proyecto.
    Soporta generación de cuerpo completo / giro 360 y recorte automático de fondo transparente (PNG).
    Garantiza fondo blanco puro aislado (#FFFFFF) y cuerpo completo (head-to-toe).
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    # Localizar el personaje
    char_match = None
    for c in project_data.get("personajes", []):
        if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id:
            char_match = c
            break

    if not char_match:
        raise ValueError(f"Personaje '{character_id}' no encontrado en el proyecto.")

    # Si se pasa una descripción visual actualizada desde la UI, actualizarla en el personaje
    if descripcion_visual and descripcion_visual.strip():
        char_match["descripcion_visual"] = descripcion_visual.strip()

    char_match["sin_fondo"] = sin_fondo
    char_match["formato_vista"] = formato_vista

    # Construir o usar prompt optimizado en inglés
    if prompt_override and prompt_override.strip():
        final_prompt = prompt_override.strip()
        # Asegurar directivas de fondo blanco y cuerpo completo si no están en el override
        if sin_fondo and "pure white background" not in final_prompt.lower():
            final_prompt += ", completely isolated on solid plain pure white background (#FFFFFF), stark white empty background, solid pure white canvas, zero scenery, no paper texture, no shadows"
        if formato_vista in ["giro_360", "cuerpo_entero"] and "full body" not in final_prompt.lower() and "head to toe" not in final_prompt.lower():
            final_prompt += ", full body standing head to toe, entire body completely visible from shoes to head, no cropped feet"
        char_match["prompt_retrato"] = final_prompt
    elif char_match.get("prompt_retrato") and char_match["prompt_retrato"].strip():
        final_prompt = char_match["prompt_retrato"].strip()
        if sin_fondo and "pure white background" not in final_prompt.lower():
            final_prompt += ", completely isolated on solid plain pure white background (#FFFFFF), stark white empty background, solid pure white canvas, zero scenery"
    else:
        final_prompt = craft_character_portrait_prompt(char_match, project_data, formato_vista=formato_vista, sin_fondo=sin_fondo, force_refresh=True)
        char_match["prompt_retrato"] = final_prompt

    # Generar imagen mediante el motor gráfico con fit_mode='contain' para no recortar vistas
    fit_mode = "contain" if (formato_vista == "giro_360" or sin_fondo) else "crop"
    img_res = generate_image(prompt=final_prompt, provider="flux", fit_mode=fit_mode)
    temp_file = Path(img_res["file_path"])

    personajes_dir = folder / "personajes"
    personajes_dir.mkdir(parents=True, exist_ok=True)

    # 1. Guardar siempre la hoja maestra completa en JPG de alta resolución
    master_jpg_path = personajes_dir / f"{character_id}.jpg"
    shutil.copy2(temp_file, master_jpg_path)

    # 2. Si se solicita sin fondo, procesar además con rembg para generar recorte transparente PNG
    png_path = personajes_dir / f"{character_id}.png"
    if sin_fondo:
        rem_ok = remove_image_background(temp_file, png_path)
        # Componer sobre lienzo blanco puro (#FFFFFF) para garantizar que el JPG maestro sea 100% blanco puro
        if rem_ok and png_path.exists():
            try:
                from PIL import Image
                with Image.open(png_path) as p_img:
                    white_canvas = Image.new("RGB", p_img.size, (255, 255, 255))
                    white_canvas.paste(p_img, (0, 0), p_img)
                    white_canvas.save(master_jpg_path, "JPEG", quality=95)
            except Exception as e:
                print(f"[WHITE_BG] Error componiendo sobre lienzo blanco puro: {e}")

    # Para hojas de giro_360 estilo Darbón, la visualización de referencia en UI usa el lienzo maestro JPG
    dest_filename = f"{character_id}.jpg" if (formato_vista == "giro_360" or not sin_fondo) else f"{character_id}.png"
    dest_file_path = personajes_dir / dest_filename

    relative_url = f"/proyectos_data/{folder.name}/personajes/{dest_filename}?t={int(time.time())}"
    char_match["imagen_url"] = relative_url
    char_match["hoja_referencia_path"] = f"proyectos/{folder.name}/personajes/{dest_filename}"
    char_match["prompt_retrato"] = final_prompt
    char_match["estado_aprobacion"] = "pendiente"
    char_match["motivo_rechazo"] = ""
    tokens = get_character_consistency_tokens(char_match, project_id=folder.name)
    char_match["cref_url"] = tokens["cref_url"]
    char_match["cref_weight"] = tokens["cref_weight"]
    char_match["cref_directive"] = tokens["cref_directive"]
    char_match["lora_model"] = tokens["lora_model"]
    char_match["lora_weight"] = tokens["lora_weight"]
    char_match["lora_trigger"] = tokens["lora_trigger"]
    char_match["lora_directive"] = tokens["lora_directive"]
    char_match["ancla_visual"] = tokens["ancla_visual"]
    char_match["seed_consistencia"] = tokens["seed_consistencia"]

    # Actualizar metadata del proyecto
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    try:
        sync_character_reference_bank(folder.name, auto_generate_missing=False)
    except Exception:
        pass

    return {
        "success": True,
        "character": char_match,
        "imagen_url": relative_url,
        "saved_path": str(dest_file_path),
        "prompt_used": final_prompt,
        "sin_fondo": sin_fondo,
        "provider": img_res.get("provider")
    }

def remove_character_background(project_id: str, character_id: str) -> Dict[str, Any]:
    """Elimina el fondo de la imagen de un personaje existente y la guarda en PNG transparente."""
    folder = get_project_folder(project_id)
    personajes_dir = folder / "personajes"
    meta_file = folder / "proyecto.json"

    src_file = None
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = personajes_dir / f"{character_id}{ext}"
        if candidate.exists():
            src_file = candidate
            break

    if not src_file:
        raise FileNotFoundError(f"No se encontró imagen física para el personaje '{character_id}'.")

    dest_png = personajes_dir / f"{character_id}.png"
    ok = remove_image_background(src_file, dest_png)
    if not ok:
        raise RuntimeError("No se pudo procesar la eliminación de fondo con rembg.")

    relative_url = f"/proyectos_data/{folder.name}/personajes/{character_id}.png?t={int(time.time())}"

    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        for c in project_data.get("personajes", []):
            if c.get("id") == character_id:
                c["imagen_url"] = relative_url
                break
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {"success": True, "imagen_url": relative_url}

def craft_environment_prompt(escenario: Dict[str, Any], project_data: Dict[str, Any]) -> str:
    """
    Genera un prompt en inglés especializado para fondos escénicos puros sin personas.
    - Traduce e integra fielmente la descripción visual en español del escenario (materiales, arquitectura, luz).
    - Ancla el ADN de técnica plástica y garantiza fondo limpio vertical 9:16 sin personas ni animales.
    """
    name = escenario.get("nombre", "Location").strip()
    tipo = escenario.get("tipo", "exterior_urbano").strip()
    desc = escenario.get("descripcion_visual", "").strip()

    dna = get_project_style_dna(project_data)
    prefix = dna["scenery_prefix"]
    art_style = dna["scenery_art_style"]

    # Traducir e integrar la descripción visual en español del escenario a inglés
    translated_env = translate_visual_description_to_english(
        name=name,
        role_or_type=tipo,
        desc_es=desc,
        category="environment"
    )

    return f"{prefix} Scenic background illustration of {name}: {translated_env}, {art_style}, empty scene, no people, no animals, vertical 9:16 background scenery, masterpiece, no 3D CGI, no photorealism"

def sync_project_style(
    project_id: str,
    new_style: Optional[str] = None,
    new_details: Optional[str] = None,
    regenerate_all: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza y propaga la técnica de dibujo seleccionada en el universo
    a todos los personajes (garantizando hoja de 4 vistas estándar Darbón)
    y escenarios clave (fondos puros sin personas con la misma técnica).
    Si regenerate_all es True, regenera las imágenes de inmediato.
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    if new_style and new_style.strip():
        project_data["estilo_visual"] = new_style.strip()
    if new_details is not None:
        project_data["estilo_detalles"] = new_details.strip()

    # 1. Sincronizar prompts de personajes con estándar de 4 vistas
    for char in project_data.get("personajes", []):
        crafted = craft_character_portrait_prompt(char, project_data, formato_vista="giro_360", sin_fondo=True)
        char["prompt_retrato"] = crafted

    # 2. Sincronizar prompts de escenarios (fondos puros sin personas con la misma técnica)
    for esc in project_data.get("escenarios", []):
        crafted_esc = craft_environment_prompt(esc, project_data)
        esc["prompt_escenario"] = crafted_esc

    # 3. Regeneración física si se solicita
    if regenerate_all:
        for char in project_data.get("personajes", []):
            try:
                generate_character_portrait(
                    project_id=project_id,
                    character_id=char["id"],
                    prompt_override=char["prompt_retrato"],
                    sin_fondo=False,
                    formato_vista="giro_360"
                )
            except Exception as ex:
                print(f"[SYNC] Error regenerando personaje {char['id']}: {ex}")

        for esc in project_data.get("escenarios", []):
            try:
                generate_environment_image(
                    project_id=project_id,
                    environment_id=esc["id"],
                    prompt_override=esc["prompt_escenario"]
                )
            except Exception as ex:
                print(f"[SYNC] Error regenerando escenario {esc['id']}: {ex}")

    project_data["actualizado_en"] = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "characters_synced": len(project_data.get("personajes", [])),
        "environments_synced": len(project_data.get("escenarios", [])),
        "personajes": project_data.get("personajes", []),
        "escenarios": project_data.get("escenarios", []),
        "estilo_visual": project_data.get("estilo_visual"),
        "estilo_detalles": project_data.get("estilo_detalles")
    }

def generate_environment_image(
    project_id: str,
    environment_id: str,
    prompt_override: Optional[str] = None
) -> Dict[str, Any]:
    """Genera la imagen de arte conceptual de un escenario recurrente del universo."""
    folder = get_project_folder(project_id)
    escenarios_dir = folder / "escenarios"
    escenarios_dir.mkdir(parents=True, exist_ok=True)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    esc_match = None
    for e in project_data.get("escenarios", []):
        if e.get("id") == environment_id or slugify(e.get("nombre", "")) == environment_id:
            esc_match = e
            break

    if not esc_match:
        raise ValueError(f"Escenario '{environment_id}' no encontrado en el proyecto.")

    if prompt_override and prompt_override.strip():
        final_prompt = prompt_override.strip()
    elif esc_match.get("prompt_escenario") and esc_match["prompt_escenario"].strip():
        final_prompt = esc_match["prompt_escenario"].strip()
    else:
        final_prompt = craft_environment_prompt(esc_match, project_data)
        esc_match["prompt_escenario"] = final_prompt

    img_res = generate_image(prompt=final_prompt, provider="flux")
    temp_file = Path(img_res["file_path"])

    dest_filename = f"{environment_id}.jpg"
    dest_path = escenarios_dir / dest_filename
    shutil.copy2(temp_file, dest_path)

    relative_url = f"/proyectos_data/{folder.name}/escenarios/{dest_filename}?t={int(time.time())}"
    esc_match["imagen_url"] = relative_url
    esc_match["prompt_escenario"] = final_prompt
    esc_match["estado_aprobacion"] = "pendiente"
    esc_match["motivo_rechazo"] = ""

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "environment": esc_match,
        "imagen_url": relative_url,
        "saved_path": str(dest_path),
        "prompt_used": final_prompt,
        "provider": img_res.get("provider")
    }

def save_environment_upload(
    project_id: str,
    environment_id: str,
    file_bytes: bytes
) -> Dict[str, Any]:
    """Guarda una imagen subida manualmente por el usuario como arte de un escenario."""
    folder = get_project_folder(project_id)
    escenarios_dir = folder / "escenarios"
    escenarios_dir.mkdir(parents=True, exist_ok=True)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    esc_match = None
    for e in project_data.get("escenarios", []):
        if e.get("id") == environment_id or slugify(e.get("nombre", "")) == environment_id:
            esc_match = e
            break

    if not esc_match:
        raise ValueError(f"Escenario '{environment_id}' no encontrado.")

    dest_filename = f"{environment_id}.jpg"
    dest_path = escenarios_dir / dest_filename
    temp_path = escenarios_dir / f"temp_{dest_filename}"

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    crop_and_resize_to_vertical(temp_path, dest_path)
    if temp_path.exists():
        temp_path.unlink()

    relative_url = f"/proyectos_data/{folder.name}/escenarios/{dest_filename}?t={int(time.time())}"
    esc_match["imagen_url"] = relative_url

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "environment": esc_match,
        "imagen_url": relative_url
    }

def delete_environment_from_project(project_id: str, environment_id: str) -> Dict[str, Any]:
    """Elimina un escenario recurrente del proyecto."""
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    escenarios = project_data.get("escenarios", [])
    project_data["escenarios"] = [e for e in escenarios if e.get("id") != environment_id]

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    for ext in [".jpg", ".png", ".jpeg"]:
        img_f = folder / "escenarios" / f"{environment_id}{ext}"
        if img_f.exists():
            try:
                img_f.unlink()
            except Exception:
                pass

    return {"success": True, "remaining": len(project_data["escenarios"])}

def save_character_portrait_upload(
    project_id: str,
    character_id: str,
    file_bytes: bytes
) -> Dict[str, Any]:
    """Guarda una foto subida manualmente por el usuario como referencia del personaje."""
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    char_match = None
    for c in project_data.get("personajes", []):
        if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id:
            char_match = c
            break

    if not char_match:
        raise ValueError(f"Personaje '{character_id}' no encontrado.")

    char_filename = f"{character_id}.jpg"
    dest_path = folder / "personajes" / char_filename
    temp_path = folder / "personajes" / f"temp_{char_filename}"

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    # Ajustar a formato vertical 9:16
    crop_and_resize_to_vertical(temp_path, dest_path)
    if temp_path.exists():
        temp_path.unlink()

    relative_url = f"/proyectos_data/{folder.name}/personajes/{char_filename}?t={int(time.time())}"
    char_match["imagen_url"] = relative_url

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "character": char_match,
        "imagen_url": relative_url
    }

def delete_character_from_project(project_id: str, character_id: str) -> Dict[str, Any]:
    """Elimina un personaje de la biblia del proyecto y su imagen de referencia."""
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    new_chars = []
    for c in project_data.get("personajes", []):
        if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id:
            img_file = folder / "personajes" / f"{character_id}.jpg"
            if img_file.exists():
                try:
                    img_file.unlink()
                except Exception:
                    pass
        else:
            new_chars.append(c)

    project_data["personajes"] = new_chars
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {"success": True, "personajes": new_chars}

def save_project_chapter(project_id: str, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
    """Guarda o actualiza un capítulo / episodio dentro de capitulos/ del proyecto."""
    folder = get_project_folder(project_id)
    title = chapter_data.get("titulo", f"Capítulo {int(time.time())}").strip()
    chapter_id = chapter_data.get("id") or slugify(title)
    
    chapter_folder = folder / "capitulos" / chapter_id
    chapter_folder.mkdir(parents=True, exist_ok=True)
    chapter_file = chapter_folder / "capitulo.json"

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    chapter_data["id"] = chapter_id
    chapter_data["titulo"] = title
    chapter_data.setdefault("scenes", [])
    chapter_data.setdefault("video_url", None)
    chapter_data.setdefault("duracion", None)
    chapter_data.setdefault("origen_tipo", "manual")
    chapter_data.setdefault("origen_ref", "")
    chapter_data.setdefault("creado_en", now)
    chapter_data["actualizado_en"] = now

    with open(chapter_file, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, ensure_ascii=False, indent=2)

    return chapter_data

def list_project_chapters(project_id: str) -> List[Dict[str, Any]]:
    """Lista todos los capítulos del proyecto ordenados lógicamente para el árbol de navegación."""
    folder = get_project_folder(project_id)
    caps_dir = folder / "capitulos"
    chapters = []
    if caps_dir.exists():
        for cap_folder in caps_dir.iterdir():
            if cap_folder.is_dir():
                cap_file = cap_folder / "capitulo.json"
                if cap_file.exists():
                    try:
                        with open(cap_file, "r", encoding="utf-8") as f:
                            c_data = json.load(f)
                            c_data.setdefault("id", cap_folder.name)
                            c_data.setdefault("titulo", cap_folder.name.replace("_", " ").title())
                            c_data.setdefault("scenes", [])
                            c_data.setdefault("video_url", None)
                            c_data.setdefault("duracion", None)
                            c_data.setdefault("origen_tipo", "manual")
                            c_data.setdefault("origen_ref", "")
                            
                            # Estado del capítulo
                            if c_data.get("video_url"):
                                c_data["status"] = "renderizado"
                            elif c_data.get("scenes") and len(c_data["scenes"]) > 0:
                                c_data["status"] = "storyboard"
                            else:
                                c_data["status"] = "borrador"
                            c_data["scenes_count"] = len(c_data["scenes"])
                            chapters.append(c_data)
                    except Exception:
                        continue

    # Ordenar por 'orden' numérico, o número en id (ej: cap_pag_5 -> 5), o título
    def get_sort_key(c):
        if c.get("orden") is not None:
            try:
                return (0, int(c["orden"]))
            except (ValueError, TypeError):
                pass
        m = re.search(r"\d+", c.get("id", ""))
        if m:
            return (1, int(m.group(0)))
        return (2, c.get("titulo", ""))

    return sorted(chapters, key=get_sort_key)

def get_project_chapter(project_id: str, chapter_id: str) -> Dict[str, Any]:
    """Obtiene el detalle completo de un capítulo por ID."""
    folder = get_project_folder(project_id)
    cap_file = folder / "capitulos" / chapter_id / "capitulo.json"
    if not cap_file.exists():
        # Búsqueda insensible a mayúsculas o slug
        for d in (folder / "capitulos").iterdir():
            if d.is_dir() and (d.name == chapter_id or slugify(d.name) == slugify(chapter_id)):
                alt_file = d / "capitulo.json"
                if alt_file.exists():
                    cap_file = alt_file
                    break
    if not cap_file.exists():
        raise FileNotFoundError(f"Capítulo '{chapter_id}' no encontrado.")
    with open(cap_file, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_project_chapter(project_id: str, chapter_id: str) -> bool:
    """Elimina permanentemente la carpeta de un capítulo del proyecto."""
    folder = get_project_folder(project_id)
    target = folder / "capitulos" / chapter_id
    if not target.exists():
        for d in (folder / "capitulos").iterdir():
            if d.is_dir() and (d.name == chapter_id or slugify(d.name) == slugify(chapter_id)):
                target = d
                break
    if target.exists() and target.is_dir():
        shutil.rmtree(target)
        return True
    return False

def batch_import_chapters_from_doc(project_id: str, source: str = "pages", max_items: int = 60) -> List[Dict[str, Any]]:
    """
    Crea automáticamente un árbol inicial de capítulos a partir del manuscrito activo:
    - source='pages': Cada página del libro se convierte en un borrador de capítulo listo para producir.
    - source='chapters': Cada capítulo/sección detectada por el parser se convierte en un capítulo.
    """
    doc = get_project_document_content(project_id)
    created = []

    if source == "pages":
        pages = doc.get("pages", [])
        for p in pages[:max_items]:
            p_num = p["page_number"]
            # Omitir páginas con casi nada de texto si hay suficientes páginas
            if p["word_count"] < 15 and len(pages) > 3:
                continue
            short_t = p.get("short_title", f"Página {p_num}")
            title = f"Pág. {p_num}: {short_t}"
            cid = f"cap_pag_{p_num:02d}"
            data = {
                "id": cid,
                "titulo": title,
                "orden": p_num,
                "origen_tipo": "pagina",
                "origen_ref": f"Página {p_num}",
                "texto_original": p["text"],
                "scenes": [],
                "video_url": None,
                "duracion": None
            }
            saved = save_project_chapter(project_id, data)
            created.append(saved)

    elif source == "chapters":
        chaps = doc.get("chapters", [])
        for idx, c in enumerate(chaps[:max_items]):
            c_idx = c.get("index", idx + 1)
            title = c.get("title", f"Capítulo {c_idx}")
            cid = f"cap_sec_{c_idx:02d}"
            data = {
                "id": cid,
                "titulo": title,
                "orden": c_idx,
                "origen_tipo": "capitulo",
                "origen_ref": f"Capítulo {c_idx}",
                "texto_original": c["text"],
                "scenes": [],
                "video_url": None,
                "duracion": None
            }
            saved = save_project_chapter(project_id, data)
            created.append(saved)

    return list_project_chapters(project_id)


def list_video_history(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista los vídeos MP4 organizados por proyecto o globalmente,
    con información detallada de la carpeta física de origen, capítulo asociado, tamaño y fecha.
    """
    videos = []

    # 1. Si se especifica un proyecto, buscar en su carpeta videos/
    if project_id:
        proj_dir = PROYECTOS_DIR / project_id
        if proj_dir.exists():
            videos_dir = proj_dir / "videos"
            cap_map = {}
            for cap in list_project_chapters(project_id):
                cid = cap.get("id")
                if cid:
                    cap_map[cid] = cap.get("titulo", cid)

            if videos_dir.exists():
                for file in sorted(videos_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
                    try:
                        stat = file.stat()
                        size_mb = round(stat.st_size / (1024 * 1024), 2)
                        created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                        thumb_file = videos_dir / f"{file.stem}_thumb.jpg"
                        cap_title = cap_map.get(file.stem, file.stem.replace("_", " ").title())

                        videos.append({
                            "filename": file.name,
                            "video_url": f"/proyectos_data/{project_id}/videos/{file.name}",
                            "thumbnail_url": f"/proyectos_data/{project_id}/videos/{thumb_file.name}" if thumb_file.exists() else None,
                            "size_mb": size_mb,
                            "created_at": created_at,
                            "project_id": project_id,
                            "chapter_title": cap_title,
                            "folder_path": f"proyectos/{project_id}/videos/{file.name}",
                            "source_type": "project"
                        })
                    except Exception:
                        continue
        return videos

    # 2. Si no se especifica proyecto, listar vídeos de todos los proyectos
    for p_dir in PROYECTOS_DIR.iterdir():
        if p_dir.is_dir():
            pid = p_dir.name
            v_dir = p_dir / "videos"
            if v_dir.exists():
                cap_map = {cap.get("id"): cap.get("titulo", cap.get("id")) for cap in list_project_chapters(pid)}
                for file in sorted(v_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
                    try:
                        stat = file.stat()
                        size_mb = round(stat.st_size / (1024 * 1024), 2)
                        created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                        thumb_file = v_dir / f"{file.stem}_thumb.jpg"
                        cap_title = cap_map.get(file.stem, file.stem.replace("_", " ").title())

                        videos.append({
                            "filename": file.name,
                            "video_url": f"/proyectos_data/{pid}/videos/{file.name}",
                            "thumbnail_url": f"/proyectos_data/{pid}/videos/{thumb_file.name}" if thumb_file.exists() else None,
                            "size_mb": size_mb,
                            "created_at": created_at,
                            "project_id": pid,
                            "chapter_title": cap_title,
                            "folder_path": f"proyectos/{pid}/videos/{file.name}",
                            "source_type": "project"
                        })
                    except Exception:
                        continue

    return videos


def delete_project_video(project_id: str, filename: str) -> Dict[str, Any]:
    """Elimina un vídeo MP4 y su miniatura de la carpeta videos/ del proyecto."""
    proj_dir = PROYECTOS_DIR / project_id
    videos_dir = proj_dir / "videos"
    target = videos_dir / filename
    if target.exists():
        target.unlink()
        thumb = videos_dir / f"{target.stem}_thumb.jpg"
        if thumb.exists():
            thumb.unlink()
        return {"success": True, "deleted": filename}

    static_target = MEDIA_DIR / filename
    if static_target.exists():
        static_target.unlink()
        return {"success": True, "deleted": filename}

    raise FileNotFoundError(f"Vídeo '{filename}' no encontrado en el proyecto.")

def update_env_settings(new_settings: Dict[str, str]) -> Dict[str, str]:
    """Actualiza de forma segura las variables de entorno en el archivo .env."""
    current_lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            current_lines = f.readlines()

    updated_keys = set()
    new_lines = []

    for line in current_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            if key in new_settings:
                new_lines.append(f"{key}={new_settings[key]}\n")
                updated_keys.add(key)
                os.environ[key] = new_settings[key]
                continue
        new_lines.append(line)

    for key, val in new_settings.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}\n")
            os.environ[key] = val

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {k: ("***" if "KEY" in k and new_settings[k] else new_settings[k]) for k in new_settings}

def get_env_settings() -> Dict[str, Any]:
    """Obtiene el estado de las claves en .env y sus valores enmascarados para la interfaz."""
    def mask_key(k: str) -> str:
        if not k:
            return ""
        if len(k) <= 10:
            return "••••••••"
        return f"{k[:7]}••••••••{k[-4:]}"

    openai_key = os.getenv("OPENAI_API_KEY", "")
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "")
    pollinations_key = os.getenv("POLLINATIONS_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    return {
        "OPENAI_API_KEY": {
            "configured": bool(openai_key and openai_key.startswith("sk-")),
            "masked": mask_key(openai_key) if openai_key else "",
            "service": "OpenAI (GPT-4o-mini)",
            "purpose": "Desglose de capítulos, coherencia de personajes y prompts visuales cinematográficos.",
            "fallback": "Plantillas heurísticas locales sin coste adicional."
        },
        "ELEVENLABS_API_KEY": {
            "configured": bool(eleven_key),
            "masked": mask_key(eleven_key) if eleven_key else "",
            "service": "ElevenLabs",
            "purpose": "Síntesis de voz neuronal hiperrealista con entonación humana y emociones.",
            "fallback": "Microsoft Edge TTS (100% gratuita, voces profesionales en español sin coste ni clave)."
        },
        "POLLINATIONS_API_KEY": {
            "configured": bool(pollinations_key),
            "masked": mask_key(pollinations_key) if pollinations_key else "",
            "service": "Pollinations AI (FLUX)",
            "purpose": "Generación de fotogramas e ilustraciones 9:16 con alta velocidad.",
            "fallback": "Servidor público gratuito de Pollinations (funciona por defecto sin clave)."
        },
        "GEMINI_API_KEY": {
            "configured": bool(gemini_key),
            "masked": mask_key(gemini_key) if gemini_key else "",
            "service": "Google Gemini",
            "purpose": "Proveedor alternativo de análisis literario de manuscritos.",
            "fallback": "OpenAI o analizador estructural regex local."
        }
    }


def sync_character_reference_bank(
    project_id: str,
    auto_generate_missing: bool = False
) -> Dict[str, Any]:
    """
    Sincroniza y cataloga el Banco de Consistencia de Personajes (--cref / LoRA) de un proyecto:
    - Verifica cada hoja de referencia física en `proyectos/{project_id}/personajes/`
    - Genera hojas de referencia faltantes si `auto_generate_missing=True`
    - Calcula y persiste los descriptores `--cref`, `--cw`, `<lora:...:weight>`, `lora_trigger`,
      `ancla_visual` y `seed_consistencia` en `proyecto.json` y en `personajes/catalogo_consistencia.json`
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Proyecto '{project_id}' no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    personajes_dir = folder / "personajes"
    personajes_dir.mkdir(parents=True, exist_ok=True)

    catalog_entries = []
    generated_now = []

    for idx, char in enumerate(project_data.get("personajes", [])):
        c_id = char.get("id") or slugify(char.get("nombre") or f"char_{idx+1}")
        char["id"] = c_id

        img_jpg = personajes_dir / f"{c_id}.jpg"
        img_png = personajes_dir / f"{c_id}.png"
        target_file = img_jpg if (img_jpg.exists() and img_jpg.stat().st_size > 2000) else (
            img_png if (img_png.exists() and img_png.stat().st_size > 2000) else None
        )

        if not target_file and auto_generate_missing:
            try:
                gen_res = generate_character_portrait(
                    project_id=folder.name,
                    character_id=c_id,
                    sin_fondo=bool(char.get("sin_fondo", True)),
                    formato_vista=char.get("formato_vista", "giro_360")
                )
                generated_now.append(c_id)
                img_jpg = personajes_dir / f"{c_id}.jpg"
                img_png = personajes_dir / f"{c_id}.png"
                target_file = img_jpg if img_jpg.exists() else (img_png if img_png.exists() else None)
            except Exception as e:
                print(f"[CHARACTER_BANK] Error generando hoja de referencia para {c_id}: {e}")

        if target_file and target_file.exists():
            mtime = int(target_file.stat().st_mtime)
            size_bytes = target_file.stat().st_size
            char["imagen_url"] = f"/proyectos_data/{folder.name}/personajes/{target_file.name}?t={mtime}"
            char["hoja_referencia_path"] = f"proyectos/{folder.name}/personajes/{target_file.name}"
        else:
            size_bytes = 0

        tokens = get_character_consistency_tokens(char, project_id=folder.name)
        char["hoja_referencia_path"] = tokens["hoja_referencia_path"]
        char["cref_url"] = tokens["cref_url"]
        char["cref_weight"] = tokens["cref_weight"]
        char["cref_directive"] = tokens["cref_directive"]
        char["lora_model"] = tokens["lora_model"]
        char["lora_weight"] = tokens["lora_weight"]
        char["lora_trigger"] = tokens["lora_trigger"]
        char["lora_directive"] = tokens["lora_directive"]
        char["ancla_visual"] = tokens["ancla_visual"]
        char["seed_consistencia"] = tokens["seed_consistencia"]

        entry = {
            "project_id": folder.name,
            "project_title": project_data.get("titulo", folder.name),
            "id": c_id,
            "nombre": char.get("nombre", c_id),
            "rol": char.get("rol", ""),
            "tipo": char.get("tipo", "humano"),
            "descripcion_visual": char.get("descripcion_visual", ""),
            "prompt_retrato": char.get("prompt_retrato", ""),
            "formato_vista": char.get("formato_vista", "giro_360"),
            "sin_fondo": char.get("sin_fondo", True),
            "imagen_url": char.get("imagen_url"),
            "clean_image_url": tokens["clean_image_url"],
            "hoja_referencia_path": tokens["hoja_referencia_path"],
            "reference_exists": bool(target_file and target_file.exists()),
            "file_size_bytes": size_bytes,
            "file_size_formatted": format_file_size(size_bytes) if size_bytes else "0 B",
            "cref_url": tokens["cref_url"],
            "cref_weight": tokens["cref_weight"],
            "cref_directive": tokens["cref_directive"],
            "lora_model": tokens["lora_model"],
            "lora_weight": tokens["lora_weight"],
            "lora_trigger": tokens["lora_trigger"],
            "lora_directive": tokens["lora_directive"],
            "ancla_visual": tokens["ancla_visual"],
            "seed_consistencia": tokens["seed_consistencia"],
            "estado_aprobacion": char.get("estado_aprobacion", "aprobado" if target_file else "pendiente")
        }
        catalog_entries.append(entry)

    # Guardar proyecto actualizado
    project_data["actualizado_en"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    # Guardar catálogo del proyecto en personajes/catalogo_consistencia.json
    catalog_payload = {
        "project_id": folder.name,
        "titulo": project_data.get("titulo", folder.name),
        "estilo_visual": project_data.get("estilo_visual", "cinematic"),
        "total_personajes": len(catalog_entries),
        "referencias_listas": sum(1 for e in catalog_entries if e["reference_exists"]),
        "generados_en_sincronizacion": generated_now,
        "actualizado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
        "personajes": catalog_entries
    }
    catalog_file = personajes_dir / "catalogo_consistencia.json"
    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(catalog_payload, f, ensure_ascii=False, indent=2)

    return catalog_payload


def get_character_reference_bank(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Devuelve el catálogo del Banco de Consistencia de Personajes (--cref / LoRA)
    para un proyecto específico o consolidado para todos los proyectos del estudio.
    """
    if project_id:
        return sync_character_reference_bank(project_id, auto_generate_missing=False)

    all_projects_catalogs = []
    all_characters = []
    for item in sorted(PROYECTOS_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if item.is_dir() and (item / "proyecto.json").exists():
            try:
                cat = sync_character_reference_bank(item.name, auto_generate_missing=False)
                all_projects_catalogs.append({
                    "project_id": cat["project_id"],
                    "titulo": cat["titulo"],
                    "estilo_visual": cat["estilo_visual"],
                    "total_personajes": cat["total_personajes"],
                    "referencias_listas": cat["referencias_listas"]
                })
                all_characters.extend(cat.get("personajes", []))
            except Exception as e:
                print(f"[CHARACTER_BANK] Error leyendo banco de {item.name}: {e}")

    global_payload = {
        "total_proyectos": len(all_projects_catalogs),
        "total_personajes": len(all_characters),
        "referencias_listas": sum(1 for c in all_characters if c.get("reference_exists")),
        "actualizado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
        "proyectos": all_projects_catalogs,
        "personajes": all_characters
    }
    global_bank_file = PROYECTOS_DIR / "banco_consistencia_global.json"
    try:
        with open(global_bank_file, "w", encoding="utf-8") as f:
            json.dump(global_payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return global_payload


def update_character_consistency_config(
    project_id: str,
    character_id: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Actualiza los parámetros técnicos de consistencia (--cref, --cw, LoRA, trigger, ancla_visual, seed)
    de un personaje y sincroniza el catálogo del proyecto.
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Proyecto '{project_id}' no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    char_match = None
    for c in project_data.get("personajes", []):
        if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id:
            char_match = c
            break

    if not char_match:
        raise ValueError(f"Personaje '{character_id}' no encontrado en el proyecto '{project_id}'.")

    for field in ("cref_url", "cref_weight", "lora_model", "lora_weight", "lora_trigger", "ancla_visual", "seed_consistencia"):
        if field in config and config[field] is not None:
            char_match[field] = config[field]

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    bank = sync_character_reference_bank(folder.name, auto_generate_missing=False)
    updated_entry = next((p for p in bank.get("personajes", []) if p.get("id") == char_match.get("id")), char_match)
    return {
        "success": True,
        "character": updated_entry,
        "bank_summary": {
            "total_personajes": bank["total_personajes"],
            "referencias_listas": bank["referencias_listas"]
        }
    }


