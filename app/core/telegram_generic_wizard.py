import json
import threading
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, ImageDraw, ImageFont

from app.core.project_manager import (
    analyze_book_with_ai,
    audit_character_prompts_coherence,
    audit_environment_prompts_coherence,
    generate_character_4_views,
    generate_character_portrait_proposals,
    generate_environment_proposals,
    get_project,
    get_project_document_content,
    get_project_folder,
    list_all_projects,
    save_or_update_project,
    select_character_portrait_proposal,
    select_environment_proposal,
    slugify,
    sync_project_style,
    upload_project_document,
)
from app.core.telegram_approvals import get_telegram_config, send_telegram_api
from app.core.tts_engine import list_voices, synthesize_speech

STATIC_MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
STATIC_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
WIZARD_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "proyectos" / "telegram_wizard_state.json"


def _load_wizard_state() -> Dict[str, Any]:
    if not WIZARD_STATE_FILE.exists():
        return {}
    try:
        return json.loads(WIZARD_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_wizard_state(state_data: Dict[str, Any]) -> None:
    WIZARD_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WIZARD_STATE_FILE.write_text(json.dumps(state_data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_chat_state(chat_id: Any) -> Dict[str, Any]:
    return _load_wizard_state().get(str(chat_id), {})


def _set_chat_state(chat_id: Any, patch: Dict[str, Any]) -> None:
    all_s = _load_wizard_state()
    cur = all_s.get(str(chat_id), {})
    cur.update(patch)
    all_s[str(chat_id)] = cur
    _save_wizard_state(all_s)


STYLE_OPTIONS = [
    ("watercolor", "🎨 Acuarela Poética"),
    ("ghibli", "🌿 Studio Ghibli"),
    ("cinematic", "🎬 Cinematográfico"),
    ("pixar", "🧸 Pixar / 3D"),
    ("storybook", "📖 Cuento Clásico"),
    ("vintage", "📜 Vintage Sepia"),
]


def _load_font(size: int = 36) -> ImageFont.ImageFont:
    for font_name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _resolve_media_path(url_or_path: str, project_id: str) -> Optional[Path]:
    if not url_or_path:
        return None
    clean = url_or_path.split("?")[0]
    if clean.startswith("/static/media/"):
        p = STATIC_MEDIA_DIR / clean.replace("/static/media/", "", 1)
        return p if p.exists() else None
    if clean.startswith(f"/proyectos_data/{project_id}/"):
        rel = clean.replace(f"/proyectos_data/{project_id}/", "", 1)
        p = get_project_folder(project_id) / rel
        return p if p.exists() else None
    p = Path(clean)
    return p if p.exists() else None


def _build_labeled_collage(
    items: List[tuple],
    out_path: Path,
    cols: int = 3,
    cell_w: int = 360,
    cell_h: int = 640,
) -> Path:
    """Genera un collage limpio con etiquetas grandes (1..6 o nombres de vistas) para móvil."""
    rows = (len(items) + cols - 1) // cols
    gap = 12
    canvas_w = cols * cell_w + (cols + 1) * gap
    canvas_h = rows * cell_h + (rows + 1) * gap
    canvas = Image.new("RGB", (canvas_w, canvas_h), (15, 23, 42))
    draw = ImageDraw.Draw(canvas)
    font = _load_font(34)

    for idx, (label, img_path) in enumerate(items):
        r = idx // cols
        c = idx % cols
        x0 = gap + c * (cell_w + gap)
        y0 = gap + r * (cell_h + gap)
        if img_path and Path(img_path).exists():
            try:
                with Image.open(img_path) as im:
                    im = im.convert("RGB")
                    im.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
                    bg = Image.new("RGB", (cell_w, cell_h), (20, 29, 49))
                    ox = (cell_w - im.width) // 2
                    oy = (cell_h - im.height) // 2
                    bg.paste(im, (ox, oy))
                    canvas.paste(bg, (x0, y0))
            except Exception:
                draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=(30, 41, 59))
        else:
            draw.rectangle([x0, y0, x0 + cell_w, y0 + cell_h], fill=(30, 41, 59))

        badge_w = max(56, 22 + len(str(label)) * 20)
        badge_h = 52
        draw.rounded_rectangle(
            [x0 + 10, y0 + 10, x0 + 10 + badge_w, y0 + 10 + badge_h],
            radius=12,
            fill=(37, 99, 235),
        )
        draw.text((x0 + 24, y0 + 18), str(label), fill=(255, 255, 255), font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="JPEG", quality=88)
    return out_path


def _save_wizard_batch(project_id: str, kind: str, item_id: str, item_name: str, proposals: List[Dict[str, Any]]) -> str:
    folder = get_project_folder(project_id)
    meta_file = folder / "proyecto.json"
    with open(meta_file, "r", encoding="utf-8") as f:
        proj = json.load(f)
    batches = proj.setdefault("telegram_wizard_batches", {})
    # Mantener solo los últimos 15 lotes para no inflar el JSON
    if len(batches) > 15:
        for old_k in list(batches.keys())[:-10]:
            batches.pop(old_k, None)
    token = uuid.uuid4().hex[:8]
    batches[token] = {
        "kind": kind,
        "item_id": item_id,
        "item_name": item_name,
        "proposals": proposals,
        "created_at": int(time.time()),
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(proj, f, ensure_ascii=False, indent=2)
    return token


def _find_wizard_batch(token: str) -> Optional[tuple]:
    for p in list_all_projects():
        pid = p.get("id")
        if not pid:
            continue
        try:
            proj = get_project(pid)
            batch = (proj.get("telegram_wizard_batches") or {}).get(token)
            if batch:
                return pid, proj, batch
        except Exception:
            continue
    return None


def register_bot_commands() -> Dict[str, Any]:
    """Registra los comandos en el botón Menú de Telegram para tenerlos siempre a mano."""
    commands = [
        {"command": "menu", "description": "Elegir con qué trabajar (VideoStudio AI u otros)"},
        {"command": "videostudio", "description": "Abrir VideoStudio AI (Edición de Vídeo)"},
        {"command": "nuevo", "description": "Subir libro nuevo (PDF, DOCX o TXT)"},
        {"command": "principito", "description": "Abrir proyecto El Principito"},
    ]
    return send_telegram_api("setMyCommands", {"commands": json.dumps(commands)})


def send_main_workspace_menu(chat_id: Any) -> None:
    text = (
        "🤖 <b>¿Con qué quieres trabajar ahora?</b>\n\n"
        "Pulsa un botón para elegir el área de trabajo:"
    )
    rows = [
        [{"text": "🎬 VideoStudio AI (Edición de Vídeo)", "callback_data": "gw:projects"}],
        [{"text": "💼 Otra cosa / Gestión General", "callback_data": "gw:other"}],
    ]
    send_telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": rows}),
        },
    )


def send_project_selector(chat_id: Any) -> None:
    projects = list_all_projects()
    rows = [[{"text": "📄 Nuevo Proyecto (Subir Libro)", "callback_data": "gw:new"}]]
    for p in projects[:10]:
        pid = p.get("id")
        title = p.get("titulo") or pid
        rows.append([{"text": f"📖 {title}", "callback_data": f"gw:dash:{pid}"[:64]}])

    text = (
        "🎬 <b>VideoStudio AI · Capa Genérica Móvil</b>\n\n"
        "Pulsa <b>📄 Nuevo Proyecto (Subir Libro)</b> para empezar subiendo un documento base (PDF, DOCX o TXT), "
        "ponerle título y analizarlo con IA, o elige un proyecto existente:"
    )
    send_telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": rows}),
        },
    )


def _send_fase1_ready_card(chat_id: Any, project_id: str, doc_name: str = "", word_count: int = 0) -> None:
    proj = get_project(project_id)
    title = proj.get("titulo") or project_id
    doc_line = f"📄 <b>Documento base:</b> <code>{doc_name}</code>" if doc_name else f"📁 <b>Proyecto:</b> <code>{project_id}</code>"
    if word_count:
        doc_line += f" ({word_count:,} palabras)".replace(",", ".")

    text = (
        f"📘 <b>Fase 1 · Documento Base Listo</b>\n\n"
        f"{doc_line}\n"
        f"📝 <b>Título del proyecto:</b> {title}\n\n"
        f"Si quieres cambiar el título pulsa <b>✏️ Cambiar Título</b>, y cuando esté listo pulsa <b>🔮 Analizar con IA</b>."
    )
    kb = [
        [{"text": "✏️ Cambiar Título", "callback_data": f"gw:asktitle:{project_id}"[:64]}],
        [{"text": "🔮 Analizar con IA", "callback_data": f"gw:analyze:{project_id}"[:64]}],
        [{"text": "📋 Proyectos", "callback_data": "gw:projects"}],
    ]
    send_telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": kb}),
        },
    )


def send_generic_dashboard(chat_id: Any, project_id: str) -> None:
    proj = get_project(project_id)
    title = proj.get("titulo") or project_id
    style = proj.get("estilo_visual") or "watercolor"
    chars = proj.get("personajes", [])
    envs = proj.get("escenarios", [])
    voice = proj.get("voz_defecto") or (proj.get("perfil_narrador") or {}).get("voz_recomendada") or "sin elegir"

    char_lines = []
    pending_chars = []
    for c in chars:
        st = c.get("estado_aprobacion") or ("aprobado" if c.get("imagen_url") else "pendiente")
        icon = "✅" if st == "aprobado" else ("❌" if st == "rechazado" else ("⚠️" if st == "en_revision" else "⏳"))
        v4 = " (4 vistas ✓)" if c.get("vistas_4") and len(c.get("vistas_4", {})) >= 4 else ""
        char_lines.append(f"  {icon} {c.get('nombre', c.get('id'))}{v4}")
        if st != "aprobado":
            pending_chars.append(c)

    env_lines = []
    pending_envs = []
    for e in envs:
        st = e.get("estado_aprobacion") or ("aprobado" if e.get("imagen_url") else "pendiente")
        icon = "✅" if st == "aprobado" else ("❌" if st == "rechazado" else ("⚠️" if st == "en_revision" else "⏳"))
        env_lines.append(f"  {icon} {e.get('nombre', e.get('id'))}")
        if st != "aprobado":
            pending_envs.append(e)

    text = (
        f"📖 <b>{title}</b>\n"
        f"🎨 <b>Estilo:</b> <code>{style}</code>\n"
        f"🎙️ <b>Voz narrador:</b> <code>{voice}</code>\n\n"
        f"<b>👥 Personajes ({len(chars)}):</b>\n" + ("\n".join(char_lines) or "  (ninguno)") + "\n\n"
        f"<b>🏛️ Escenarios ({len(envs)}):</b>\n" + ("\n".join(env_lines) or "  (ninguno)")
    )

    keyboard: List[List[Dict[str, str]]] = [
        [{"text": "🎨 Cambiar Estilo Visual", "callback_data": f"gw:styles:{project_id}"[:64]}]
    ]

    for c in pending_chars[:3]:
        cid = c.get("id")
        cname = c.get("nombre", cid)
        keyboard.append([{"text": f"🎨 6 propuestas: {cname}", "callback_data": f"gw:gc:{project_id}:{cid}"[:64]}])

    for e in pending_envs[:3]:
        eid = e.get("id")
        ename = e.get("nombre", eid)
        keyboard.append([{"text": f"🏛️ 6 propuestas: {ename}", "callback_data": f"gw:ge:{project_id}:{eid}"[:64]}])

    keyboard.append([
        {"text": "👥 Elegir Personaje", "callback_data": f"gw:lc:{project_id}"[:64]},
        {"text": "🏛️ Elegir Escenario", "callback_data": f"gw:le:{project_id}"[:64]},
    ])
    keyboard.append([
        {"text": "🔍 Revisar Coherencia", "callback_data": f"gw:aud:{project_id}"[:64]},
        {"text": "🎙️ Elegir Voz", "callback_data": f"gw:v:{project_id}"[:64]},
    ])
    keyboard.append([{"text": "📚 Cambiar de Proyecto", "callback_data": "gw:projects"}])

    send_telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": json.dumps({"inline_keyboard": keyboard}),
        },
    )


def _send_proposals_for_character(chat_id: Any, project_id: str, char_id: str) -> None:
    try:
        proj = get_project(project_id)
        char = next((c for c in proj.get("personajes", []) if c.get("id") == char_id), None)
        if not char:
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Personaje '{char_id}' no encontrado."})
            return

        cname = char.get("nombre", char_id)
        send_telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": f"🎨 Generando 6 propuestas para <b>{cname}</b>...", "parse_mode": "HTML"},
        )
        res = generate_character_portrait_proposals(project_id=project_id, character_id=char_id, count=6)
        proposals = res.get("proposals", [])
        if not proposals:
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ No se pudieron generar propuestas para {cname}."})
            return

        collage_items = [
            (str(i + 1), _resolve_media_path(p.get("imagen_url", ""), project_id))
            for i, p in enumerate(proposals[:6])
        ]
        collage_path = STATIC_MEDIA_DIR / f"tg_collage_{project_id}_{char_id}_{int(time.time())}.jpg"
        _build_labeled_collage(collage_items, collage_path, cols=3)
        token = _save_wizard_batch(project_id, "c", char_id, cname, proposals)

        kb = [
            [
                {"text": "1️⃣", "callback_data": f"gw:p:{token}:0"},
                {"text": "2️⃣", "callback_data": f"gw:p:{token}:1"},
                {"text": "3️⃣", "callback_data": f"gw:p:{token}:2"},
            ],
            [
                {"text": "4️⃣", "callback_data": f"gw:p:{token}:3"},
                {"text": "5️⃣", "callback_data": f"gw:p:{token}:4"},
                {"text": "6️⃣", "callback_data": f"gw:p:{token}:5"},
            ],
            [
                {"text": "🔄 Otras 6", "callback_data": f"gw:gc:{project_id}:{char_id}"[:64]},
                {"text": "📋 Panel", "callback_data": f"gw:dash:{project_id}"[:64]},
            ],
        ]
        send_telegram_api(
            "sendPhoto",
            {
                "chat_id": chat_id,
                "caption": f"👤 <b>{cname}</b> — Elige una de las 6 propuestas (al elegirla se aprobará y generará sus 4 vistas):",
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": kb}),
            },
            files={"photo": collage_path},
        )
    except Exception as e:
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error generando propuestas: {e}"})


def _send_proposals_for_environment(chat_id: Any, project_id: str, env_id: str) -> None:
    try:
        proj = get_project(project_id)
        env = next((e for e in proj.get("escenarios", []) if e.get("id") == env_id), None)
        if not env:
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Escenario '{env_id}' no encontrado."})
            return

        ename = env.get("nombre", env_id)
        send_telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": f"🏛️ Generando 6 propuestas para <b>{ename}</b>...", "parse_mode": "HTML"},
        )
        res = generate_environment_proposals(project_id=project_id, environment_id=env_id, count=6)
        proposals = res.get("proposals", [])
        if not proposals:
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ No se pudieron generar propuestas para {ename}."})
            return

        collage_items = [
            (str(i + 1), _resolve_media_path(p.get("imagen_url", ""), project_id))
            for i, p in enumerate(proposals[:6])
        ]
        collage_path = STATIC_MEDIA_DIR / f"tg_collage_{project_id}_{env_id}_{int(time.time())}.jpg"
        _build_labeled_collage(collage_items, collage_path, cols=3)
        token = _save_wizard_batch(project_id, "e", env_id, ename, proposals)

        kb = [
            [
                {"text": "1️⃣", "callback_data": f"gw:p:{token}:0"},
                {"text": "2️⃣", "callback_data": f"gw:p:{token}:1"},
                {"text": "3️⃣", "callback_data": f"gw:p:{token}:2"},
            ],
            [
                {"text": "4️⃣", "callback_data": f"gw:p:{token}:3"},
                {"text": "5️⃣", "callback_data": f"gw:p:{token}:4"},
                {"text": "6️⃣", "callback_data": f"gw:p:{token}:5"},
            ],
            [
                {"text": "🔄 Otras 6", "callback_data": f"gw:ge:{project_id}:{env_id}"[:64]},
                {"text": "📋 Panel", "callback_data": f"gw:dash:{project_id}"[:64]},
            ],
        ]
        send_telegram_api(
            "sendPhoto",
            {
                "chat_id": chat_id,
                "caption": f"🏛️ <b>{ename}</b> — Elige una de las 6 propuestas para aprobar este escenario:",
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": kb}),
            },
            files={"photo": collage_path},
        )
    except Exception as e:
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error generando propuestas de escenario: {e}"})


def _apply_picked_proposal(chat_id: Any, token: str, idx: int) -> None:
    found = _find_wizard_batch(token)
    if not found:
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": "⚠️ Esa propuesta ya expiró. Abre el panel de nuevo con /generico."})
        return

    project_id, proj, batch = found
    proposals = batch.get("proposals", [])
    if idx < 0 or idx >= len(proposals):
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": "❌ Índice de propuesta inválido."})
        return

    chosen = proposals[idx]
    kind = batch["kind"]
    item_id = batch["item_id"]
    item_name = batch["item_name"]

    try:
        if kind == "c":
            select_character_portrait_proposal(
                project_id=project_id,
                character_id=item_id,
                imagen_url=chosen["imagen_url"],
                seed_consistencia=chosen.get("seed"),
            )
            proj_upd = get_project(project_id)
            for c in proj_upd.get("personajes", []):
                if c.get("id") == item_id:
                    c["estado_aprobacion"] = "aprobado"
                    c["motivo_rechazo"] = ""
                    break
            save_or_update_project(proj_upd)

            send_telegram_api(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": f"✅ <b>{item_name}</b> aprobado (opción {idx + 1}, Seed <code>{chosen.get('seed')}</code>).\n🔄 Generando sus 4 vistas (Detalle, Frontal, Trasera, Perfil)...",
                    "parse_mode": "HTML",
                },
            )
            res4 = generate_character_4_views(project_id=project_id, character_id=item_id)
            v4 = res4.get("vistas_4", {})
            v_items = [
                ("Detalle", _resolve_media_path((v4.get("detalle") or {}).get("imagen_url", ""), project_id)),
                ("Frontal", _resolve_media_path((v4.get("frontal") or {}).get("imagen_url", ""), project_id)),
                ("Trasera", _resolve_media_path((v4.get("trasera") or {}).get("imagen_url", ""), project_id)),
                ("Perfil", _resolve_media_path((v4.get("perfil") or {}).get("imagen_url", ""), project_id)),
            ]
            v_collage = STATIC_MEDIA_DIR / f"tg_4views_{project_id}_{item_id}_{int(time.time())}.jpg"
            _build_labeled_collage(v_items, v_collage, cols=2)
            send_telegram_api(
                "sendPhoto",
                {
                    "chat_id": chat_id,
                    "caption": f"🧩 <b>4 vistas generadas para {item_name}</b>",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(
                        {
                            "inline_keyboard": [
                                [{"text": "🔄 Regenerar 4 vistas", "callback_data": f"gw:4v:{project_id}:{item_id}"[:64]}],
                                [{"text": "📋 Continuar en el Panel", "callback_data": f"gw:dash:{project_id}"[:64]}],
                            ]
                        }
                    ),
                },
                files={"photo": v_collage},
            )
        else:
            select_environment_proposal(
                project_id=project_id,
                environment_id=item_id,
                imagen_url=chosen["imagen_url"],
                seed_consistencia=chosen.get("seed"),
            )
            proj_upd = get_project(project_id)
            for e in proj_upd.get("escenarios", []):
                if e.get("id") == item_id:
                    e["estado_aprobacion"] = "aprobado"
                    e["motivo_rechazo"] = ""
                    break
            save_or_update_project(proj_upd)

            send_telegram_api(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": f"✅ Escenario <b>{item_name}</b> aprobado (opción {idx + 1}, Seed <code>{chosen.get('seed')}</code>).",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(
                        {"inline_keyboard": [[{"text": "📋 Continuar en el Panel", "callback_data": f"gw:dash:{project_id}"[:64]}]]}
                    ),
                },
            )
    except Exception as e:
        send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error guardando selección: {e}"})


def handle_wizard_callback(cb_id: str, chat_id: Any, data: str) -> Dict[str, Any]:
    parts = data.split(":")
    cmd = parts[1] if len(parts) > 1 else ""

    if cmd == "menu":
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Menú principal"})
        send_main_workspace_menu(chat_id)
        return {"type": "wizard", "cmd": cmd}

    if cmd == "other":
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Otras herramientas"})
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": (
                    "💼 <b>Otras áreas de trabajo</b>\n\n"
                    "Este bot está conectado ahora mismo a <b>VideoStudio AI (Edición de Vídeo)</b>.\n"
                    "Si quieres tener un bot independiente solo para VideoStudio AI (y dejar el otro libre para tus tareas generales), "
                    "solo tienes que crear uno en <b>@BotFather</b> y poner su token en el <code>.env</code> de VideoStudio AI."
                ),
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": [[{"text": "⬅️ Volver al Menú Principal", "callback_data": "gw:menu"}]]}),
            },
        )
        return {"type": "wizard", "cmd": cmd}

    if cmd == "projects":
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Cargando proyectos..."})
        send_project_selector(chat_id)
        return {"type": "wizard", "cmd": cmd}

    if cmd == "new":
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Envía el documento"})
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "📄 <b>Paso 1 · Subir documento base</b>\n\nEnvíame ahora el archivo del libro (<code>.pdf</code>, <code>.docx</code> o <code>.txt</code>) como documento en este chat.",
                "parse_mode": "HTML",
            },
        )
        return {"type": "wizard", "cmd": cmd}

    if cmd == "asktitle" and len(parts) >= 3:
        pid = parts[2]
        _set_chat_state(chat_id, {"awaiting_title_for": pid})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Escribe el título"})
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "✏️ <b>Escríbeme ahora el título</b> que quieres ponerle al proyecto:",
                "parse_mode": "HTML",
            },
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "analyze" and len(parts) >= 3:
        pid = parts[2]
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Analizando con IA..."})
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "🔮 <b>Analizando el documento con IA...</b>\nExtrayendo universo, personajes, escenarios y perfil del narrador.",
                "parse_mode": "HTML",
            },
        )

        def _run_analysis():
            try:
                doc_data = get_project_document_content(pid)
                text_extracted = doc_data.get("texto") or ""
                if not text_extracted.strip():
                    proj_cur = get_project(pid)
                    text_extracted = f"{proj_cur.get('titulo', '')}\n{proj_cur.get('descripcion', '')}"
                analysis = analyze_book_with_ai(text_extracted, project_id=pid)
                proj = get_project(pid)
                for k in ("descripcion", "audiencia", "ambiente", "personajes_recurrentes_texto", "personajes", "escenarios", "perfil_narrador"):
                    if analysis.get(k):
                        proj[k] = analysis[k]
                save_or_update_project(proj)
                send_telegram_api(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": f"✅ <b>Análisis IA completado</b> para <b>{proj.get('titulo', pid)}</b>: {len(proj.get('personajes', []))} personajes y {len(proj.get('escenarios', []))} escenarios detectados.",
                        "parse_mode": "HTML",
                    },
                )
                send_generic_dashboard(chat_id, pid)
            except Exception as e:
                send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error en análisis IA: {e}"})

        threading.Thread(target=_run_analysis, daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "dash" and len(parts) >= 3:
        pid = parts[2]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Abriendo panel..."})
        send_generic_dashboard(chat_id, pid)
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "styles" and len(parts) >= 3:
        pid = parts[2]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Elige estilo"})
        kb = [[{"text": label, "callback_data": f"gw:setst:{pid}:{key}"[:64]}] for key, label in STYLE_OPTIONS]
        kb.append([{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}])
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "🎨 <b>Elige el Estilo Visual del proyecto:</b>\nAl seleccionarlo se actualizarán los prompts de personajes y escenarios.",
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": kb}),
            },
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "setst" and len(parts) >= 4:
        pid, skey = parts[2], parts[3]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Estilo {skey} aplicado"})
        threading.Thread(
            target=lambda: (
                sync_project_style(project_id=pid, new_style=skey, regenerate_all=False),
                send_generic_dashboard(chat_id, pid),
            ),
            daemon=True,
        ).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "style": skey}

    if cmd == "lc" and len(parts) >= 3:
        pid = parts[2]
        proj = get_project(pid)
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Elige personaje"})
        kb = [
            [{"text": f"🎨 {c.get('nombre', c.get('id'))}", "callback_data": f"gw:gc:{pid}:{c.get('id')}"[:64]}]
            for c in proj.get("personajes", [])
        ]
        kb.append([{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}])
        send_telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": "👥 <b>¿Para qué personaje quieres generar 6 propuestas?</b>", "parse_mode": "HTML", "reply_markup": json.dumps({"inline_keyboard": kb})},
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "le" and len(parts) >= 3:
        pid = parts[2]
        proj = get_project(pid)
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Elige escenario"})
        kb = [
            [{"text": f"🏛️ {e.get('nombre', e.get('id'))}", "callback_data": f"gw:ge:{pid}:{e.get('id')}"[:64]}]
            for e in proj.get("escenarios", [])
        ]
        kb.append([{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}])
        send_telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": "🏛️ <b>¿Para qué escenario quieres generar 6 propuestas?</b>", "parse_mode": "HTML", "reply_markup": json.dumps({"inline_keyboard": kb})},
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "gc" and len(parts) >= 4:
        pid, cid = parts[2], parts[3]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Generando 6 propuestas..."})
        threading.Thread(target=_send_proposals_for_character, args=(chat_id, pid, cid), daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "character_id": cid}

    if cmd == "ge" and len(parts) >= 4:
        pid, eid = parts[2], parts[3]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Generando 6 propuestas..."})
        threading.Thread(target=_send_proposals_for_environment, args=(chat_id, pid, eid), daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "environment_id": eid}

    if cmd == "p" and len(parts) >= 4:
        token, idx = parts[2], int(parts[3])
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Opción {idx + 1} seleccionada"})
        threading.Thread(target=_apply_picked_proposal, args=(chat_id, token, idx), daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "token": token, "index": idx}

    if cmd == "4v" and len(parts) >= 4:
        pid, cid = parts[2], parts[3]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Regenerando 4 vistas..."})

        def _regen_4v():
            res4 = generate_character_4_views(project_id=pid, character_id=cid)
            v4 = res4.get("vistas_4", {})
            v_items = [
                ("Detalle", _resolve_media_path((v4.get("detalle") or {}).get("imagen_url", ""), pid)),
                ("Frontal", _resolve_media_path((v4.get("frontal") or {}).get("imagen_url", ""), pid)),
                ("Trasera", _resolve_media_path((v4.get("trasera") or {}).get("imagen_url", ""), pid)),
                ("Perfil", _resolve_media_path((v4.get("perfil") or {}).get("imagen_url", ""), pid)),
            ]
            v_collage = STATIC_MEDIA_DIR / f"tg_4views_{pid}_{cid}_{int(time.time())}.jpg"
            _build_labeled_collage(v_items, v_collage, cols=2)
            send_telegram_api(
                "sendPhoto",
                {
                    "chat_id": chat_id,
                    "caption": f"🧩 <b>4 vistas actualizadas ({cid})</b>",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps({"inline_keyboard": [[{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}]]}),
                },
                files={"photo": v_collage},
            )

        threading.Thread(target=_regen_4v, daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "character_id": cid}

    if cmd == "aud" and len(parts) >= 3:
        pid = parts[2]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Revisando coherencia..."})
        ac = audit_character_prompts_coherence(pid)
        ae = audit_environment_prompts_coherence(pid)
        msg = (
            f"🔍 <b>Revisión de Coherencia ({pid})</b>\n"
            f"👥 Personajes: {ac['approved']}/{ac['total']} coherentes\n"
            f"🏛️ Escenarios: {ae['approved']}/{ae['total']} coherentes"
        )
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": [[{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}]]}),
            },
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "v" and len(parts) >= 3:
        pid = parts[2]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Voces en español"})
        voices = [v for v in list_voices() if v.get("id") != "gtts_es"][:8]
        kb = [[{"text": f"🎙️ {v['name']}", "callback_data": f"gw:tv:{pid}:{v['id']}"[:64]}] for v in voices]
        kb.append([{"text": "📋 Volver al panel", "callback_data": f"gw:dash:{pid}"[:64]}])
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "🎙️ <b>Elige una voz en español de España para escuchar su muestra:</b>",
                "parse_mode": "HTML",
                "reply_markup": json.dumps({"inline_keyboard": kb}),
            },
        )
        return {"type": "wizard", "cmd": cmd, "project_id": pid}

    if cmd == "tv" and len(parts) >= 4:
        pid, vid = parts[2], parts[3]
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Generando audio de prueba..."})

        def _send_voice_sample():
            proj = get_project(pid)
            sample = (proj.get("perfil_narrador") or {}).get("texto_muestra") or "Érase una vez un pequeño príncipe que vivía en un asteroide."
            tts = synthesize_speech(sample[:320], voice_key=vid)
            fpath = Path(tts["file_path"])
            send_telegram_api(
                "sendAudio",
                {
                    "chat_id": chat_id,
                    "caption": f"🎙️ Muestra de <code>{vid}</code>",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps(
                        {
                            "inline_keyboard": [
                                [{"text": "✅ Elegir esta voz", "callback_data": f"gw:sv:{pid}:{vid}"[:64]}],
                                [{"text": "🎙️ Probar otra", "callback_data": f"gw:v:{pid}"[:64]}],
                            ]
                        }
                    ),
                },
                files={"audio": fpath},
            )

        threading.Thread(target=_send_voice_sample, daemon=True).start()
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "voice_id": vid}

    if cmd == "sv" and len(parts) >= 4:
        pid, vid = parts[2], parts[3]
        proj = get_project(pid)
        proj["voz_defecto"] = vid
        if proj.get("perfil_narrador"):
            proj["perfil_narrador"]["voz_recomendada"] = vid
        save_or_update_project(proj)
        send_telegram_api("answerCallbackQuery", {"callback_query_id": cb_id, "text": f"Voz {vid} guardada"})
        send_generic_dashboard(chat_id, pid)
        return {"type": "wizard", "cmd": cmd, "project_id": pid, "voice_id": vid}

    return {"type": "wizard", "cmd": cmd}


def handle_wizard_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    chat_id = (msg.get("chat") or {}).get("id")
    if not chat_id:
        return None

    # 1. Subida directa de un libro PDF / DOCX / TXT por Telegram (Paso 1 de Fase 1)
    doc = msg.get("document")
    if doc:
        fname = doc.get("file_name") or "libro.pdf"
        ext = Path(fname).suffix.lower()
        if ext in (".pdf", ".docx", ".txt"):
            token, _, _ = get_telegram_config()
            if not token:
                return None
            file_id = doc.get("file_id")
            _set_chat_state(chat_id, {"awaiting_title_for": None})
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"📥 Recibido <b>{fname}</b>. Guardando documento base...", "parse_mode": "HTML"})

            def _process_uploaded_book():
                try:
                    info_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
                    with urllib.request.urlopen(info_url, timeout=15) as r:
                        info = json.loads(r.read().decode("utf-8"))
                    fpath = info["result"]["file_path"]
                    dl_url = f"https://api.telegram.org/file/bot{token}/{fpath}"
                    with urllib.request.urlopen(dl_url, timeout=30) as r:
                        file_bytes = r.read()

                    title = Path(fname).stem.replace("_", " ").strip()
                    pid = slugify(title)
                    save_or_update_project({"id": pid, "titulo": title})
                    doc_res = upload_project_document(pid, file_bytes, fname)
                    word_count = int(doc_res.get("palabras") or len((doc_res.get("texto_extraido") or "").split()))
                    _set_chat_state(chat_id, {"last_project_id": pid, "last_doc_name": fname, "last_word_count": word_count})
                    _send_fase1_ready_card(chat_id, pid, fname, word_count)
                except Exception as e:
                    send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error guardando documento: {e}"})

            threading.Thread(target=_process_uploaded_book, daemon=True).start()
            return {"type": "wizard_document", "file_name": fname}

    raw_text = (msg.get("text") or "").strip()
    if not raw_text:
        return None
    text = raw_text.lower()

    # 2. Comandos de texto (/menu, /start, /videostudio, /generico, /nuevo, /principito)
    if text in ("/menu", "/start", "menu", "hola", "1"):
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_main_workspace_menu(chat_id)
        return {"type": "wizard_command", "command": text}
    if text in ("/videostudio", "/generico", "/proyectos", "generico", "videostudio"):
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_project_selector(chat_id)
        return {"type": "wizard_command", "command": text}
    if text in ("/nuevo", "nuevo"):
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "📄 <b>Paso 1 · Subir documento base</b>\n\nEnvíame ahora el archivo del libro (<code>.pdf</code>, <code>.docx</code> o <code>.txt</code>) como documento en este chat.",
                "parse_mode": "HTML",
            },
        )
        return {"type": "wizard_command", "command": text}
    if text in ("/principito", "principito"):
        _set_chat_state(chat_id, {"awaiting_title_for": None})
        send_generic_dashboard(chat_id, "el_principito")
        return {"type": "wizard_command", "command": text, "project_id": "el_principito"}

    # 3. Si estamos esperando el título del proyecto recién subido
    chat_state = _get_chat_state(chat_id)
    awaiting_pid = chat_state.get("awaiting_title_for")
    if awaiting_pid and not raw_text.startswith("/"):
        try:
            proj = get_project(awaiting_pid)
            proj["titulo"] = raw_text
            save_or_update_project(proj)
            _set_chat_state(chat_id, {"awaiting_title_for": None})
            _send_fase1_ready_card(
                chat_id,
                awaiting_pid,
                chat_state.get("last_doc_name", ""),
                int(chat_state.get("last_word_count") or 0),
            )
            return {"type": "wizard_set_title", "project_id": awaiting_pid, "titulo": raw_text}
        except Exception as e:
            _set_chat_state(chat_id, {"awaiting_title_for": None})
            send_telegram_api("sendMessage", {"chat_id": chat_id, "text": f"❌ Error actualizando título: {e}"})
            return {"type": "wizard_set_title_error", "error": str(e)}

    return None
