import os
import re
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

from app.core.project_manager import (
    get_project,
    save_or_update_project,
    get_project_folder,
    list_all_projects,
    get_project_chapter,
    save_project_chapter,
    list_project_chapters,
    generate_character_portrait,
    generate_environment_image,
    slugify
)
from app.core.video_renderer import (
    render_single_scene_preview_clip,
    resolve_media_path
)
from app.core.image_engine import generate_image

load_dotenv()

# Token y Chat ID por defecto configurados en el ecosistema 2026
DEFAULT_BOT_TOKEN = "8691202872:AAGolw9n9HOGSos7NTlYHZJg-AeW4cMNzgU"
DEFAULT_CHAT_ID = "7156474626"
DEFAULT_N8N_WEBHOOK_URL = "http://127.0.0.1:5678/webhook/videostudio-scene-approval"

_LAST_UPDATE_OFFSET: int = 0

def get_n8n_webhook_config() -> Tuple[str, bool]:
    """Obtiene la URL del webhook de n8n para envío/orquestación de clips y su estado."""
    webhook_url = os.getenv("N8N_WEBHOOK_CLIPS_URL") or DEFAULT_N8N_WEBHOOK_URL
    n8n_enabled = os.getenv("N8N_WEBHOOK_ENABLED", "true").lower() in ("true", "1", "yes")
    return webhook_url, n8n_enabled

def trigger_n8n_clip_approval_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía los metadatos del clip generado al webhook de n8n antes del ensamblado final.
    Si la instancia de n8n no está accesible en tiempo real, registra el evento con fallback
    limpio para que el envío directo por Telegram Bot API continúe sin interrupción.
    """
    webhook_url, n8n_enabled = get_n8n_webhook_config()
    if not n8n_enabled or not webhook_url:
        return {"triggered": False, "webhook_url": webhook_url, "reason": "n8n webhook deshabilitado"}

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            return {
                "triggered": True,
                "webhook_url": webhook_url,
                "status_code": resp.status,
                "response": resp_body[:500]
            }
    except Exception as e:
        return {
            "triggered": False,
            "webhook_url": webhook_url,
            "fallback": "direct_telegram_bot_api",
            "note": str(e)
        }

def get_telegram_config() -> Tuple[str, str, bool]:
    """Obtiene el token, chat_id y estado de activación para Telegram Approvals."""
    token = os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_BOT_TOKEN
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or DEFAULT_CHAT_ID
    enabled = os.getenv("TELEGRAM_APPROVALS_ENABLED", "true").lower() in ("true", "1", "yes")

    # Si no están en env, intentar leer desde .env.keys global
    if not token or not chat_id:
        try:
            keys_path = Path("D:/OneDrive/04_Desarrollo_proyectos/0000_Utilidades/04_Claves_Subcripciones_APIs/.env.keys")
            if keys_path.exists():
                with open(keys_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_BOT_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                        elif line.startswith("TELEGRAM_CHAT_ID="):
                            chat_id = line.split("=", 1)[1].strip()
        except Exception:
            pass

    return token or DEFAULT_BOT_TOKEN, chat_id or DEFAULT_CHAT_ID, enabled

def send_telegram_api(method: str, payload: Dict[str, Any], files: Optional[Dict[str, Path]] = None) -> Dict[str, Any]:
    """Llama a la API de Telegram Bot con payload y archivos multipart opcionales."""
    token, _, _ = get_telegram_config()
    if not token:
        return {"ok": False, "error": "Token de Telegram no configurado"}

    url = f"https://api.telegram.org/bot{token}/{method}"

    if not files:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # Multipart form-data para subida de imágenes (sendPhoto)
    boundary = f"----WebKitFormBoundaryVideoStudio{int(time.time()*1000)}"
    parts: List[bytes] = []

    for k, v in payload.items():
        if v is not None:
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))

    for field_name, file_path in files.items():
        if file_path.exists():
            fname = file_path.name
            lower_fname = fname.lower()
            if lower_fname.endswith(".mp4"):
                mime = "video/mp4"
            elif lower_fname.endswith(".mp3"):
                mime = "audio/mpeg"
            elif lower_fname.endswith(".png"):
                mime = "image/png"
            else:
                mime = "image/jpeg"
            with open(file_path, "rb") as f:
                content = f.read()
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{fname}\"\r\nContent-Type: {mime}\r\n\r\n".encode("utf-8")
            )
            parts.append(content)
            parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def find_item_image_path(project_id: str, category: str, item_id: str) -> Optional[Path]:
    """Localiza el archivo de imagen en disco para un personaje o escenario."""
    folder = get_project_folder(project_id)
    sub_dir = folder / ("personajes" if category in ("c", "character", "personaje") else "escenarios")
    
    for ext in (".jpg", ".png", ".jpeg"):
        candidate = sub_dir / f"{item_id}{ext}"
        if candidate.exists() and candidate.stat().st_size > 1000:
            return candidate
    return None

def send_character_approval(
    project_id: str,
    character_id: str,
    prompt_override: Optional[str] = None,
    auto_generate_if_missing: bool = True
) -> Dict[str, Any]:
    """
    Envía una propuesta de personaje por Telegram solicitando aprobación Human-in-the-Loop.
    Incluye la imagen del personaje y botones interactivos: Aprobar, Rechazar, Rehacer.
    """
    token, chat_id, enabled = get_telegram_config()
    if not enabled:
        return {"ok": False, "error": "Integración Telegram de aprobaciones desactivada"}

    proj = get_project(project_id)
    char = next(
        (c for c in proj.get("personajes", []) if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id),
        None
    )
    if not char:
        raise ValueError(f"Personaje '{character_id}' no encontrado en el proyecto '{project_id}'.")

    # Localizar imagen existente o generarla
    img_path = find_item_image_path(project_id, "character", character_id)
    if not img_path and auto_generate_if_missing:
        gen_res = generate_character_portrait(project_id, character_id, prompt_override=prompt_override)
        if gen_res.get("saved_path") and Path(gen_res["saved_path"]).exists():
            img_path = Path(gen_res["saved_path"])

    proj_title = proj.get("titulo", project_id)
    char_name = char.get("nombre", character_id)
    char_role = char.get("rol", "Personaje")
    char_type = char.get("tipo", "humano")
    char_desc = char.get("descripcion_visual", "Sin descripción visual detallada.")
    style_vis = proj.get("estilo_visual", "cinematic")

    caption = (
        f"🎨 <b>PROPUESTA DE PERSONAJE</b>\n\n"
        f"👤 <b>Nombre:</b> {char_name}\n"
        f"📖 <b>Proyecto:</b> {proj_title}\n"
        f"🎭 <b>Rol:</b> {char_role} | <b>Tipo:</b> {char_type}\n"
        f"🖌 <b>Estilo:</b> {style_vis}\n\n"
        f"📝 <b>Descripción de propuesta:</b>\n<i>{char_desc}</i>\n\n"
        f"👉 <b>¿Apruebas esta propuesta para la serie?</b>\n"
        f"• Pulsa un botón o responde con «<b>aprobar</b>» o «<b>rechazar</b>» («<b>sí</b>» o «<b>no</b>»).\n"
        f"• Si es que no, indica el motivo para revisarlo porque no cuadra, o pulsa <b>Rehacer</b>."
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Aprobar (Sí)", "callback_data": f"appr:c:{project_id}:{character_id}"},
                {"text": "❌ Rechazar (No)", "callback_data": f"rejc:c:{project_id}:{character_id}"}
            ],
            [
                {"text": "🔄 Rehacer propuesta (No cuadra)", "callback_data": f"redo:c:{project_id}:{character_id}"}
            ]
        ]
    }

    if img_path and img_path.exists():
        api_res = send_telegram_api(
            "sendPhoto",
            payload={
                "chat_id": chat_id,
                "caption": caption[:1024],
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            },
            files={"photo": img_path}
        )
    else:
        # Fallback si no hay imagen física disponible
        api_res = send_telegram_api(
            "sendMessage",
            payload={
                "chat_id": chat_id,
                "text": f"{caption}\n\n<i>(Nota: No se encontró la imagen en disco, pendiente de generación)</i>",
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            }
        )

    if api_res.get("ok"):
        msg_id = api_res.get("result", {}).get("message_id")
        char["estado_aprobacion"] = "pendiente"
        char["telegram_message_id"] = msg_id
        char["propuesta_enviada_en"] = datetime.now().isoformat()
        char["motivo_rechazo"] = ""
        save_or_update_project(proj)
        return {
            "ok": True,
            "message_id": msg_id,
            "character_id": character_id,
            "status": "pendiente",
            "telegram_response": api_res
        }
    else:
        return {"ok": False, "error": api_res.get("error", "Error desconocido en Telegram API")}

def send_environment_approval(
    project_id: str,
    environment_id: str,
    prompt_override: Optional[str] = None,
    auto_generate_if_missing: bool = True
) -> Dict[str, Any]:
    """
    Envía una propuesta de escenario por Telegram solicitando aprobación Human-in-the-Loop.
    Incluye la imagen del escenario y botones interactivos: Aprobar, Rechazar, Rehacer.
    """
    token, chat_id, enabled = get_telegram_config()
    if not enabled:
        return {"ok": False, "error": "Integración Telegram de aprobaciones desactivada"}

    proj = get_project(project_id)
    esc = next(
        (e for e in proj.get("escenarios", []) if e.get("id") == environment_id or slugify(e.get("nombre", "")) == environment_id),
        None
    )
    if not esc:
        raise ValueError(f"Escenario '{environment_id}' no encontrado en el proyecto '{project_id}'.")

    # Localizar imagen existente o generarla
    img_path = find_item_image_path(project_id, "environment", environment_id)
    if not img_path and auto_generate_if_missing:
        gen_res = generate_environment_image(project_id, environment_id, prompt_override=prompt_override)
        if gen_res.get("saved_path") and Path(gen_res["saved_path"]).exists():
            img_path = Path(gen_res["saved_path"])

    proj_title = proj.get("titulo", project_id)
    esc_name = esc.get("nombre", environment_id)
    esc_type = esc.get("tipo", "exterior_urbano")
    esc_desc = esc.get("descripcion_visual", "Sin descripción de entorno detallada.")
    style_vis = proj.get("estilo_visual", "cinematic")

    caption = (
        f"🏛️ <b>PROPUESTA DE ESCENARIO</b>\n\n"
        f"📍 <b>Nombre:</b> {esc_name}\n"
        f"📖 <b>Proyecto:</b> {proj_title}\n"
        f"🏷 <b>Tipo:</b> {esc_type}\n"
        f"🖌 <b>Estilo:</b> {style_vis}\n\n"
        f"📝 <b>Descripción de escenario:</b>\n<i>{esc_desc}</i>\n\n"
        f"👉 <b>¿Apruebas este escenario para el universo?</b>\n"
        f"• Pulsa un botón o responde con «<b>aprobar</b>» o «<b>rechazar</b>» («<b>sí</b>» o «<b>no</b>»).\n"
        f"• Si es que no, indica el motivo para revisarlo porque no cuadra, o pulsa <b>Rehacer</b>."
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Aprobar (Sí)", "callback_data": f"appr:e:{project_id}:{environment_id}"},
                {"text": "❌ Rechazar (No)", "callback_data": f"rejc:e:{project_id}:{environment_id}"}
            ],
            [
                {"text": "🔄 Rehacer propuesta (No cuadra)", "callback_data": f"redo:e:{project_id}:{environment_id}"}
            ]
        ]
    }

    if img_path and img_path.exists():
        api_res = send_telegram_api(
            "sendPhoto",
            payload={
                "chat_id": chat_id,
                "caption": caption[:1024],
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            },
            files={"photo": img_path}
        )
    else:
        api_res = send_telegram_api(
            "sendMessage",
            payload={
                "chat_id": chat_id,
                "text": f"{caption}\n\n<i>(Nota: No se encontró la imagen en disco, pendiente de generación)</i>",
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            }
        )

    if api_res.get("ok"):
        msg_id = api_res.get("result", {}).get("message_id")
        esc["estado_aprobacion"] = "pendiente"
        esc["telegram_message_id"] = msg_id
        esc["propuesta_enviada_en"] = datetime.now().isoformat()
        esc["motivo_rechazo"] = ""
        save_or_update_project(proj)
        return {
            "ok": True,
            "message_id": msg_id,
            "environment_id": environment_id,
            "status": "pendiente",
            "telegram_response": api_res
        }
    else:
        return {"ok": False, "error": api_res.get("error", "Error desconocido en Telegram API")}

def send_project_initial_proposals(project_id: str) -> Dict[str, Any]:
    """
    Envía todas las propuestas iniciales de personajes y escenarios de un proyecto a Telegram
    para su validación interactiva inicial.
    """
    proj = get_project(project_id)
    sent_chars = []
    sent_envs = []
    errors = []

    for char in proj.get("personajes", []):
        cid = char.get("id") or slugify(char.get("nombre", ""))
        try:
            res = send_character_approval(project_id, cid)
            if res.get("ok"):
                sent_chars.append(char.get("nombre", cid))
            else:
                errors.append(f"Personaje {cid}: {res.get('error')}")
        except Exception as e:
            errors.append(f"Personaje {cid}: {str(e)}")

    for esc in proj.get("escenarios", []):
        eid = esc.get("id") or slugify(esc.get("nombre", ""))
        try:
            res = send_environment_approval(project_id, eid)
            if res.get("ok"):
                sent_envs.append(esc.get("nombre", eid))
            else:
                errors.append(f"Escenario {eid}: {res.get('error')}")
        except Exception as e:
            errors.append(f"Escenario {eid}: {str(e)}")

    # Mensaje global de resumen a Telegram
    _, chat_id, enabled = get_telegram_config()
    if enabled and (sent_chars or sent_envs):
        summary_text = (
            f"🚀 <b>PROPUESTAS INICIALES ENVIADAS</b>\n\n"
            f"📖 <b>Proyecto:</b> {proj.get('titulo', project_id)}\n"
            f"👥 <b>Personajes ({len(sent_chars)}):</b> {', '.join(sent_chars) if sent_chars else 'Ninguno'}\n"
            f"🏞 <b>Escenarios ({len(sent_envs)}):</b> {', '.join(sent_envs) if sent_envs else 'Ninguno'}\n\n"
            f"<i>Por favor, revisa cada una de las imágenes anteriores y responde aprobando o solicitando cambios.</i>"
        )
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": summary_text, "parse_mode": "HTML"})

    return {
        "ok": True,
        "sent_characters": sent_chars,
        "sent_environments": sent_envs,
        "errors": errors
    }

def apply_approval_decision(
    project_id: str,
    item_type: str,
    item_id: str,
    action: str,
    feedback: str = "",
    notify_telegram: bool = True
) -> Dict[str, Any]:
    """
    Aplica la decisión humana (Aprobar, Rechazar o Rehacer) sobre un personaje o escenario.
    Actualiza el proyecto y notifica al usuario por Telegram.
    """
    proj = get_project(project_id)
    is_char = item_type.lower() in ("c", "char", "character", "personaje")
    collection_key = "personajes" if is_char else "escenarios"
    items = proj.get(collection_key, [])

    match_item = None
    for item in items:
        if item.get("id") == item_id or slugify(item.get("nombre", "")) == item_id:
            match_item = item
            break

    if not match_item:
        raise ValueError(f"Elemento '{item_id}' no encontrado en {collection_key} del proyecto '{project_id}'.")

    item_name = match_item.get("nombre", item_id)
    tipo_label = "el personaje" if is_char else "el escenario"
    now_iso = datetime.now().isoformat()
    _, chat_id, enabled = get_telegram_config()

    action_norm = action.strip().lower()

    if action_norm in ("appr", "approve", "aprobado", "aprobar", "si", "sí", "ok"):
        match_item["estado_aprobacion"] = "aprobado"
        match_item["aprobado_en"] = now_iso
        match_item["motivo_rechazo"] = ""
        save_or_update_project(proj)

        if notify_telegram and enabled:
            msg = (
                f"✅ <b>¡APROBADO!</b>\n\n"
                f"Has aprobado {tipo_label} <b>{item_name}</b> para el proyecto <b>{proj.get('titulo', project_id)}</b>.\n"
                f"Queda fijado oficialmente en la biblia visual del universo. 🎬"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

        return {
            "ok": True,
            "status": "aprobado",
            "item_id": item_id,
            "nombre": item_name,
            "collection": collection_key
        }

    elif action_norm in ("rejc", "reject", "rechazado", "rechazar", "no"):
        clean_feedback = feedback.strip() if feedback else "No cuadra con la visión esperada."
        match_item["estado_aprobacion"] = "rechazado"
        match_item["motivo_rechazo"] = clean_feedback
        save_or_update_project(proj)

        if notify_telegram and enabled:
            msg = (
                f"❌ <b>RECHAZADO / PARA REVISIÓN</b>\n\n"
                f"Has rechazado {tipo_label} <b>{item_name}</b>.\n"
                f"💬 <b>Observación/Motivo:</b> {clean_feedback}\n\n"
                f"<i>Puedes editar la descripción en el estudio o solicitar rehacerlo en cualquier momento.</i>"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

        return {
            "ok": True,
            "status": "rechazado",
            "item_id": item_id,
            "nombre": item_name,
            "collection": collection_key,
            "motivo_rechazo": clean_feedback
        }

    elif action_norm in ("redo", "rehacer", "regenerar"):
        # Rehacer propuesta: regenerar imagen con nueva semilla y volver a enviar propuesta
        clean_feedback = feedback.strip() if feedback else "Propuesta anterior no cuadraba."
        match_item["estado_aprobacion"] = "pendiente"
        match_item["motivo_rechazo"] = f"Rehecho: {clean_feedback}"
        save_or_update_project(proj)

        if notify_telegram and enabled:
            prep_msg = (
                f"🔄 <b>REHACIENDO PROPUESTA</b>\n\n"
                f"Regenerando {tipo_label} <b>{item_name}</b> porque no cuadraba...\n"
                f"<i>Enseguida recibirás la nueva propuesta visual por este canal.</i>"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": prep_msg, "parse_mode": "HTML"})

        # Generar nueva imagen
        if is_char:
            generate_character_portrait(project_id, item_id)
            res_new = send_character_approval(project_id, item_id, auto_generate_if_missing=False)
        else:
            generate_environment_image(project_id, item_id)
            res_new = send_environment_approval(project_id, item_id, auto_generate_if_missing=False)

        return {
            "ok": True,
            "status": "rehecho_y_enviado",
            "item_id": item_id,
            "nombre": item_name,
            "collection": collection_key,
            "new_proposal": res_new
        }

    else:
        raise ValueError(f"Acción '{action}' no reconocida. Usa 'approve', 'reject' o 'redo'.")

def send_scene_clip_approval(
    project_id: str,
    chapter_id: str,
    scene_id: int,
    render_clip_if_missing: bool = True,
    enable_ken_burns: bool = False,
    trigger_n8n: bool = True
) -> Dict[str, Any]:
    """
    Envía un clip de escena generado (antes del ensamblado final) por Telegram y al Webhook de n8n,
    incluyendo botones interactivos 'Aprobar' y 'Regenerar escena'.
    """
    token, chat_id, enabled = get_telegram_config()
    if not enabled:
        return {"ok": False, "error": "Integración Telegram de aprobaciones desactivada"}

    proj = get_project(project_id)
    chapter = get_project_chapter(project_id, chapter_id)
    scenes = chapter.get("scenes", [])

    scene_index = -1
    target_scene: Optional[Dict[str, Any]] = None
    for idx, sc in enumerate(scenes):
        sc_id = sc.get("id") or (idx + 1)
        if int(sc_id) == int(scene_id):
            scene_index = idx
            target_scene = sc
            break

    if target_scene is None and 1 <= int(scene_id) <= len(scenes):
        scene_index = int(scene_id) - 1
        target_scene = scenes[scene_index]

    if target_scene is None:
        raise ValueError(f"Escena {scene_id} no encontrada en capítulo '{chapter_id}' del proyecto '{project_id}'.")

    actual_scene_id = int(target_scene.get("id") or (scene_index + 1))

    # Localizar clip MP4 existente o renderizarlo antes del ensamblado final
    clip_path: Optional[Path] = None
    if target_scene.get("clip_url"):
        cand = resolve_media_path(target_scene["clip_url"])
        if cand.exists() and cand.stat().st_size > 1000:
            clip_path = cand

    if not clip_path and render_clip_if_missing and target_scene.get("image_url"):
        try:
            clip_res = render_single_scene_preview_clip(
                scene=target_scene,
                scene_index=scene_index,
                project_id=project_id,
                chapter_id=chapter_id,
                enable_subtitles=True,
                enable_ken_burns=enable_ken_burns
            )
            if clip_res.get("ok") and clip_res.get("clip_path"):
                clip_path = Path(clip_res["clip_path"])
                target_scene["clip_url"] = clip_res["clip_url"]
                target_scene["duracion_real"] = clip_res.get("duration") or target_scene.get("duracion_real")
        except Exception as e:
            print(f"[Telegram Clip Render Fallback] {e}")

    img_path: Optional[Path] = None
    if target_scene.get("image_url"):
        cand_img = resolve_media_path(target_scene["image_url"])
        if cand_img.exists():
            img_path = cand_img

    proj_title = proj.get("titulo", project_id)
    chap_title = chapter.get("titulo", chapter_id)
    narrador = target_scene.get("narrador", "Sin texto de narración.")
    chars_list = ", ".join(target_scene.get("personajes_en_escena", [])) or "Sin personajes específicos"
    esc_clave = target_scene.get("escenario_clave") or "General"
    dur_val = target_scene.get("duracion_real") or target_scene.get("duracion_estimada") or 5

    caption = (
        f"🎬 <b>APROBACIÓN DE CLIP DE ESCENA (PRE-ENSAMBLADO)</b>\n\n"
        f"📖 <b>Proyecto:</b> {proj_title}\n"
        f"📑 <b>Capítulo:</b> {chap_title}\n"
        f"🎞 <b>Escena:</b> #{actual_scene_id} de {len(scenes)} ({dur_val}s)\n"
        f"👥 <b>Personajes:</b> {chars_list}\n"
        f"🏛 <b>Escenario:</b> {esc_clave}\n\n"
        f"🎙 <b>Locución:</b>\n<i>«{narrador}»</i>\n\n"
        f"👉 <b>¿Apruebas este clip antes del ensamblado final?</b>\n"
        f"• Pulsa <b>✅ Aprobar</b> o <b>🔄 Regenerar escena</b>."
    )

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Aprobar", "callback_data": f"appr:s:{project_id}:{chapter_id}:{actual_scene_id}"},
                {"text": "🔄 Regenerar escena", "callback_data": f"redo:s:{project_id}:{chapter_id}:{actual_scene_id}"}
            ],
            [
                {"text": "❌ Rechazar escena", "callback_data": f"rejc:s:{project_id}:{chapter_id}:{actual_scene_id}"}
            ]
        ]
    }

    # Notificar también al Webhook de n8n (Orquestación Human-in-the-Loop)
    n8n_res = {"triggered": False}
    if trigger_n8n:
        n8n_payload = {
            "event": "scene_clip_ready_for_approval",
            "project_id": project_id,
            "project_title": proj_title,
            "chapter_id": chapter_id,
            "chapter_title": chap_title,
            "scene_id": actual_scene_id,
            "total_scenes": len(scenes),
            "narrador": narrador,
            "prompt_imagen": target_scene.get("prompt_imagen", ""),
            "clip_url": target_scene.get("clip_url"),
            "clip_path": str(clip_path) if clip_path else None,
            "image_url": target_scene.get("image_url"),
            "audio_url": target_scene.get("audio_url"),
            "duration": dur_val,
            "chat_id": chat_id,
            "inline_keyboard": inline_keyboard,
            "buttons": ["✅ Aprobar", "🔄 Regenerar escena"],
            "decision_webhook_url": f"http://127.0.0.1:8001/api/projects/{project_id}/chapters/{chapter_id}/scenes/{actual_scene_id}/decision"
        }
        n8n_res = trigger_n8n_clip_approval_webhook(n8n_payload)

    # Enviar el clip de vídeo MP4 por Telegram (o imagen/mensaje como fallback)
    if clip_path and clip_path.exists():
        api_res = send_telegram_api(
            "sendVideo",
            payload={
                "chat_id": chat_id,
                "caption": caption[:1024],
                "parse_mode": "HTML",
                "supports_streaming": "true",
                "reply_markup": json.dumps(inline_keyboard)
            },
            files={"video": clip_path}
        )
    elif img_path and img_path.exists():
        api_res = send_telegram_api(
            "sendPhoto",
            payload={
                "chat_id": chat_id,
                "caption": caption[:1024],
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            },
            files={"photo": img_path}
        )
    else:
        api_res = send_telegram_api(
            "sendMessage",
            payload={
                "chat_id": chat_id,
                "text": caption,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(inline_keyboard)
            }
        )

    if api_res.get("ok"):
        msg_id = api_res.get("result", {}).get("message_id")
        target_scene["estado_aprobacion"] = "pendiente"
        target_scene["telegram_message_id"] = msg_id
        target_scene["propuesta_enviada_en"] = datetime.now().isoformat()
        target_scene["motivo_rechazo"] = ""
        chapter["aprobacion_clips_status"] = "en_revision"
        save_project_chapter(project_id, chapter)
        return {
            "ok": True,
            "message_id": msg_id,
            "project_id": project_id,
            "chapter_id": chapter_id,
            "scene_id": actual_scene_id,
            "clip_url": target_scene.get("clip_url"),
            "status": "pendiente",
            "buttons_sent": ["✅ Aprobar", "🔄 Regenerar escena"],
            "inline_keyboard": inline_keyboard,
            "n8n_webhook": n8n_res,
            "telegram_response": api_res
        }
    else:
        return {
            "ok": False,
            "error": api_res.get("error", "Error enviando clip a Telegram"),
            "n8n_webhook": n8n_res
        }

def send_chapter_clips_for_approval(
    project_id: str,
    chapter_id: str,
    render_clips_if_missing: bool = True,
    enable_ken_burns: bool = False,
    trigger_n8n: bool = True
) -> Dict[str, Any]:
    """
    Envía todos los clips de las escenas de un capítulo por Telegram y n8n
    para su aprobación humana antes del ensamblado final del vídeo MP4.
    """
    chapter = get_project_chapter(project_id, chapter_id)
    proj = get_project(project_id)
    scenes = chapter.get("scenes", [])
    if not scenes:
        raise ValueError(f"El capítulo '{chapter_id}' no tiene escenas generadas.")

    sent_scenes = []
    errors = []

    for idx, sc in enumerate(scenes):
        sc_id = int(sc.get("id") or (idx + 1))
        try:
            res = send_scene_clip_approval(
                project_id=project_id,
                chapter_id=chapter_id,
                scene_id=sc_id,
                render_clip_if_missing=render_clips_if_missing,
                enable_ken_burns=enable_ken_burns,
                trigger_n8n=trigger_n8n
            )
            if res.get("ok"):
                sent_scenes.append({
                    "scene_id": sc_id,
                    "message_id": res.get("message_id"),
                    "clip_url": res.get("clip_url"),
                    "status": res.get("status")
                })
            else:
                errors.append(f"Escena {sc_id}: {res.get('error')}")
        except Exception as e:
            errors.append(f"Escena {sc_id}: {str(e)}")

    _, chat_id, enabled = get_telegram_config()
    if enabled and sent_scenes:
        summary_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Aprobar Todas las Escenas (Listo para Ensamblar)",
                        "callback_data": f"appr_all:ch:{project_id}:{chapter_id}"
                    }
                ]
            ]
        }
        summary_text = (
            f"🎞 <b>CLIPS ENVIADOS PARA APROBACIÓN PRE-ENSAMBLADO</b>\n\n"
            f"📖 <b>Proyecto:</b> {proj.get('titulo', project_id)}\n"
            f"📑 <b>Capítulo:</b> {chapter.get('titulo', chapter_id)}\n"
            f"🎬 <b>Clips enviados:</b> {len(sent_scenes)} de {len(scenes)}\n\n"
            f"<i>Revisa cada clip arriba y pulsa «✅ Aprobar» o «🔄 Regenerar escena» antes de ensamblar el MP4 definitivo.</i>"
        )
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": summary_text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(summary_keyboard)
            }
        )

    return {
        "ok": len(sent_scenes) > 0,
        "project_id": project_id,
        "chapter_id": chapter_id,
        "sent_scenes_count": len(sent_scenes),
        "total_scenes": len(scenes),
        "sent_scenes": sent_scenes,
        "errors": errors
    }

def apply_scene_approval_decision(
    project_id: str,
    chapter_id: str,
    scene_id: int,
    action: str,
    feedback: str = "",
    notify_telegram: bool = True,
    auto_regenerate_media: bool = False
) -> Dict[str, Any]:
    """
    Aplica la decisión humana ('Aprobar', 'Regenerar escena' o 'Rechazar') sobre el clip de una escena.
    Actualiza capitulo.json y notifica por Telegram.
    """
    proj = get_project(project_id)
    chapter = get_project_chapter(project_id, chapter_id)
    scenes = chapter.get("scenes", [])

    scene_index = -1
    target_scene: Optional[Dict[str, Any]] = None
    for idx, sc in enumerate(scenes):
        sc_id = sc.get("id") or (idx + 1)
        if int(sc_id) == int(scene_id):
            scene_index = idx
            target_scene = sc
            break

    if target_scene is None and 1 <= int(scene_id) <= len(scenes):
        scene_index = int(scene_id) - 1
        target_scene = scenes[scene_index]

    if target_scene is None:
        raise ValueError(f"Escena {scene_id} no encontrada en capítulo '{chapter_id}' del proyecto '{project_id}'.")

    actual_scene_id = int(target_scene.get("id") or (scene_index + 1))
    now_iso = datetime.now().isoformat()
    _, chat_id, enabled = get_telegram_config()
    action_norm = action.strip().lower()

    if action_norm in ("appr", "approve", "aprobado", "aprobar", "si", "sí", "ok"):
        target_scene["estado_aprobacion"] = "aprobado"
        target_scene["aprobado_en"] = now_iso
        target_scene["motivo_rechazo"] = ""

        all_approved = all(s.get("estado_aprobacion") == "aprobado" for s in scenes)
        chapter["aprobacion_clips_status"] = "aprobado_listo_ensamblar" if all_approved else "en_revision"
        save_project_chapter(project_id, chapter)

        if notify_telegram and enabled:
            ready_note = (
                "\n\n🎉 <b>¡Todas las escenas del capítulo están aprobadas!</b> Ya puedes ejecutar el ensamblado final del vídeo."
                if all_approved else ""
            )
            msg = (
                f"✅ <b>¡CLIP DE ESCENA #{actual_scene_id} APROBADO!</b>\n\n"
                f"📑 <b>Capítulo:</b> {chapter.get('titulo', chapter_id)}\n"
                f"📖 <b>Proyecto:</b> {proj.get('titulo', project_id)}"
                f"{ready_note}"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

        return {
            "ok": True,
            "status": "aprobado",
            "project_id": project_id,
            "chapter_id": chapter_id,
            "scene_id": actual_scene_id,
            "all_scenes_approved": all_approved,
            "chapter_approval_status": chapter["aprobacion_clips_status"]
        }

    elif action_norm in ("redo", "rehacer", "regenerar", "regenerar_escena", "regenerar escena"):
        clean_feedback = feedback.strip() if feedback else "Solicitada regeneración de escena desde Telegram."
        target_scene["estado_aprobacion"] = "regenerando"
        target_scene["motivo_rechazo"] = clean_feedback
        target_scene["regeneraciones_count"] = int(target_scene.get("regeneraciones_count") or 0) + 1
        chapter["aprobacion_clips_status"] = "en_revision"
        save_project_chapter(project_id, chapter)

        if notify_telegram and enabled:
            prep_msg = (
                f"🔄 <b>REGENERANDO ESCENA #{actual_scene_id}</b>\n\n"
                f"📑 <b>Capítulo:</b> {chapter.get('titulo', chapter_id)}\n"
                f"💬 <b>Motivo:</b> {clean_feedback}\n"
                f"<i>Generando nueva versión del clip antes del ensamblado final...</i>"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": prep_msg, "parse_mode": "HTML"})

        new_proposal = None
        if auto_regenerate_media:
            try:
                prompt_img = target_scene.get("prompt_imagen") or f"Scene {actual_scene_id}, vertical 9:16"
                new_seed = int(time.time()) % 999999
                img_res = generate_image(
                    prompt=prompt_img,
                    provider="flux",
                    seed=new_seed,
                    reference_image=target_scene.get("reference_image")
                )
                if img_res.get("url"):
                    target_scene["image_url"] = img_res["url"]
                clip_res = render_single_scene_preview_clip(
                    scene=target_scene,
                    scene_index=scene_index,
                    project_id=project_id,
                    chapter_id=chapter_id,
                    enable_subtitles=True,
                    enable_ken_burns=False
                )
                if clip_res.get("clip_url"):
                    target_scene["clip_url"] = clip_res["clip_url"]
                save_project_chapter(project_id, chapter)
            except Exception as e:
                print(f"[Auto Regenerate Scene Error] {e}")

            new_proposal = send_scene_clip_approval(
                project_id=project_id,
                chapter_id=chapter_id,
                scene_id=actual_scene_id,
                render_clip_if_missing=False,
                trigger_n8n=True
            )
        else:
            # Marcar como pendiente de revisión / regeneración solicitada
            target_scene["estado_aprobacion"] = "regenerar_solicitado"
            save_project_chapter(project_id, chapter)

        return {
            "ok": True,
            "status": "regenerar_escena",
            "project_id": project_id,
            "chapter_id": chapter_id,
            "scene_id": actual_scene_id,
            "motivo": clean_feedback,
            "regeneraciones_count": target_scene["regeneraciones_count"],
            "new_proposal": new_proposal
        }

    elif action_norm in ("rejc", "reject", "rechazado", "rechazar", "no"):
        clean_feedback = feedback.strip() if feedback else "Escena descartada para revisión."
        target_scene["estado_aprobacion"] = "rechazado"
        target_scene["motivo_rechazo"] = clean_feedback
        chapter["aprobacion_clips_status"] = "en_revision"
        save_project_chapter(project_id, chapter)

        if notify_telegram and enabled:
            msg = (
                f"❌ <b>ESCENA #{actual_scene_id} RECHAZADA</b>\n\n"
                f"📑 <b>Capítulo:</b> {chapter.get('titulo', chapter_id)}\n"
                f"💬 <b>Motivo:</b> {clean_feedback}"
            )
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})

        return {
            "ok": True,
            "status": "rechazado",
            "project_id": project_id,
            "chapter_id": chapter_id,
            "scene_id": actual_scene_id,
            "motivo_rechazo": clean_feedback
        }

    else:
        raise ValueError(f"Acción '{action}' no reconocida para escena. Usa 'approve', 'redo' o 'reject'.")

def find_item_by_message_id(message_id: int) -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
    """
    Busca qué personaje, escenario o clip de escena coincide con un message_id de Telegram.
    Devuelve (project_id, item_type ['c', 'e' o 's:{chapter_id}'], item_id, item_data) o None.
    """
    all_projs = list_all_projects()
    for p_summary in all_projs:
        pid = p_summary.get("id")
        try:
            full_proj = get_project(pid)
            for c in full_proj.get("personajes", []):
                if c.get("telegram_message_id") == message_id:
                    return pid, "c", c.get("id"), c
            for e in full_proj.get("escenarios", []):
                if e.get("telegram_message_id") == message_id:
                    return pid, "e", e.get("id"), e
            for ch_summary in list_project_chapters(pid):
                chid = ch_summary.get("id")
                if not chid:
                    continue
                ch_data = get_project_chapter(pid, chid)
                for idx, sc in enumerate(ch_data.get("scenes", [])):
                    if sc.get("telegram_message_id") == message_id:
                        sc_id = str(sc.get("id") or (idx + 1))
                        return pid, f"s:{chid}", sc_id, sc
        except Exception:
            continue
    return None

def find_latest_pending_item() -> Optional[Tuple[str, str, str, Dict[str, Any]]]:
    """
    Localiza la propuesta pendiente más reciente enviada a Telegram across all projects
    (incluyendo personajes, escenarios y clips de escenas).
    """
    candidates = []
    all_projs = list_all_projects()
    for p_summary in all_projs:
        pid = p_summary.get("id")
        try:
            full_proj = get_project(pid)
            for c in full_proj.get("personajes", []):
                if c.get("estado_aprobacion") == "pendiente" and c.get("propuesta_enviada_en"):
                    candidates.append((c["propuesta_enviada_en"], pid, "c", c.get("id"), c))
            for e in full_proj.get("escenarios", []):
                if e.get("estado_aprobacion") == "pendiente" and e.get("propuesta_enviada_en"):
                    candidates.append((e["propuesta_enviada_en"], pid, "e", e.get("id"), e))
            for ch_summary in list_project_chapters(pid):
                chid = ch_summary.get("id")
                if not chid:
                    continue
                ch_data = get_project_chapter(pid, chid)
                for idx, sc in enumerate(ch_data.get("scenes", [])):
                    if sc.get("estado_aprobacion") in ("pendiente", "regenerar_solicitado") and sc.get("propuesta_enviada_en"):
                        sc_id = str(sc.get("id") or (idx + 1))
                        candidates.append((sc["propuesta_enviada_en"], pid, f"s:{chid}", sc_id, sc))
        except Exception:
            continue

    if not candidates:
        return None

    # Ordenar por fecha enviada descendente
    candidates.sort(key=lambda x: x[0], reverse=True)
    best = candidates[0]
    return best[1], best[2], best[3], best[4]

def parse_natural_language_decision(text: str) -> Tuple[Optional[str], str]:
    """
    Analiza una respuesta en texto natural del usuario en Telegram.
    Soporta: «aprobar», «regenerar escena», «rechazar», «sí», «no», «ok», «no cuadra», «rehacer», etc.
    Devuelve (accion ['approve'|'reject'|'redo'|None], feedback).
    """
    clean = text.strip()
    lower = clean.lower()

    # 1. Patrones de rehacer / regenerar escena
    redo_patterns = [
        r"^(regenerar|regenerar escena|rehacer|repite|repetir|hazlo de nuevo|vuelve a generar|generar otro|cambiar|otra vez)\b",
        r"\b(regenerar escena|rehacer escena|rehacer|otra propuesta)\b"
    ]
    for pat in redo_patterns:
        if re.search(pat, lower):
            return "redo", clean

    # 2. Patrones de rechazo (deben evaluarse antes que aprobación para captar 'no me gusta' o 'no cuadra')
    reject_patterns = [
        r"^(no|rechazo|rechazado|rechazar|mal|descartar|descarta)\b",
        r"\b(no me gusta|no cuadra|no vale|horrible|incorrecto|no encaja)\b"
    ]
    for pat in reject_patterns:
        if re.search(pat, lower):
            return "reject", clean

    # 3. Patrones de aprobación positiva
    approve_patterns = [
        r"^(s[ií]|ok|vale|apruebo|aprobado|aprobar|acepto|aceptar|dale|perfecto|adelante|dispara)\b",
        r"(?<!no\s)\b(lo apruebo|me gusta|está genial|queda aprobado|aprobar escena)\b"
    ]
    for pat in approve_patterns:
        if re.search(pat, lower):
            return "approve", clean

    return None, clean

def process_telegram_update(update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Procesa una única actualización de Telegram (Callback Query o Mensaje de Texto)."""
    token, _, _ = get_telegram_config()

    # Caso 1: Botón interactivo presionado (Callback Query)
    if "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb.get("id")
        data = cb.get("data", "")
        parts = data.split(":")

        # Caso 1A: Botón de clip de escena -> {action}:s:{project_id}:{chapter_id}:{scene_id}
        if len(parts) >= 5 and parts[1] == "s":
            action, _, project_id, chapter_id, scene_id_str = parts[0], parts[1], parts[2], parts[3], parts[4]
            try:
                label = "Aprobar" if action == "appr" else ("Regenerar escena" if action == "redo" else "Rechazar")
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Escena #{scene_id_str}: {label}"})
                res = apply_scene_approval_decision(
                    project_id=project_id,
                    chapter_id=chapter_id,
                    scene_id=int(scene_id_str),
                    action=action,
                    notify_telegram=True
                )
                return {
                    "type": "callback_query",
                    "item_type": "scene",
                    "action": action,
                    "project_id": project_id,
                    "chapter_id": chapter_id,
                    "scene_id": int(scene_id_str),
                    "result": res
                }
            except Exception as e:
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Error: {e}"})
                return {"type": "callback_query", "error": str(e)}

        # Caso 1B: Aprobar todas las escenas de un capítulo -> appr_all:ch:{project_id}:{chapter_id}
        if len(parts) >= 4 and parts[0] == "appr_all" and parts[1] == "ch":
            project_id, chapter_id = parts[2], parts[3]
            try:
                chapter = get_project_chapter(project_id, chapter_id)
                for idx, sc in enumerate(chapter.get("scenes", [])):
                    sc_id = int(sc.get("id") or (idx + 1))
                    apply_scene_approval_decision(project_id, chapter_id, sc_id, "approve", notify_telegram=False)
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "¡Todas las escenas aprobadas!"})
                _, chat_id, enabled = get_telegram_config()
                if enabled:
                    send_telegram_api(
                        "sendMessage",
                        {
                            "chat_id": chat_id,
                            "text": f"✅ <b>¡TODAS LAS ESCENAS APROBADAS!</b>\nEl capítulo <b>{chapter.get('titulo', chapter_id)}</b> está listo para el ensamblado final.",
                            "parse_mode": "HTML"
                        }
                    )
                return {
                    "type": "callback_query",
                    "item_type": "chapter",
                    "action": "approve_all",
                    "project_id": project_id,
                    "chapter_id": chapter_id
                }
            except Exception as e:
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Error: {e}"})
                return {"type": "callback_query", "error": str(e)}

        # Caso 1C: Personaje o escenario -> {action}:{item_type}:{project_id}:{item_id}
        if len(parts) >= 4:
            action, item_type, project_id, item_id = parts[0], parts[1], parts[2], parts[3]
            try:
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Acción '{action}' recibida"})
                res = apply_approval_decision(project_id, item_type, item_id, action, notify_telegram=True)
                return {"type": "callback_query", "action": action, "item_id": item_id, "result": res}
            except Exception as e:
                send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Error: {e}"})
                return {"type": "callback_query", "error": str(e)}

    # Caso 2: Mensaje de texto recibido (Respuesta o comando)
    if "message" in update:
        msg = update["message"]
        text = msg.get("text", "")
        if not text:
            return None

        action, feedback = parse_natural_language_decision(text)
        if not action:
            return None

        # Identificar qué elemento se está respondiendo
        target = None
        reply_to = msg.get("reply_to_message")
        if reply_to:
            target = find_item_by_message_id(reply_to.get("message_id"))

        if not target:
            # Si no es un reply directo, aplicar sobre la propuesta pendiente más reciente
            target = find_latest_pending_item()

        if target:
            project_id, item_type, item_id, _ = target
            try:
                if item_type.startswith("s:"):
                    chapter_id = item_type.split(":", 1)[1]
                    res = apply_scene_approval_decision(
                        project_id=project_id,
                        chapter_id=chapter_id,
                        scene_id=int(item_id),
                        action=action,
                        feedback=feedback,
                        notify_telegram=True
                    )
                    return {
                        "type": "message_text",
                        "item_type": "scene",
                        "action": action,
                        "chapter_id": chapter_id,
                        "scene_id": int(item_id),
                        "result": res
                    }
                else:
                    res = apply_approval_decision(project_id, item_type, item_id, action, feedback=feedback, notify_telegram=True)
                    return {"type": "message_text", "action": action, "item_id": item_id, "result": res}
            except Exception as e:
                return {"type": "message_text", "error": str(e)}

    return None

def poll_telegram_updates(limit: int = 15) -> Dict[str, Any]:
    """
    Consulta activamente los mensajes y clics pendientes en Telegram y los procesa.
    Actualiza el offset para no procesar el mismo mensaje dos veces.
    """
    global _LAST_UPDATE_OFFSET
    token, _, enabled = get_telegram_config()
    if not enabled:
        return {"ok": False, "error": "Telegram no habilitado"}

    url_params = {"limit": limit}
    if _LAST_UPDATE_OFFSET > 0:
        url_params["offset"] = _LAST_UPDATE_OFFSET + 1

    resp = send_telegram_api("getUpdates", url_params)
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error", "Error al obtener updates de Telegram")}

    updates = resp.get("result", [])
    processed_list = []

    for up in updates:
        up_id = up.get("update_id")
        if up_id and up_id > _LAST_UPDATE_OFFSET:
            _LAST_UPDATE_OFFSET = up_id

        res = process_telegram_update(up)
        if res:
            processed_list.append(res)

    return {
        "ok": True,
        "updates_count": len(updates),
        "processed_count": len(processed_list),
        "processed": processed_list,
        "last_offset": _LAST_UPDATE_OFFSET
    }
