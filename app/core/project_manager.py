import os
import json
import time
import re
import shutil
import random
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
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
CENTRAL_ENV_KEYS_PATH = BASE_DIR.parent / "0000_Utilidades" / "04_Claves_Subcripciones_APIs" / ".env.keys"
if CENTRAL_ENV_KEYS_PATH.exists():
    load_dotenv(CENTRAL_ENV_KEYS_PATH, override=False)

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
    existing_chars_map = {
        (c.get("id") or slugify(c.get("nombre") or f"char_{i+1}")): c
        for i, c in enumerate(existing.get("personajes", []))
    }
    for idx, c in enumerate(project_data.get("personajes", existing.get("personajes", []))):
        c_id = c.get("id") or slugify(c.get("nombre") or f"char_{idx+1}")
        prev_char = existing_chars_map.get(c_id, {})
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
            "formato_vista": c.get("formato_vista") or "cuerpo_entero",
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
            "propuesta_enviada_en": c.get("propuesta_enviada_en"),
            "reglas_personaje": c.get("reglas_personaje") if c.get("reglas_personaje") is not None else prev_char.get("reglas_personaje"),
            "hoja_4_vistas_url": c.get("hoja_4_vistas_url") if c.get("hoja_4_vistas_url") is not None else prev_char.get("hoja_4_vistas_url"),
            "vistas_4": c.get("vistas_4") if c.get("vistas_4") is not None else prev_char.get("vistas_4"),
            "active_version": c.get("active_version") if c.get("active_version") is not None else prev_char.get("active_version"),
            "historial_imagenes": c.get("historial_imagenes") if c.get("historial_imagenes") is not None else prev_char.get("historial_imagenes", [])
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
    existing_envs_map = {
        (e.get("id") or slugify(e.get("nombre") or f"esc_{i+1}")): e
        for i, e in enumerate(existing.get("escenarios", []))
    }
    for idx, e in enumerate(project_data.get("escenarios", existing.get("escenarios", []))):
        e_id = e.get("id") or slugify(e.get("nombre") or f"esc_{idx+1}")
        prev_env = existing_envs_map.get(e_id, {})
        clean_environments.append({
            "id": e_id,
            "nombre": e.get("nombre", f"Escenario {idx+1}").strip(),
            "tipo": e.get("tipo", "exterior_urbano").strip(),
            "descripcion_visual": e.get("descripcion_visual", "").strip(),
            "imagen_url": e.get("imagen_url"),
            "prompt_escenario": e.get("prompt_escenario", "").strip(),
            "reglas_escenario": e.get("reglas_escenario") if e.get("reglas_escenario") is not None else prev_env.get("reglas_escenario"),
            "seed_consistencia": e.get("seed_consistencia") if e.get("seed_consistencia") is not None else prev_env.get("seed_consistencia"),
            "active_version": e.get("active_version") if e.get("active_version") is not None else prev_env.get("active_version"),
            "estado_aprobacion": e.get("estado_aprobacion", "pendiente" if e.get("imagen_url") else "pendiente"),
            "motivo_rechazo": e.get("motivo_rechazo", ""),
            "telegram_message_id": e.get("telegram_message_id"),
            "aprobado_en": e.get("aprobado_en"),
            "propuesta_enviada_en": e.get("propuesta_enviada_en"),
            "historial_imagenes": e.get("historial_imagenes") if e.get("historial_imagenes") is not None else prev_env.get("historial_imagenes", [])
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
        "reglas_generacion": project_data.get("reglas_generacion", existing.get("reglas_generacion", {
            "fondo_blanco": True,
            "hoja_4_vistas": False,
            "cuerpo_entero": True,
            "sin_texto": True,
            "escenarios_sin_personas": True,
            "formato_vertical": True,
            "nivel_detalle": 75,
            "nivel_realismo": 75
        })),
        "motor_imagenes": project_data.get("motor_imagenes", existing.get("motor_imagenes", "flux")),
        "voz_defecto": project_data.get("voz_defecto", existing.get("voz_defecto", final_narrator.get("voz_recomendada", "openai_fable"))),
        "perfil_narrador": final_narrator,
        "personajes_recurrentes_texto": project_data.get("personajes_recurrentes_texto", existing.get("personajes_recurrentes_texto", "")),
        "referencia_personaje_id": project_data.get("referencia_personaje_id", existing.get("referencia_personaje_id")),
        "referencia_escenario_id": project_data.get("referencia_escenario_id", existing.get("referencia_escenario_id")),
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
        char_style = (
            "delicate poetic watercolor and ink storybook illustration, "
            "soft artistic translucent color washes, subtle sepia pencil and ink outlines"
        )
        scen_prefix = "Delicate poetic watercolor and ink storybook illustration of"
        scen_style = (
            "delicate poetic watercolor and ink storybook scenery, "
            "soft artistic translucent color washes, subtle sepia pencil and ink outlines, "
            "warm Mediterranean sunlight, classic storybook painting"
        )
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
    tipo_en = {"humano": "human", "animal": "animal", "criatura": "creature", "objeto": "object"}.get(tipo.lower().strip(), "character")
    if not desc_es or not desc_es.strip():
        if category == "character":
            return f"{name}, authentic {tipo_en} anatomy"
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

    # Fallback automático de traducción ES->EN si OpenAI no está disponible o sin saldo
    clean_desc = clean_desc_es.strip()[:320].replace('"', '')
    try:
        import urllib.request, urllib.parse
        q = urllib.parse.quote(clean_desc)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=es&tl=en&dt=t&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp_http:
            data = json.loads(resp_http.read().decode("utf-8"))
        translated_en = "".join(seg[0] for seg in data[0] if seg and seg[0]).strip()
        if translated_en:
            result = f"{name}, {translated_en}"
            _PROMPT_TRANSLATION_CACHE[cache_key] = result
            return result
    except Exception as te:
        print(f"[PROMPT_TRANSLATE] Fallback HTTP ES->EN error: {te}")

    if category == "character":
        return f"{name}, {clean_desc}, authentic {tipo_en} anatomy"
    return f"{name}, {clean_desc}"

def _build_detail_and_realism_clauses(nivel_detalle: int = 75, nivel_realismo: int = 75, is_environment: bool = False) -> str:
    """Traduce los deslizadores (0-100) de detalle y dibujo/realismo alineados con ilustración artística."""
    try:
        d = max(0, min(100, int(nivel_detalle)))
    except Exception:
        d = 75
    try:
        r = max(0, min(100, int(nivel_realismo)))
    except Exception:
        r = 75

    if d <= 20:
        detail_clause = "minimalist simplified shapes, very low detail, clean uncluttered lines, simple flat washes"
    elif d <= 40:
        detail_clause = "simple charming storybook detail, clean uncluttered ink lines, soft minimal shading"
    elif d <= 60:
        detail_clause = "balanced medium storybook detail, clear expressive features, gentle watercolor washes"
    elif d <= 80:
        detail_clause = "delicate storybook detail, fine sepia ink linework and soft artistic translucent washes"
    else:
        detail_clause = "intricate fine ink linework, rich delicate storybook detail and layered translucent washes"

    if r <= 20:
        realism_clause = "stylized 2D cartoon character design, exaggerated playful proportions, expressive animated look"
    elif r <= 40:
        realism_clause = "semi-stylized animated storybook character, gentle charming stylized proportions"
    elif r <= 60:
        realism_clause = "classic hand-drawn storybook illustration proportions, gentle stylized poetic character design"
    elif r <= 80:
        realism_clause = "gentle stylized classic storybook illustration proportions, expressive hand-drawn picture-book character design, soft simplified features"
    else:
        realism_clause = "refined classic picture-book illustration proportions, expressive hand-drawn storybook style"

    combined = f"{detail_clause}, {realism_clause}"
    if is_environment:
        combined = combined.replace("character design", "scenery design").replace("storybook character", "storybook scenery")
    return combined


def craft_character_portrait_prompt(
    character: Dict[str, Any],
    project_data: Dict[str, Any],
    formato_vista: str = "cuerpo_entero",
    sin_fondo: bool = True,
    force_refresh: bool = False,
    reglas_override: Optional[Dict[str, Any]] = None,
    style_prompt_override: Optional[str] = None
) -> str:
    """
    Genera un prompt de concepto de personaje en inglés optimizado con la descripción traducida,
    las reglas específicas de ese personaje (4 vistas, cuerpo entero, fondo blanco, sin texto, vertical)
    y al final el prompt de definición del estilo del proyecto.
    """
    name = character.get("nombre", "Character").strip()
    role = character.get("rol", "").strip()
    desc = character.get("descripcion_visual", "").strip()
    tipo = character.get("tipo", "humano").lower().strip()

    # Resolver reglas efectivas: override explícito -> reglas_personaje -> reglas_generacion del proyecto -> defaults
    proj_rules = project_data.get("reglas_generacion") or {}
    char_rules = character.get("reglas_personaje") or {}
    effective_rules = {**proj_rules, **char_rules, **(reglas_override or {})}

    use_4_views = (formato_vista == "giro_360")
    use_full_body = bool(effective_rules.get("cuerpo_entero", formato_vista != "retrato"))
    use_white_bg = bool(effective_rules.get("fondo_blanco", sin_fondo))
    use_no_text = bool(effective_rules.get("sin_texto", True))
    use_vertical = bool(effective_rules.get("formato_vertical", True))
    nivel_detalle = effective_rules.get("nivel_detalle", 75)
    nivel_realismo = effective_rules.get("nivel_realismo", 75)

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

    # 2. Guardas anatómicas breves y precisas según especie y Cuerpo Entero
    if is_bird:
        guard = "full body perched head to claws, no humans" if use_full_body else "avian bird, no humans"
    elif tipo == "animal" or any(w in f"{lower_name} {lower_desc}" for w in ["burro", "donkey", "perro", "dog", "galgo", "gato", "caballo", "animal"]):
        guard = "standing on all four legs, full body visible head to tail and hooves, no humans, no clothing" if use_full_body else "quadruped animal, no humans"
    else:
        is_child = any(w in f"{lower_name} {lower_desc} {lower_trans}" for w in ["niño", "niña", "child", "boy", "girl", "joven", "young", "adolescente", "teen", "10", "11", "12", "13", "14", "15"])
        human_anatomy = "child/adolescent human" if is_child else "single human"
        guard = f"{human_anatomy}, full body standing head to toe, shoes visible, no other characters" if use_full_body else f"{human_anatomy}, no other characters"

    subject = f"{translated_subject}, {guard}"

    # 3. Cláusula de vistas / encuadre optimizada para FLUX y estilo pictórico al inicio y al final
    dna = get_project_style_dna(project_data)
    art_clause = (style_prompt_override or "").strip() or dna["character_art_style"]
    if use_white_bg:
        for paper_term in [
            "rich textured paper grain", "textured paper grain", "textured paper",
            "visible cold-press paper texture", "paper texture",
            "warm Mediterranean sunlight", "warm sunlight"
        ]:
            art_clause = art_clause.replace(paper_term, "").strip(", ")
        art_clause = ", ".join([p.strip() for p in art_clause.split(",") if p.strip()])

    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    style_lead = "delicate poetic watercolor and ink" if style_key == "watercolor" else "illustrated"

    if use_4_views:
        prefix = (
            f"A square 1:1 2x2 grid {style_lead} character turnaround reference sheet with 4 distinct full-body views of {subject}"
            if use_full_body
            else f"A square 1:1 2x2 grid {style_lead} character turnaround sheet with 4 distinct views of {subject}"
        )
        views_clause = (
            "4 separate square panels arranged in a clean 2x2 grid: "
            "top-left panel direct symmetrical front view looking straight ahead at the camera, "
            "top-right panel direct rear view seen from behind showing back and tail, "
            "bottom-left panel strict 90-degree side profile view, "
            "bottom-right panel 45-degree three-quarter front-side angle view, "
            "same exact character design and proportions in all 4 panels"
        )
    elif use_full_body:
        prefix = f"Three-quarter angle (45-degree front-side view) {style_lead} character illustration of {subject}"
        views_clause = "single character shown in a natural three-quarter front-side pose (body and head angled 45 degrees to the side, non-symmetrical diagonal stance, not facing straight at the camera), full body standing head to toe, wide safety margins, no cropped feet"
    else:
        prefix = f"Three-quarter angle (45-degree front-side view) {style_lead} character portrait of {subject}"
        views_clause = "single character shown in a natural three-quarter front-side pose (shoulders and head angled 45 degrees to the side, not facing straight at the camera), upper body bust portrait, centered framing"

    # 4. Cláusula de fondo, texto, orientación y sliders de detalle/realismo
    bg_parts = []
    if use_white_bg:
        bg_parts.append("centered composition with wide safety margins, completely isolated on solid plain pure white background (#FFFFFF), stark white empty background, solid pure white canvas, no paper texture, no parchment texture, no yellow tint, no shadows, zero scenery")
    else:
        bg_parts.append("centered composition, clean minimal neutral background")

    if use_no_text:
        bg_parts.append("no text, no words, no labels, no arrows")
    if use_vertical:
        bg_parts.append("vertical 9:16 portrait composition")
    else:
        bg_parts.append("square 1:1 composition")

    sliders_clause = _build_detail_and_realism_clauses(nivel_detalle, nivel_realismo)
    bg_clause = ", ".join(bg_parts)
    neg_clause = ", no 3D CGI, no photorealism" if style_key in ("watercolor", "storybook_kids", "ghibli_anime", "anime", "comic") else ""

    return f"{prefix}, {views_clause}, {sliders_clause}, {bg_clause}, {art_clause}, masterpiece{neg_clause}"

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

def recommend_narrator_with_ai(
    project_id: str,
    profile_override: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Si se recibe `profile_override` (especificación actual del panel superior), propone la voz más
    adecuada en función de ese perfil sin sobrescribirlo.
    Si no, analiza el proyecto y su manuscrito para deducir perfil y voz.
    """
    proj = get_project(project_id)

    if profile_override:
        genero = (profile_override.get("genero") or "masculino").strip().lower()
        rango = (profile_override.get("rango_edad") or "adulto").strip().lower()
        tono = (profile_override.get("tono") or "").strip().lower()
        justif = (profile_override.get("justificacion") or "").strip().lower()
        edad = (profile_override.get("edad_aprox") or "").strip().lower()
        context_text = f"{tono} {justif} {edad}"

        if genero == "femenino":
            if rango in ("infantil", "joven") or any(k in context_text for k in ("joven", "adolesc", "dinám", "juvenil")):
                voz = "edge_ximena"
                motivo = "Voz femenina juvenil y expresiva en español nativo acorde al rango de edad y tono indicados."
            else:
                voz = "edge_elvira"
                motivo = "Voz femenina cálida y literaria en español peninsular acorde al perfil indicado."
        elif genero == "neutro":
            voz = "edge_alvaro"
            motivo = "Voz castellana neutra y equilibrada acorde al género especificado."
        else:
            if rango in ("infantil", "joven") or any(k in context_text for k in ("12-14", "muchacho", "joven", "adolesc", "infantil")):
                voz = "edge_alvaro_joven"
                motivo = "Voz juvenil masculina (12-14 años) en español peninsular nativo acorde al perfil indicado."
            elif any(k in context_text for k in ("eleven", "clásic", "profund", "solemne", "maduro")) or rango == "maduro":
                voz = "eleven_ZtGDHPi9jPEEuRGCBOY5"
                motivo = "Voz narrativa clásica en español (ElevenLabs) acorde a un timbre maduro y literario."
            else:
                voz = "edge_alvaro"
                motivo = "Voz masculina castellana estándar y documental acorde al perfil indicado."

        merged_profile = {
            "nombre": profile_override.get("nombre") or proj.get("perfil_narrador", {}).get("nombre", "Narrador Principal"),
            "genero": genero,
            "edad_aprox": profile_override.get("edad_aprox") or proj.get("perfil_narrador", {}).get("edad_aprox", ""),
            "rango_edad": rango,
            "tono": profile_override.get("tono") or proj.get("perfil_narrador", {}).get("tono", ""),
            "justificacion": profile_override.get("justificacion") or proj.get("perfil_narrador", {}).get("justificacion", ""),
            "voz_recomendada": voz,
            "motivo_propuesta": motivo
        }
        return merged_profile

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
                "tono": "Lírico, contemplativo, tierno, pausado y reflexivo en español nativo",
                "justificacion": "En Platero y yo el narrador es una voz lírica joven (el autor recordando su adolescencia en Moguer) en diálogo íntimo y confidente con su burrillo Platero. Requiere una voz juvenil masculina en español peninsular nativo (12-14 años), tierna y pausada, sin acento foráneo ni pesadez adulta.",
                "voz_recomendada": "edge_alvaro_joven",
                "texto_muestra": "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos. Sólo los espejos de azabache de sus ojos son duros cual dos escarabajos de cristal negro."
            }
        else:
            narrator = {
                "nombre": "Narrador Principal",
                "genero": "masculino",
                "edad_aprox": "Adulto (30-40 años)",
                "rango_edad": "adulto",
                "tono": "Cálido, envolvente y literario en español peninsular",
                "justificacion": "Narrador omnisciente estándar en español castellano neutro para relatos narrativos.",
                "voz_recomendada": "edge_alvaro",
                "texto_muestra": "Había una vez un lugar donde las historias cobraban vida."
            }
    return narrator

def _rescue_existing_asset_if_needed(
    folder: Path,
    category: str,
    item_id: str,
    item_dict: Dict[str, Any],
    active_jpg_path: Path,
    active_png_path: Optional[Path] = None
) -> None:
    """Archiva la imagen previa existente como v000 antes de sobrescribirla por primera vez."""
    historial = item_dict.setdefault("historial_imagenes", [])
    if historial or not active_jpg_path.exists():
        return

    history_dir = folder / category / "historial" / item_id
    history_dir.mkdir(parents=True, exist_ok=True)
    mtime_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(active_jpg_path.stat().st_mtime))
    hist_jpg = f"v000_previa_{mtime_str}.jpg"
    shutil.copy2(active_jpg_path, history_dir / hist_jpg)

    hist_png = None
    if active_png_path and active_png_path.exists():
        hist_png = f"v000_previa_{mtime_str}.png"
        shutil.copy2(active_png_path, history_dir / hist_png)

    historial.append({
        "version": 0,
        "filename": hist_jpg,
        "png_filename": hist_png,
        "url": f"/proyectos_data/{folder.name}/{category}/historial/{item_id}/{hist_jpg}",
        "provider": "previa",
        "prompt": "",
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(active_jpg_path.stat().st_mtime))
    })


def _assert_asset_not_approved(item_dict: Dict[str, Any], label: str = "personaje") -> None:
    """Impide regenerar, subir o cambiar la imagen si el elemento está aprobado."""
    if (item_dict.get("estado_aprobacion") or "").strip().lower() == "aprobado":
        raise ValueError(f"Este {label} está aprobado y bloqueado. Cámbialo a 'Pendiente' antes de regenerar o cambiar su imagen.")


def _assert_character_not_approved(char_match: Dict[str, Any]) -> None:
    """Impide regenerar, subir o cambiar la imagen si el personaje está aprobado."""
    _assert_asset_not_approved(char_match, "personaje")


def _record_new_asset_version(
    folder: Path,
    category: str,
    item_id: str,
    item_dict: Dict[str, Any],
    active_jpg_path: Path,
    provider: str,
    prompt: str = "",
    active_png_path: Optional[Path] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Guarda una copia versionada en historial/{item_id}/ tras generar o subir una imagen."""
    historial = item_dict.setdefault("historial_imagenes", [])
    history_dir = folder / category / "historial" / item_id
    history_dir.mkdir(parents=True, exist_ok=True)

    next_ver = max((h.get("version", 0) for h in historial), default=0) + 1
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_prov = slugify(provider or "ia")
    hist_jpg = f"v{next_ver:03d}_{ts}_{safe_prov}.jpg"
    shutil.copy2(active_jpg_path, history_dir / hist_jpg)

    hist_png = None
    if active_png_path and active_png_path.exists():
        hist_png = f"v{next_ver:03d}_{ts}_{safe_prov}.png"
        shutil.copy2(active_png_path, history_dir / hist_png)

    entry = {
        "version": next_ver,
        "filename": hist_jpg,
        "png_filename": hist_png,
        "url": f"/proyectos_data/{folder.name}/{category}/historial/{item_id}/{hist_jpg}",
        "provider": provider or "basic",
        "prompt": (prompt or ""),
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    if seed is not None:
        entry["seed"] = int(seed)
    historial.append(entry)
    item_dict["active_version"] = next_ver
    return entry


def restore_asset_version(
    project_id: str,
    category: str,
    item_id: str,
    version: int
) -> Dict[str, Any]:
    """Restaura una versión previa del historial como imagen activa del personaje o escenario."""
    if category not in ("personajes", "escenarios"):
        raise ValueError("Categoría inválida; debe ser 'personajes' o 'escenarios'.")

    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    items = project_data.get(category, [])
    item_match = next(
        (it for it in items if it.get("id") == item_id or slugify(it.get("nombre", "")) == item_id),
        None
    )
    if not item_match:
        raise ValueError(f"Elemento '{item_id}' no encontrado en {category}.")

    _assert_asset_not_approved(item_match, "personaje" if category == "personajes" else "escenario")

    historial = item_match.get("historial_imagenes", [])
    entry = next((h for h in historial if int(h.get("version", -1)) == int(version)), None)
    if not entry:
        raise ValueError(f"Versión {version} no encontrada en el historial de '{item_id}'.")

    history_dir = folder / category / "historial" / item_id
    src_jpg = history_dir / entry["filename"]
    if not src_jpg.exists():
        raise FileNotFoundError(f"Archivo de historial no encontrado: {src_jpg}")

    active_jpg = folder / category / f"{item_id}.jpg"
    active_jpg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_jpg, active_jpg)

    dest_filename = f"{item_id}.jpg"
    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    if entry.get("png_filename") and style_key != "watercolor":
        src_png = history_dir / entry["png_filename"]
        if src_png.exists():
            active_png = folder / category / f"{item_id}.png"
            shutil.copy2(src_png, active_png)
            if category == "personajes" and item_match.get("formato_vista") != "giro_360" and item_match.get("sin_fondo", True):
                dest_filename = f"{item_id}.png"

    relative_url = f"/proyectos_data/{folder.name}/{category}/{dest_filename}?t={int(time.time())}"
    item_match["imagen_url"] = relative_url
    item_match["active_version"] = int(version)
    if category == "personajes":
        item_match["hoja_referencia_path"] = f"proyectos/{folder.name}/{category}/{dest_filename}"
    if entry.get("seed") is not None:
        item_match["seed_consistencia"] = int(entry["seed"])

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    if category == "personajes":
        try:
            sync_character_reference_bank(folder.name, auto_generate_missing=False)
        except Exception:
            pass

    return {
        "success": True,
        "imagen_url": relative_url,
        "version": version,
        "active_version": int(version),
        "provider": entry.get("provider"),
        "prompt": entry.get("prompt", ""),
        "historial_imagenes": historial
    }


def _resolve_character_portrait_context(
    project_id: str,
    character_id: str,
    prompt_override: Optional[str] = None,
    sin_fondo: bool = True,
    formato_vista: str = "cuerpo_entero",
    descripcion_visual: Optional[str] = None
):
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    char_match = next(
        (c for c in project_data.get("personajes", []) if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id),
        None
    )
    if not char_match:
        raise ValueError(f"Personaje '{character_id}' no encontrado en el proyecto.")

    _assert_character_not_approved(char_match)

    if descripcion_visual and descripcion_visual.strip():
        char_match["descripcion_visual"] = descripcion_visual.strip()

    char_match["sin_fondo"] = sin_fondo
    char_match["formato_vista"] = formato_vista

    if prompt_override and prompt_override.strip():
        final_prompt = prompt_override.strip()
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

    char_rules = char_match.get("reglas_personaje") or {}
    proj_rules = project_data.get("reglas_generacion") or {}
    use_vertical = bool(char_rules.get("formato_vertical", proj_rules.get("formato_vertical", True)))
    fit_mode = "crop" if use_vertical else ("contain" if sin_fondo else "square")
    return folder, meta_file, project_data, char_match, final_prompt, use_vertical, fit_mode


def _apply_character_portrait_image(
    folder: Path,
    meta_file: Path,
    project_data: Dict[str, Any],
    char_match: Dict[str, Any],
    character_id: str,
    temp_file: Path,
    final_prompt: str,
    sin_fondo: bool,
    formato_vista: str,
    use_vertical: bool,
    provider_name: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    personajes_dir = folder / "personajes"
    personajes_dir.mkdir(parents=True, exist_ok=True)

    master_jpg_path = personajes_dir / f"{character_id}.jpg"
    png_path = personajes_dir / f"{character_id}.png"

    _rescue_existing_asset_if_needed(folder, "personajes", character_id, char_match, master_jpg_path, png_path)
    shutil.copy2(temp_file, master_jpg_path)

    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    apply_rembg = sin_fondo and style_key != "watercolor"
    if apply_rembg:
        rem_ok = remove_image_background(temp_file, png_path)
        if rem_ok and png_path.exists():
            try:
                from PIL import Image
                with Image.open(png_path) as p_img:
                    white_canvas = Image.new("RGB", p_img.size, (255, 255, 255))
                    white_canvas.paste(p_img, (0, 0), p_img)
                    white_canvas.save(master_jpg_path, "JPEG", quality=95)
            except Exception as e:
                print(f"[WHITE_BG] Error componiendo sobre lienzo blanco puro: {e}")

    _record_new_asset_version(
        folder, "personajes", character_id, char_match,
        master_jpg_path, provider=provider_name,
        prompt=final_prompt, active_png_path=png_path if apply_rembg else None,
        seed=seed
    )

    dest_filename = f"{character_id}.jpg" if (use_vertical or formato_vista == "giro_360" or not apply_rembg) else f"{character_id}.png"
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
    char_match["seed_consistencia"] = int(seed) if seed is not None else tokens["seed_consistencia"]

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
        "provider": provider_name,
        "seed_consistencia": char_match["seed_consistencia"],
        "historial_imagenes": char_match.get("historial_imagenes", []),
        "active_version": char_match.get("active_version")
    }


def generate_character_portrait(
    project_id: str,
    character_id: str,
    prompt_override: Optional[str] = None,
    sin_fondo: bool = True,
    formato_vista: str = "cuerpo_entero",
    descripcion_visual: Optional[str] = None,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera el retrato o concepto completo de un personaje del proyecto.
    """
    folder, meta_file, project_data, char_match, final_prompt, use_vertical, fit_mode = _resolve_character_portrait_context(
        project_id, character_id, prompt_override, sin_fondo, formato_vista, descripcion_visual
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    img_res = generate_image(prompt=final_prompt, provider=selected_provider, fit_mode=fit_mode)
    return _apply_character_portrait_image(
        folder=folder,
        meta_file=meta_file,
        project_data=project_data,
        char_match=char_match,
        character_id=character_id,
        temp_file=Path(img_res["file_path"]),
        final_prompt=final_prompt,
        sin_fondo=sin_fondo,
        formato_vista=formato_vista,
        use_vertical=use_vertical,
        provider_name=img_res.get("provider", selected_provider),
        seed=img_res.get("seed")
    )


def generate_character_portrait_proposals(
    project_id: str,
    character_id: str,
    prompt_override: Optional[str] = None,
    sin_fondo: bool = True,
    formato_vista: str = "cuerpo_entero",
    descripcion_visual: Optional[str] = None,
    provider: Optional[str] = None,
    count: int = 6
) -> Dict[str, Any]:
    """Genera varias propuestas (por defecto 6) en paralelo con distintas semillas para que el usuario elija una."""
    folder, meta_file, project_data, char_match, final_prompt, use_vertical, fit_mode = _resolve_character_portrait_context(
        project_id, character_id, prompt_override, sin_fondo, formato_vista, descripcion_visual
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    total = max(2, min(8, int(count or 6)))
    seeds = [random.randint(100000, 999999) for _ in range(total)]

    def _run_one(idx: int, seed_val: int) -> Dict[str, Any]:
        res = generate_image(prompt=final_prompt, provider=selected_provider, seed=seed_val, fit_mode=fit_mode)
        return {
            "index": idx,
            "url": res["url"],
            "file_path": res["file_path"],
            "seed": res.get("seed") or seed_val,
            "provider": res.get("provider", selected_provider)
        }

    proposals: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=total) as pool:
        futures = {pool.submit(_run_one, i, s): i for i, s in enumerate(seeds)}
        for fut in as_completed(futures):
            try:
                proposals.append(fut.result())
            except Exception as e:
                print(f"[PROPOSALS] Error generando propuesta {futures[fut]}: {e}")

    proposals.sort(key=lambda x: x["index"])
    if not proposals:
        raise RuntimeError("No se pudo generar ninguna propuesta de imagen.")

    return {
        "success": True,
        "character_id": character_id,
        "character_name": char_match.get("nombre", character_id),
        "prompt_used": final_prompt,
        "proposals": proposals
    }


def select_character_portrait_proposal(
    project_id: str,
    character_id: str,
    file_path: str,
    seed: Optional[int] = None,
    provider: Optional[str] = None,
    prompt_used: Optional[str] = None,
    sin_fondo: bool = True,
    formato_vista: str = "cuerpo_entero"
) -> Dict[str, Any]:
    """Fija una de las propuestas elegidas como retrato activo del personaje y registra su semilla."""
    src_path = Path(file_path)
    if not src_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de la propuesta seleccionada: {file_path}")

    folder, meta_file, project_data, char_match, final_prompt, use_vertical, _ = _resolve_character_portrait_context(
        project_id, character_id, prompt_used, sin_fondo, formato_vista, None
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    return _apply_character_portrait_image(
        folder=folder,
        meta_file=meta_file,
        project_data=project_data,
        char_match=char_match,
        character_id=character_id,
        temp_file=src_path,
        final_prompt=final_prompt,
        sin_fondo=sin_fondo,
        formato_vista=formato_vista,
        use_vertical=use_vertical,
        provider_name=selected_provider,
        seed=seed
    )

def generate_character_4_views(
    project_id: str,
    character_id: str,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Paso 2: A partir de la vista frontal aprobada del personaje, genera las otras 3 vistas
    consistentes (trasera, perfil lateral 90° y perfil 3/4 45°) usando FLUX Kontext con
    la imagen frontal como referencia, y compone una hoja 2x2 de 1024x1024.
    """
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
        raise ValueError(f"Personaje '{character_id}' no encontrado en el proyecto.")

    personajes_dir = folder / "personajes"
    front_path = personajes_dir / f"{character_id}.jpg"
    if not front_path.exists():
        alt_png = personajes_dir / f"{character_id}.png"
        if alt_png.exists():
            front_path = alt_png
        else:
            raise FileNotFoundError("Primero debes generar la vista frontal del personaje antes de crear las 4 vistas.")

    selected_provider = (provider or project_data.get("motor_imagenes") or "fal_flux_dev").strip().lower()
    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    style_hint = "delicate poetic watercolor and ink storybook illustration style, soft artistic translucent color washes, subtle sepia pencil and ink outlines, no 3D CGI, no photorealism" if style_key == "watercolor" else f"{style_key} illustration style matching the reference"
    char_rules = char_match.get("reglas_personaje") or {}
    proj_rules = project_data.get("reglas_generacion") or {}
    use_vertical = bool(char_rules.get("formato_vertical", proj_rules.get("formato_vertical", True)))
    fit_mode = "crop" if use_vertical else "square"

    # La imagen inicial es la vista tres cuartos (3/4). Generamos 4 vistas nuevas (Detalle facial + Frontal + Trasera + Perfil):
    view_specs = [
        (
            "detalle",
            f"Close-up front-facing portrait of the face and head only of this exact same character from the reference image, looking straight ahead at the camera, showing fine facial features, eyes and expression clearly, keeping the exact same design, colors, and {style_hint}, isolated on pure solid white background (#FFFFFF), no text, no labels"
        ),
        (
            "frontal",
            f"Direct symmetrical front view looking straight ahead at the camera of this exact same character from the reference image, keeping the exact same design, proportions, colors, and {style_hint}, full body standing head to toe, isolated on pure solid white background (#FFFFFF), no text, no labels"
        ),
        (
            "trasera",
            f"Full-body back view of this exact same character from the reference image seen from the back, facing away toward the background, showing the back of the head, back and tail, keeping the exact same design, proportions, colors, and {style_hint}, full body standing head to toe, isolated on pure solid white background (#FFFFFF), no text, no labels"
        ),
        (
            "perfil",
            f"Direct 90-degree side profile view facing right of this exact same character from the reference image, keeping the exact same design, proportions, colors, and {style_hint}, full body standing head to toe, isolated on pure solid white background (#FFFFFF), no text, no labels"
        ),
    ]

    from PIL import Image, ImageDraw, ImageStat
    ts = int(time.time())
    vistas_4: Dict[str, str] = {}
    generated_paths: List[Path] = []
    for view_name, view_prompt in view_specs:
        src_p = None
        for attempt in range(3):
            prompt_try = view_prompt if attempt == 0 else (
                f"Storybook back-facing character sheet view of this exact same character facing away, showing the back and silhouette clearly, {style_hint}, full body standing head to toe, isolated on pure solid white background (#FFFFFF), no text, no labels"
                if view_name == "trasera" else view_prompt
            )
            res = generate_image(
                prompt=prompt_try,
                provider=selected_provider,
                fit_mode=fit_mode,
                reference_image=str(front_path)
            )
            cand_p = Path(res["file_path"])
            with Image.open(cand_p) as chk_im:
                if max(ImageStat.Stat(chk_im.convert("RGB")).mean) >= 5.0:
                    src_p = cand_p
                    break
        if src_p is None:
            src_p = cand_p
        view_filename = f"{character_id}_v_{view_name}.jpg"
        view_dest = personajes_dir / view_filename
        shutil.copy2(src_p, view_dest)
        generated_paths.append(view_dest)
        vistas_4[view_name] = f"/proyectos_data/{folder.name}/personajes/{view_filename}?t={ts}"

    canvas = Image.new("RGB", (1024, 1024), (255, 255, 255))
    positions = [(0, 0), (512, 0), (0, 512), (512, 512)]

    for idx, img_path in enumerate(generated_paths):
        with Image.open(img_path) as raw_img:
            if raw_img.mode in ("RGBA", "LA") or (raw_img.mode == "P" and "transparency" in raw_img.info):
                rgba = raw_img.convert("RGBA")
                tile_bg = Image.new("RGB", rgba.size, (255, 255, 255))
                tile_bg.paste(rgba, (0, 0), rgba)
                rgb_img = tile_bg
            else:
                rgb_img = raw_img.convert("RGB")
            rgb_img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (512, 512), (255, 255, 255))
            offset_x = (512 - rgb_img.width) // 2
            offset_y = (512 - rgb_img.height) // 2
            tile.paste(rgb_img, (offset_x, offset_y))
            canvas.paste(tile, positions[idx])

    draw = ImageDraw.Draw(canvas)
    draw.line([(512, 0), (512, 1024)], fill=(232, 232, 232), width=2)
    draw.line([(0, 512), (1024, 512)], fill=(232, 232, 232), width=2)

    sheet_filename = f"{character_id}_4vistas.jpg"
    sheet_path = personajes_dir / sheet_filename
    canvas.save(sheet_path, "JPEG", quality=95)

    relative_4v_url = f"/proyectos_data/{folder.name}/personajes/{sheet_filename}?t={ts}"
    char_match["hoja_4_vistas_url"] = relative_4v_url
    char_match["vistas_4"] = vistas_4

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "character": char_match,
        "vistas_4": vistas_4,
        "hoja_4_vistas_url": relative_4v_url,
        "saved_path": str(sheet_path),
        "provider": selected_provider
    }


def audit_character_prompts_coherence(
    project_id: str,
    reference_char_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Audita localmente (sin consumir API de visión ni tocar imágenes) que los prompts de todos
    los personajes cuadren con:
    1. El estilo visual del proyecto (ej. acuarela poética y tinta sepia, no 3D CGI, no photorealism).
    2. Sus opciones particulares (fondo blanco, sin texto, vertical 9:16, cuerpo entero, sliders).
    3. La coherencia estilística con el Personaje de Referencia Principal marcado en azul.
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    chars = project_data.get("personajes", [])
    if not chars:
        return {
            "success": True,
            "style": project_data.get("estilo_visual", "watercolor"),
            "reference_char_id": None,
            "reference_char_name": None,
            "total": 0,
            "approved": 0,
            "healed": 0,
            "rejected": 0,
            "results": []
        }

    ref_id = reference_char_id or project_data.get("referencia_personaje_id") or chars[0].get("id")
    ref_char = next((c for c in chars if c.get("id") == ref_id or slugify(c.get("nombre", "")) == ref_id), chars[0])
    ref_id = ref_char.get("id")
    ref_name = ref_char.get("nombre") or ref_id
    ref_prompt = (ref_char.get("prompt_retrato") or "").lower()

    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    style_det = (project_data.get("estilo_detalles") or "").strip().lower()
    proj_rules = project_data.get("reglas_generacion") or {}

    spanish_markers = [" de ", " con ", " y ", " el ", " la ", " los ", " las ", " ojos ", " viste ", " cabello ", " pelaje "]

    results = []
    approved_count = 0
    rejected_count = 0

    for c in chars:
        cid = c.get("id")
        cname = c.get("nombre") or cid
        prompt = (c.get("prompt_retrato") or "").strip()
        p_low = prompt.lower()
        char_rules = c.get("reglas_personaje") or {}
        eff_rules = {**proj_rules, **char_rules}

        issues: List[str] = []
        if not prompt:
            issues.append("No tiene prompt generado todavía.")
        else:
            if "2x2 grid" in p_low or "turnaround model sheet" in p_low or "four distinct" in p_low:
                issues.append("Usa formato antiguo de cuadrícula 2x2 en lugar de vista 3/4.")
            if any(m in f" {p_low} " for m in spanish_markers):
                issues.append("Contiene texto en español sin traducir al inglés.")

            # Comprobación de estilo del proyecto
            if style_key == "watercolor":
                if "watercolor" not in p_low:
                    issues.append("Falta el estilo de acuarela (`watercolor`).")
                if "delicate poetic watercolor" not in p_low and "delicate poetic watercolor" in ref_prompt:
                    issues.append(f"La técnica no coincide con la acuarela poética del personaje de referencia ({ref_name}).")
                if "no 3d cgi" not in p_low or "no photorealism" not in p_low:
                    issues.append("Faltan los negativos anti-3D y anti-fotorrealismo (`no 3D CGI, no photorealism`).")
            elif style_key and style_key.replace("_", " ") not in p_low and style_key not in p_low:
                if "ghibli" in style_key and "ghibli" not in p_low:
                    issues.append("Falta referencia al estilo Ghibli.")
                elif "pixar" in style_key and "pixar" not in p_low:
                    issues.append("Falta referencia al estilo Pixar 3D.")

            if style_det and len(style_det) > 3 and style_det not in p_low:
                issues.append(f"Falta el detalle personalizado del estilo (`{style_det}`).")

            # Comprobación de opciones particulares
            if eff_rules.get("fondo_blanco", c.get("sin_fondo", True)) and "#ffffff" not in p_low and "white background" not in p_low:
                issues.append("Falta fondo blanco puro (`#FFFFFF`).")
            if eff_rules.get("sin_texto", True) and "no text" not in p_low:
                issues.append("Falta regla `no text`.")
            if eff_rules.get("formato_vertical", True) and "9:16" not in p_low and "vertical" not in p_low:
                issues.append("Falta formato vertical `9:16`.")
            if eff_rules.get("cuerpo_entero", c.get("formato_vista") != "retrato") and "full body" not in p_low:
                issues.append("Falta `full body` (cuerpo entero).")

            # Coherencia directa con el prompt del personaje principal de referencia (marcado en azul)
            if cid != ref_id and ref_prompt:
                ref_checks = [
                    ("delicate poetic watercolor", "No usa el mismo estilo de acuarela poética del personaje principal"),
                    ("subtle sepia pencil", "Faltan los contornos sutiles de lápiz/tinta sepia del personaje principal"),
                    ("no paper texture", "Falta `no paper texture` presente en el personaje principal"),
                    ("vertical 9:16", "No coincide con el formato vertical 9:16 del personaje principal"),
                    ("three-quarter", f"Ángulo distinto al del personaje principal ({ref_name}, 3/4)"),
                    ("no 3d cgi", "Falta `no 3D CGI` presente en el personaje principal"),
                    ("no photorealism", "Falta `no photorealism` presente en el personaje principal"),
                ]
                for token, msg in ref_checks:
                    if token in ref_prompt and token not in p_low:
                        if msg not in issues:
                            issues.append(f"{msg} ({ref_name}).")

        is_ok = len(issues) == 0
        if is_ok:
            approved_count += 1
        else:
            rejected_count += 1
            # Quitar el aprobado y pasar a "en_revision" para que el usuario aplique los cambios
            c["estado_aprobacion"] = "en_revision"
            c["motivo_rechazo"] = " | ".join(issues)

        is_ref = (cid == ref_id)
        results.append({
            "id": cid,
            "nombre": f"{cname} ★ (Referencia)" if is_ref else cname,
            "is_reference": is_ref,
            "status": "APPROVED" if is_ok else "REJECTED",
            "estado_aprobacion": c.get("estado_aprobacion", "pendiente"),
            "imagen_url": c.get("imagen_url"),
            "detected_style": f"{style_key} · Detalle {eff_rules.get('nivel_detalle', 75)}% · Realismo {eff_rules.get('nivel_realismo', 75)}%",
            "reason": "Coherente con el estilo del libro, sus opciones y el prompt del personaje principal." if is_ok else "Cambios necesarios: " + " | ".join(issues)
        })

    if rejected_count > 0:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "style": style_key,
        "reference_char_id": ref_id,
        "reference_char_name": ref_name,
        "total": len(chars),
        "approved": approved_count,
        "healed": 0,
        "rejected": rejected_count,
        "results": results
    }


def sync_incoherent_character_prompts(
    project_id: str,
    reference_char_id: Optional[str] = None
) -> Dict[str, Any]:
    """Actualiza solo los prompts desalineados (sin tocar imágenes) y vuelve a auditar."""
    audit = audit_character_prompts_coherence(project_id, reference_char_id=reference_char_id)
    bad_ids = {r["id"] for r in audit["results"] if r["status"] != "APPROVED"}
    if not bad_ids:
        return {"success": True, "updated_count": 0, "audit": audit}

    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    updated = 0
    for c in project_data.get("personajes", []):
        if c.get("id") in bad_ids:
            c["prompt_retrato"] = craft_character_portrait_prompt(
                character=c,
                project_data=project_data,
                formato_vista=c.get("formato_vista", "cuerpo_entero"),
                sin_fondo=c.get("sin_fondo", True),
                force_refresh=True
            )
            updated += 1

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    new_audit = audit_character_prompts_coherence(project_id, reference_char_id=reference_char_id)
    return {"success": True, "updated_count": updated, "audit": new_audit}

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

def craft_environment_prompt(
    escenario: Dict[str, Any],
    project_data: Dict[str, Any],
    force_refresh: bool = False,
    reglas_override: Optional[Dict[str, Any]] = None,
    style_prompt_override: Optional[str] = None
) -> str:
    """
    Genera un prompt en inglés especializado para fondos escénicos combinando:
    1. Estilo visual global del proyecto (y detalle personalizado o style_prompt_override).
    2. Descripción visual en español del escenario traducida al inglés.
    3. Opciones particulares del escenario (sin personas, sin texto, formato vertical 9:16, nivel de detalle y realismo).
    """
    name = escenario.get("nombre", "Location").strip()
    tipo = escenario.get("tipo", "exterior_urbano").strip()
    desc = escenario.get("descripcion_visual", "").strip()

    dna = get_project_style_dna(project_data)
    prefix = dna["scenery_prefix"]
    art_style = dna["scenery_art_style"]

    proj_rules = project_data.get("reglas_generacion") or {}
    env_rules = reglas_override if reglas_override is not None else (escenario.get("reglas_escenario") or {})
    effective_rules = {**proj_rules, **env_rules}

    no_people = bool(effective_rules.get("escenarios_sin_personas", effective_rules.get("sin_personas", True)))
    no_text = bool(effective_rules.get("sin_texto", True))
    vertical_916 = bool(effective_rules.get("formato_vertical", True))
    nivel_detalle = effective_rules.get("nivel_detalle", 75)
    nivel_realismo = effective_rules.get("nivel_realismo", 75)

    # Traducir e integrar la descripción visual en español del escenario a inglés
    translated_env = translate_visual_description_to_english(
        name=name,
        role_or_type=tipo,
        desc_es=desc,
        category="environment"
    )
    if translated_env.lower().startswith(f"{name.lower()},"):
        translated_env = translated_env[len(name) + 1:].strip()

    sliders_clause = _build_detail_and_realism_clauses(nivel_detalle, nivel_realismo, is_environment=True)
    rule_clauses: List[str] = []
    if no_people:
        rule_clauses.append("empty scene, no people, no characters, no animals")
    if no_text:
        rule_clauses.append("no text, no words, no labels, no watermarks")
    if vertical_916:
        rule_clauses.append("vertical 9:16 portrait background scenery")
    if sliders_clause:
        rule_clauses.append(sliders_clause)

    style_block = style_prompt_override.strip() if (style_prompt_override and style_prompt_override.strip()) else f"{prefix} {art_style}".strip()
    rules_str = ", ".join(rule_clauses)
    return f"{style_block}, Scenic background illustration of {name}: {translated_env}, {rules_str}, masterpiece, no 3D CGI, no photorealism"


def audit_environment_prompts_coherence(
    project_id: str,
    reference_env_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Audita localmente (sin consumir API de visión ni tocar imágenes) que los prompts de todos
    los escenarios cuadren con:
    1. El estilo visual del proyecto (ej. acuarela poética y tinta sepia, no 3D CGI, no photorealism).
    2. Sus opciones particulares (sin personas, sin texto, vertical 9:16, sliders).
    3. La coherencia estilística con el Escenario de Referencia Principal marcado en azul.
    """
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    envs = project_data.get("escenarios", [])
    if not envs:
        return {
            "success": True,
            "style": project_data.get("estilo_visual", "watercolor"),
            "reference_env_id": None,
            "reference_env_name": None,
            "total": 0,
            "approved": 0,
            "healed": 0,
            "rejected": 0,
            "results": []
        }

    ref_id = reference_env_id or project_data.get("referencia_escenario_id") or envs[0].get("id")
    ref_env = next((e for e in envs if e.get("id") == ref_id or slugify(e.get("nombre", "")) == ref_id), envs[0])
    ref_id = ref_env.get("id")
    ref_name = ref_env.get("nombre") or ref_id
    ref_prompt = (ref_env.get("prompt_escenario") or "").lower()

    style_key = (project_data.get("estilo_visual") or "watercolor").strip().lower()
    style_det = (project_data.get("estilo_detalles") or "").strip().lower()
    proj_rules = project_data.get("reglas_generacion") or {}

    spanish_markers = [" de ", " con ", " y ", " el ", " la ", " los ", " las ", " calles ", " casas ", " cielo "]

    results = []
    approved_count = 0
    rejected_count = 0
    state_changed = False

    for e in envs:
        eid = e.get("id")
        ename = e.get("nombre") or eid
        prompt = (e.get("prompt_escenario") or "").strip()
        p_low = prompt.lower()
        p_no_name = p_low.replace(ename.lower(), " ")
        env_rules = e.get("reglas_escenario") or {}
        eff_rules = {**proj_rules, **env_rules}

        issues: List[str] = []
        if not prompt:
            issues.append("No tiene prompt generado todavía.")
        else:
            if any(m in f" {p_no_name} " for m in spanish_markers):
                issues.append("Contiene texto en español sin traducir al inglés.")

            if style_key == "watercolor":
                if "watercolor" not in p_low:
                    issues.append("Falta el estilo de acuarela (`watercolor`).")
                if "delicate poetic watercolor" not in p_low and "delicate poetic watercolor" in ref_prompt:
                    issues.append(f"La técnica no coincide con la acuarela poética del escenario de referencia ({ref_name}).")
                if "no 3d cgi" not in p_low or "no photorealism" not in p_low:
                    issues.append("Faltan los negativos anti-3D y anti-fotorrealismo (`no 3D CGI, no photorealism`).")
            elif style_key and style_key.replace("_", " ") not in p_low and style_key not in p_low:
                if "ghibli" in style_key and "ghibli" not in p_low:
                    issues.append("Falta referencia al estilo Ghibli.")
                elif "pixar" in style_key and "pixar" not in p_low:
                    issues.append("Falta referencia al estilo Pixar 3D.")

            if style_det and len(style_det) > 3 and style_det not in p_low:
                issues.append(f"Falta el detalle personalizado del estilo (`{style_det}`).")

            if eff_rules.get("escenarios_sin_personas", eff_rules.get("sin_personas", True)) and "no people" not in p_low:
                issues.append("Falta regla `no people` (escenario sin personas).")
            if eff_rules.get("sin_texto", True) and "no text" not in p_low:
                issues.append("Falta regla `no text`.")
            if eff_rules.get("formato_vertical", True) and "9:16" not in p_low and "vertical" not in p_low:
                issues.append("Falta formato vertical `9:16`.")

            if eid != ref_id and ref_prompt:
                ref_checks = [
                    ("delicate poetic watercolor", "No usa el mismo estilo de acuarela poética del escenario principal"),
                    ("vertical 9:16", "No coincide con el formato vertical 9:16 del escenario principal"),
                    ("no 3d cgi", "Falta `no 3D CGI` presente en el escenario principal"),
                    ("no photorealism", "Falta `no photorealism` presente en el escenario principal"),
                ]
                for token, msg in ref_checks:
                    if token in ref_prompt and token not in p_low and msg not in issues:
                        issues.append(f"{msg} ({ref_name}).")

        is_ok = len(issues) == 0
        if is_ok:
            approved_count += 1
            if e.get("estado_aprobacion") == "en_revision":
                e["estado_aprobacion"] = "aprobado" if e.get("imagen_url") else "pendiente"
                e["motivo_rechazo"] = ""
                state_changed = True
        else:
            rejected_count += 1
            e["estado_aprobacion"] = "en_revision"
            e["motivo_rechazo"] = " | ".join(issues)
            state_changed = True

        is_ref = (eid == ref_id)
        results.append({
            "id": eid,
            "nombre": f"{ename} ★ (Referencia)" if is_ref else ename,
            "is_reference": is_ref,
            "status": "APPROVED" if is_ok else "REJECTED",
            "estado_aprobacion": e.get("estado_aprobacion", "pendiente"),
            "imagen_url": e.get("imagen_url"),
            "detected_style": f"{style_key} · Detalle {eff_rules.get('nivel_detalle', 75)}% · Realismo {eff_rules.get('nivel_realismo', 75)}%",
            "reason": "Coherente con el estilo del libro, sus opciones y el prompt del escenario principal." if is_ok else "Cambios necesarios: " + " | ".join(issues)
        })

    if state_changed:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "style": style_key,
        "reference_env_id": ref_id,
        "reference_env_name": ref_name,
        "total": len(envs),
        "approved": approved_count,
        "healed": 0,
        "rejected": rejected_count,
        "results": results
    }


def sync_incoherent_environment_prompts(
    project_id: str,
    reference_env_id: Optional[str] = None
) -> Dict[str, Any]:
    """Actualiza solo los prompts de escenarios desalineados (sin tocar imágenes) y vuelve a auditar."""
    audit = audit_environment_prompts_coherence(project_id, reference_env_id=reference_env_id)
    bad_ids = {r["id"] for r in audit["results"] if r["status"] != "APPROVED"}
    if not bad_ids:
        return {"success": True, "updated_count": 0, "audit": audit}

    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    updated = 0
    for e in project_data.get("escenarios", []):
        if e.get("id") in bad_ids:
            e["prompt_escenario"] = craft_environment_prompt(
                escenario=e,
                project_data=project_data,
                force_refresh=True
            )
            updated += 1

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    new_audit = audit_environment_prompts_coherence(project_id, reference_env_id=reference_env_id)
    return {"success": True, "updated_count": updated, "audit": new_audit}

def sync_project_style(
    project_id: str,
    new_style: Optional[str] = None,
    new_details: Optional[str] = None,
    regenerate_all: bool = False,
    sync_characters: bool = True,
    sync_environments: bool = True
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

    # 1. Sincronizar prompts de personajes según las reglas de generación del proyecto
    reglas = project_data.get("reglas_generacion") or {}
    sin_fondo_rule = bool(reglas.get("fondo_blanco", True))
    if reglas.get("hoja_4_vistas", False):
        formato_rule = "giro_360"
    elif reglas.get("cuerpo_entero", True):
        formato_rule = "cuerpo_entero"
    else:
        formato_rule = "retrato"

    chars_synced = 0
    if sync_characters:
        for char in project_data.get("personajes", []):
            crafted = craft_character_portrait_prompt(char, project_data, formato_vista=formato_rule, sin_fondo=sin_fondo_rule)
            char["prompt_retrato"] = crafted
            chars_synced += 1

    # 2. Sincronizar prompts de escenarios (fondos puros sin personas con la misma técnica)
    envs_synced = 0
    if sync_environments:
        for esc in project_data.get("escenarios", []):
            crafted_esc = craft_environment_prompt(esc, project_data)
            esc["prompt_escenario"] = crafted_esc
            envs_synced += 1

    # 3. Regeneración física si se solicita
    if regenerate_all:
        for char in project_data.get("personajes", []):
            try:
                generate_character_portrait(
                    project_id=project_id,
                    character_id=char["id"],
                    prompt_override=char["prompt_retrato"],
                    sin_fondo=sin_fondo_rule,
                    formato_vista=char.get("formato_vista") or formato_rule
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
        "characters_synced": chars_synced,
        "environments_synced": envs_synced,
        "personajes": project_data.get("personajes", []),
        "escenarios": project_data.get("escenarios", []),
        "estilo_visual": project_data.get("estilo_visual"),
        "estilo_detalles": project_data.get("estilo_detalles")
    }

def _resolve_environment_context(
    project_id: str,
    environment_id: str,
    prompt_override: Optional[str] = None
):
    folder = get_project_folder(project_id)
    escenarios_dir = folder / "escenarios"
    escenarios_dir.mkdir(parents=True, exist_ok=True)
    meta_file = folder / "proyecto.json"
    if not meta_file.exists():
        raise FileNotFoundError("Proyecto no encontrado.")

    with open(meta_file, "r", encoding="utf-8") as f:
        project_data = json.load(f)

    esc_match = next(
        (e for e in project_data.get("escenarios", []) if e.get("id") == environment_id or slugify(e.get("nombre", "")) == environment_id),
        None
    )
    if not esc_match:
        raise ValueError(f"Escenario '{environment_id}' no encontrado en el proyecto.")

    _assert_asset_not_approved(esc_match, "escenario")

    if prompt_override and prompt_override.strip():
        final_prompt = prompt_override.strip()
    elif esc_match.get("prompt_escenario") and esc_match["prompt_escenario"].strip():
        final_prompt = esc_match["prompt_escenario"].strip()
    else:
        final_prompt = craft_environment_prompt(esc_match, project_data)
        esc_match["prompt_escenario"] = final_prompt

    return folder, escenarios_dir, meta_file, project_data, esc_match, final_prompt


def _apply_environment_image(
    folder: Path,
    escenarios_dir: Path,
    meta_file: Path,
    project_data: Dict[str, Any],
    esc_match: Dict[str, Any],
    environment_id: str,
    temp_file: Path,
    final_prompt: str,
    provider_name: str,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    dest_filename = f"{environment_id}.jpg"
    dest_path = escenarios_dir / dest_filename
    _rescue_existing_asset_if_needed(folder, "escenarios", environment_id, esc_match, dest_path)
    shutil.copy2(temp_file, dest_path)
    _record_new_asset_version(
        folder, "escenarios", environment_id, esc_match,
        dest_path, provider=provider_name, prompt=final_prompt, seed=seed
    )

    relative_url = f"/proyectos_data/{folder.name}/escenarios/{dest_filename}?t={int(time.time())}"
    esc_match["imagen_url"] = relative_url
    esc_match["prompt_escenario"] = final_prompt
    esc_match["estado_aprobacion"] = "pendiente"
    esc_match["motivo_rechazo"] = ""
    if seed is not None:
        esc_match["seed_consistencia"] = int(seed)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "environment": esc_match,
        "imagen_url": relative_url,
        "saved_path": str(dest_path),
        "prompt_used": final_prompt,
        "provider": provider_name,
        "seed_consistencia": esc_match.get("seed_consistencia"),
        "historial_imagenes": esc_match.get("historial_imagenes", []),
        "active_version": esc_match.get("active_version")
    }


def generate_environment_image(
    project_id: str,
    environment_id: str,
    prompt_override: Optional[str] = None,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """Genera la imagen de arte conceptual de un escenario recurrente del universo."""
    folder, escenarios_dir, meta_file, project_data, esc_match, final_prompt = _resolve_environment_context(
        project_id, environment_id, prompt_override
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    img_res = generate_image(prompt=final_prompt, provider=selected_provider)
    return _apply_environment_image(
        folder=folder,
        escenarios_dir=escenarios_dir,
        meta_file=meta_file,
        project_data=project_data,
        esc_match=esc_match,
        environment_id=environment_id,
        temp_file=Path(img_res["file_path"]),
        final_prompt=final_prompt,
        provider_name=img_res.get("provider", selected_provider),
        seed=img_res.get("seed")
    )


def generate_environment_proposals(
    project_id: str,
    environment_id: str,
    prompt_override: Optional[str] = None,
    provider: Optional[str] = None,
    count: int = 6
) -> Dict[str, Any]:
    """Genera 6 propuestas en paralelo para un escenario con distintas semillas."""
    folder, escenarios_dir, meta_file, project_data, esc_match, final_prompt = _resolve_environment_context(
        project_id, environment_id, prompt_override
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    total = max(2, min(8, int(count or 6)))
    seeds = [random.randint(100000, 999999) for _ in range(total)]

    def _run_one(idx: int, seed_val: int) -> Dict[str, Any]:
        res = generate_image(prompt=final_prompt, provider=selected_provider, seed=seed_val)
        return {
            "index": idx,
            "url": res["url"],
            "file_path": res["file_path"],
            "seed": res.get("seed") or seed_val,
            "provider": res.get("provider", selected_provider)
        }

    proposals: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=total) as pool:
        futures = {pool.submit(_run_one, i, s): i for i, s in enumerate(seeds)}
        for fut in as_completed(futures):
            try:
                proposals.append(fut.result())
            except Exception as e:
                print(f"[ENV_PROPOSALS] Error generando propuesta {futures[fut]}: {e}")

    proposals.sort(key=lambda x: x["index"])
    if not proposals:
        raise RuntimeError("No se pudo generar ninguna propuesta de escenario.")

    return {
        "success": True,
        "environment_id": environment_id,
        "environment_name": esc_match.get("nombre", environment_id),
        "prompt_used": final_prompt,
        "proposals": proposals
    }


def select_environment_proposal(
    project_id: str,
    environment_id: str,
    file_path: str,
    seed: Optional[int] = None,
    provider: Optional[str] = None,
    prompt_used: Optional[str] = None
) -> Dict[str, Any]:
    """Fija una de las propuestas elegidas como arte activo del escenario y guarda su semilla."""
    src_path = Path(file_path)
    if not src_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de la propuesta seleccionada: {file_path}")

    folder, escenarios_dir, meta_file, project_data, esc_match, final_prompt = _resolve_environment_context(
        project_id, environment_id, prompt_used
    )
    selected_provider = (provider or project_data.get("motor_imagenes") or "flux").strip().lower()
    return _apply_environment_image(
        folder=folder,
        escenarios_dir=escenarios_dir,
        meta_file=meta_file,
        project_data=project_data,
        esc_match=esc_match,
        environment_id=environment_id,
        temp_file=src_path,
        final_prompt=final_prompt,
        provider_name=selected_provider,
        seed=seed
    )

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

    _assert_asset_not_approved(esc_match, "escenario")

    dest_filename = f"{environment_id}.jpg"
    dest_path = escenarios_dir / dest_filename
    temp_path = escenarios_dir / f"temp_{dest_filename}"

    _rescue_existing_asset_if_needed(folder, "escenarios", environment_id, esc_match, dest_path)

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    crop_and_resize_to_vertical(temp_path, dest_path)
    if temp_path.exists():
        temp_path.unlink()

    _record_new_asset_version(folder, "escenarios", environment_id, esc_match, dest_path, provider="upload")

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

    _assert_character_not_approved(char_match)

    char_filename = f"{character_id}.jpg"
    dest_path = folder / "personajes" / char_filename
    temp_path = folder / "personajes" / f"temp_{char_filename}"

    _rescue_existing_asset_if_needed(folder, "personajes", character_id, char_match, dest_path)

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    # Ajustar a formato vertical 9:16
    crop_and_resize_to_vertical(temp_path, dest_path)
    if temp_path.exists():
        temp_path.unlink()

    _record_new_asset_version(folder, "personajes", character_id, char_match, dest_path, provider="upload")

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
    chapter_id = (chapter_data.get("id") or chapter_data.get("chapter_id") or slugify(title)).strip()
    
    chapter_folder = folder / "capitulos" / chapter_id
    chapter_folder.mkdir(parents=True, exist_ok=True)
    chapter_file = chapter_folder / "capitulo.json"

    existing: Dict[str, Any] = {}
    if chapter_file.exists():
        try:
            with open(chapter_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    merged = dict(existing)
    for k, v in chapter_data.items():
        if k == "chapter_id":
            continue
        if v is not None or k not in merged:
            merged[k] = v

    merged["id"] = chapter_id
    merged["titulo"] = title
    merged.setdefault("scenes", [])
    merged.setdefault("video_url", None)
    merged.setdefault("duracion", None)
    merged.setdefault("origen_tipo", "manual")
    merged.setdefault("origen_ref", "")
    merged.setdefault("creado_en", now)
    merged["actualizado_en"] = now

    with open(chapter_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return merged

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

def _upsert_env_file(env_path: Path, new_settings: Dict[str, str]) -> None:
    """Actualiza o añade pares clave=valor en un archivo .env preservando comentarios y el resto de líneas."""
    current_lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
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
                continue
        new_lines.append(line)

    for key, val in new_settings.items():
        if key not in updated_keys:
            if new_lines and not new_lines[-1].endswith("\n"):
                new_lines.append("\n")
            new_lines.append(f"{key}={val}\n")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def update_env_settings(new_settings: Dict[str, str], sync_central: bool = True) -> Dict[str, str]:
    """Actualiza las variables en .env local y opcionalmente en el repositorio central de utilidades."""
    if not new_settings:
        return {}

    _upsert_env_file(ENV_PATH, new_settings)
    if sync_central and CENTRAL_ENV_KEYS_PATH.parent.exists():
        _upsert_env_file(CENTRAL_ENV_KEYS_PATH, new_settings)

    for key, val in new_settings.items():
        os.environ[key] = val

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
    fal_key = os.getenv("FAL_KEY", "")

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
        },
        "FAL_KEY": {
            "configured": bool(fal_key),
            "masked": mask_key(fal_key) if fal_key else "",
            "service": "Fal.ai (FLUX.1 Dev / Kontext)",
            "purpose": "Motor gráfico dedicado FLUX para personajes, escenarios y consistencia visual.",
            "fallback": "Motor Básico (OpenAI / Pollinations gratuito)."
        }
    }


def get_providers_billing_status() -> Dict[str, Any]:
    """Consulta en paralelo el estado de cuenta, cuota o saldo disponible de cada proveedor configurado."""
    import concurrent.futures
    import shutil
    import requests as _req

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    pollinations_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    fal_key = os.getenv("FAL_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    def _check_openai() -> Dict[str, Any]:
        base = {
            "home_url": "https://platform.openai.com",
            "billing_url": "https://platform.openai.com/settings/organization/billing/overview",
            "keys_url": "https://platform.openai.com/api-keys",
        }
        if not openai_key or not openai_key.startswith("sk-"):
            return {**base, "status": "unconfigured", "label": "Sin clave configurada (activo respaldo LLM gratuito)"}
        try:
            r = _req.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "ok"}], "max_tokens": 1},
                timeout=5,
            )
            if r.status_code == 200:
                return {**base, "status": "ok", "label": "Cuenta activa con crédito disponible"}
            if r.status_code == 401:
                return {**base, "status": "error", "label": "Clave inválida o revocada (401)"}
            if r.status_code == 429:
                return {**base, "status": "error", "label": "Saldo agotado en OpenAI (activo respaldo LLM gratuito 0€)"}
            return {**base, "status": "warning", "label": f"HTTP {r.status_code}"}
        except Exception as e:
            return {**base, "status": "warning", "label": f"Sin respuesta: {str(e)[:45]}"}

    def _check_elevenlabs() -> Dict[str, Any]:
        base = {
            "home_url": "https://elevenlabs.io",
            "billing_url": "https://elevenlabs.io/app/subscription",
            "keys_url": "https://elevenlabs.io/app/developers/api-keys",
        }
        if not eleven_key:
            return {**base, "status": "unconfigured", "label": "Opcional (usando Edge TTS gratuito)", "remaining_chars": 0, "limit_chars": 0}
        try:
            r = _req.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": eleven_key},
                timeout=4,
            )
            if r.status_code == 200:
                d = r.json()
                used = int(d.get("character_count", 0))
                limit = int(d.get("character_limit", 0))
                rem = max(0, limit - used)
                tier = d.get("tier", "free")
                pct_rem = round((rem / limit) * 100) if limit > 0 else 0
                st = "error" if rem <= 0 else ("warning" if pct_rem < 15 else "ok")
                return {
                    **base,
                    "status": st,
                    "remaining_chars": rem,
                    "limit_chars": limit,
                    "tier": tier,
                    "label": f"Plan {tier}: {rem:,} / {limit:,} caracteres restantes ({pct_rem}%)",
                }
            if r.status_code == 401:
                return {**base, "status": "error", "label": "Clave inválida (401)", "remaining_chars": 0, "limit_chars": 0}
            return {**base, "status": "warning", "label": f"HTTP {r.status_code}", "remaining_chars": 0, "limit_chars": 0}
        except Exception as e:
            return {**base, "status": "warning", "label": f"Sin respuesta: {str(e)[:45]}", "remaining_chars": 0, "limit_chars": 0}

    def _check_fal() -> Dict[str, Any]:
        base = {
            "home_url": "https://fal.ai",
            "billing_url": "https://fal.ai/dashboard/billing",
            "keys_url": "https://fal.ai/dashboard/keys",
        }
        if not fal_key:
            return {**base, "status": "unconfigured", "label": "Sin clave configurada"}
        try:
            # Comprueba estado real de autenticación y saldo en fal.run (que verifica crédito inmediatamente)
            r = _req.post(
                "https://fal.run/fal-ai/any-llm",
                headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"},
                json={},
                timeout=5,
            )
            txt = r.text[:240]
            if r.status_code == 403 and ("Exhausted balance" in txt or "locked" in txt.lower()):
                return {**base, "status": "error", "label": "Saldo agotado (recargar en Billing)"}
            if r.status_code == 401:
                return {**base, "status": "error", "label": "Clave inválida o no autorizada (401)"}
            if r.status_code in (200, 400, 422):
                return {**base, "status": "ok", "label": "Cuenta activa con saldo disponible (ver USD en Billing)"}
            return {**base, "status": "warning", "label": f"Estado HTTP {r.status_code}"}
        except Exception as e:
            return {**base, "status": "warning", "label": f"Sin respuesta: {str(e)[:45]}"}

    def _check_pollinations() -> Dict[str, Any]:
        base = {
            "home_url": "https://pollinations.ai",
            "billing_url": "https://enter.pollinations.ai",
            "keys_url": "https://enter.pollinations.ai",
        }
        if not pollinations_key:
            return {**base, "status": "free", "label": "Modo público gratuito activo (sin clave)"}
        return {**base, "status": "ok", "label": "Clave prioritaria configurada"}

    def _check_gemini() -> Dict[str, Any]:
        base = {
            "home_url": "https://aistudio.google.com",
            "billing_url": "https://console.cloud.google.com/billing",
            "keys_url": "https://aistudio.google.com/apikey",
        }
        if not gemini_key:
            return {**base, "status": "unconfigured", "label": "Opcional (sin clave configurada)"}
        try:
            r = _req.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}",
                timeout=4,
            )
            if r.status_code == 200:
                return {**base, "status": "ok", "label": "Clave válida y operativa"}
            if r.status_code in (400, 401, 403):
                return {**base, "status": "error", "label": f"Clave inválida o sin permisos ({r.status_code})"}
            if r.status_code == 429:
                return {**base, "status": "warning", "label": "Cuota agotada temporalmente (429)"}
            return {**base, "status": "warning", "label": f"HTTP {r.status_code}"}
        except Exception as e:
            return {**base, "status": "warning", "label": f"Sin respuesta: {str(e)[:45]}"}

    checks = {
        "OPENAI_API_KEY": _check_openai,
        "ELEVENLABS_API_KEY": _check_elevenlabs,
        "FAL_KEY": _check_fal,
        "POLLINATIONS_API_KEY": _check_pollinations,
        "GEMINI_API_KEY": _check_gemini,
    }
    results: Dict[str, Any] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(fn): key for key, fn in checks.items()}
        for fut in concurrent.futures.as_completed(futs):
            k = futs[fut]
            try:
                results[k] = fut.result()
            except Exception as e:
                results[k] = {"status": "warning", "label": str(e)[:50]}

    results["EDGE_TTS"] = {
        "status": "free",
        "label": "Gratuita e ilimitada (sin API key)",
        "home_url": "https://speech.microsoft.com/portal/voicegallery",
    }
    results["FFMPEG"] = {
        "status": "ok" if shutil.which("ffmpeg") else "error",
        "label": "Instalado localmente (0€)" if shutil.which("ffmpeg") else "No encontrado en PATH",
        "home_url": "https://ffmpeg.org",
    }
    return results


def evaluate_chapter_feasibility(
    text: str = "",
    voice: str = "edge_alvaro",
    image_engine: str = "flux",
    i2v_model: str = "kling_v21_pro",
    enable_i2v: bool = True,
    scenes_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Evalúa antes de empezar un capítulo si las herramientas y créditos actuales permiten
    completarlo con la calidad deseada, calculando recursos necesarios y coste estimado.
    """
    clean_t = (text or "").strip()
    words = len(clean_t.split()) if clean_t else 130
    chars = len(clean_t) if clean_t else 780
    is_estimate = not bool(clean_t)

    est_audio_sec = round(max(12.0, words / 2.35), 1)
    optimal_scenes = int(scenes_count) if (scenes_count and int(scenes_count) > 0) else max(2, min(8, round(words / 26)))
    clip_sec_per_scene = 10
    total_i2v_sec = optimal_scenes * clip_sec_per_scene if enable_i2v else 0

    i2v_rates = {
        "kling_v21_pro": ("Kling 2.1 Pro (Máxima calidad)", 0.098),
        "kling_v25_pro": ("Kling 2.5 Turbo Pro (Fluido / -29% coste)", 0.070),
        "hailuo_02_pro": ("MiniMax Hailuo 02 Pro", 0.080),
        "kling_v21": ("Kling 2.1 Standard (Económico)", 0.050),
        "kling_v16": ("Kling 1.6 Standard", 0.045),
    }
    i2v_label, i2v_rate = i2v_rates.get(i2v_model, i2v_rates["kling_v21_pro"])

    img_unit_cost = 0.04 if image_engine == "flux" else 0.0
    img_cost_usd = round(optimal_scenes * img_unit_cost, 2)
    vid_cost_usd = round(total_i2v_sec * i2v_rate, 2) if enable_i2v else 0.0
    total_cost_usd = round(img_cost_usd + vid_cost_usd, 2)

    billing = get_providers_billing_status()
    openai_st = billing.get("OPENAI_API_KEY", {})
    fal_st = billing.get("FAL_KEY", {})
    eleven_st = billing.get("ELEVENLABS_API_KEY", {})
    ffmpeg_st = billing.get("FFMPEG", {})

    stages: List[Dict[str, Any]] = []
    blockers: List[str] = []

    # 1. Guion y Prompts en 5 capas
    if openai_st.get("status") == "ok":
        llm_detail = "OpenAI GPT-4o-mini activo con crédito"
    elif fal_st.get("status") == "ok":
        llm_detail = "Respaldo Fal.ai Any-LLM activo (< $0.002)"
    else:
        llm_detail = "Respaldo LLM gratuito Pollinations (0€) activo porque OpenAI/Fal no tienen saldo"
    stages.append({
        "phase": "1. Guion y Prompts (5 capas)",
        "tool": "Cascada LLM Inteligente",
        "status": "ok",
        "needed": f"{words} palabras → {optimal_scenes} escenas (~{round(est_audio_sec / optimal_scenes)}s/escena)",
        "available": llm_detail,
        "cost_usd": 0.0,
        "billing_url": openai_st.get("billing_url"),
    })

    # 2. Locución del Narrador
    uses_eleven = (voice or "").lower().startswith("eleven")
    if uses_eleven:
        rem_c = int(eleven_st.get("remaining_chars") or 0)
        if eleven_st.get("status") == "ok" and rem_c >= chars:
            stages.append({
                "phase": "2. Locución del Narrador",
                "tool": "ElevenLabs",
                "status": "ok",
                "needed": f"~{chars:,} caracteres",
                "available": f"{rem_c:,} caracteres disponibles",
                "cost_usd": 0.0,
                "billing_url": eleven_st.get("billing_url"),
            })
        else:
            blockers.append(f"ElevenLabs requiere ~{chars:,} caracteres y tienes {rem_c:,} (o puedes cambiar a voz Edge TTS gratuita).")
            stages.append({
                "phase": "2. Locución del Narrador",
                "tool": "ElevenLabs",
                "status": "error",
                "needed": f"~{chars:,} caracteres",
                "available": eleven_st.get("label", "Cuota insuficiente"),
                "cost_usd": 0.0,
                "billing_url": eleven_st.get("billing_url"),
            })
    else:
        stages.append({
            "phase": "2. Locución del Narrador",
            "tool": "Microsoft Edge TTS",
            "status": "ok",
            "needed": f"~{chars:,} caracteres (~{est_audio_sec}s)",
            "available": "Ilimitado y 100% gratuito (0€)",
            "cost_usd": 0.0,
            "billing_url": None,
        })

    # 3. Imágenes de Escena (Personajes + Fondo)
    if image_engine == "flux":
        if fal_st.get("status") == "ok":
            stages.append({
                "phase": "3. Fotos 9:16 (Personaje + Fondo)",
                "tool": "Fal.ai FLUX Kontext Multi",
                "status": "ok",
                "needed": f"{optimal_scenes} imágenes ($0.04/ud)",
                "available": "Cuenta Fal.ai con saldo activo",
                "cost_usd": img_cost_usd,
                "billing_url": fal_st.get("billing_url"),
            })
        else:
            blockers.append(f"Fal.ai tiene el saldo agotado para generar las {optimal_scenes} imágenes con FLUX Kontext Multi (${img_cost_usd:.2f} USD).")
            stages.append({
                "phase": "3. Fotos 9:16 (Personaje + Fondo)",
                "tool": "Fal.ai FLUX Kontext Multi",
                "status": "error",
                "needed": f"{optimal_scenes} imágenes (${img_cost_usd:.2f} USD)",
                "available": fal_st.get("label", "Saldo agotado en Fal.ai"),
                "cost_usd": img_cost_usd,
                "billing_url": fal_st.get("billing_url"),
            })
    else:
        stages.append({
            "phase": "3. Fotos 9:16 (Motor Básico)",
            "tool": "Pollinations FLUX Público",
            "status": "ok",
            "needed": f"{optimal_scenes} imágenes",
            "available": "Servidor público gratuito (0€)",
            "cost_usd": 0.0,
            "billing_url": None,
        })

    # 4. Animación de Vídeo I2V
    if enable_i2v:
        if fal_st.get("status") == "ok":
            stages.append({
                "phase": "4. Animación de Vídeo (I2V)",
                "tool": f"Fal.ai · {i2v_label}",
                "status": "ok",
                "needed": f"{optimal_scenes} clips × 10s = {total_i2v_sec}s (${vid_cost_usd:.2f} USD)",
                "available": f"Cuenta activa (verifica tener ≥ ${total_cost_usd:.2f} USD en Billing)",
                "cost_usd": vid_cost_usd,
                "billing_url": fal_st.get("billing_url"),
            })
        else:
            blockers.append(f"Fal.ai no tiene saldo para animar {total_i2v_sec}s de vídeo con {i2v_label} (requiere recargar ≥ ${total_cost_usd:.2f} USD en Billing).")
            stages.append({
                "phase": "4. Animación de Vídeo (I2V)",
                "tool": f"Fal.ai · {i2v_label}",
                "status": "error",
                "needed": f"{optimal_scenes} clips × 10s = {total_i2v_sec}s (${vid_cost_usd:.2f} USD)",
                "available": fal_st.get("label", "Saldo agotado en Fal.ai"),
                "cost_usd": vid_cost_usd,
                "billing_url": fal_st.get("billing_url"),
            })

    # 5. Renderizado Final y Subtítulos
    stages.append({
        "phase": "5. Montaje y Subtítulos (.ass)",
        "tool": "FFmpeg Local",
        "status": ffmpeg_st.get("status", "ok"),
        "needed": f"Vídeo final ~{est_audio_sec}s en 1080x1920",
        "available": ffmpeg_st.get("label", "Instalado localmente (0€)"),
        "cost_usd": 0.0,
        "billing_url": None,
    })

    overall_status = "ready" if not blockers else "action_required"
    if overall_status == "ready":
        overall_summary = (
            f"✅ Viable con la calidad seleccionada: todas las herramientas están operativas. "
            f"Coste total estimado para este capítulo ({optimal_scenes} escenas, ~{est_audio_sec}s): ${total_cost_usd:.2f} USD."
        )
    else:
        overall_summary = (
            f"⚠️ Atención antes de empezar: necesitas recargar saldo para completar el capítulo con la calidad máxima "
            f"(coste estimado: ${total_cost_usd:.2f} USD)."
        )

    return {
        "success": True,
        "overall_status": overall_status,
        "overall_summary": overall_summary,
        "blockers": blockers,
        "metrics": {
            "is_estimate": is_estimate,
            "words": words,
            "chars": chars,
            "est_audio_sec": est_audio_sec,
            "optimal_scenes": optimal_scenes,
            "total_i2v_sec": total_i2v_sec,
            "img_cost_usd": img_cost_usd,
            "vid_cost_usd": vid_cost_usd,
            "total_cost_usd": total_cost_usd,
            "i2v_model_label": i2v_label,
        },
        "stages": stages,
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
                    formato_vista=char.get("formato_vista") or "cuerpo_entero"
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
            "formato_vista": char.get("formato_vista") or "cuerpo_entero",
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


