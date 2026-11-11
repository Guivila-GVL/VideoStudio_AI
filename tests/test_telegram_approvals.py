import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.core.project_manager import (
    get_project,
    save_or_update_project,
    get_project_chapter,
    save_project_chapter
)
from app.core.telegram_approvals import (
    get_telegram_config,
    parse_natural_language_decision,
    apply_approval_decision,
    apply_scene_approval_decision,
    process_telegram_update,
    send_character_approval,
    send_environment_approval,
    send_scene_clip_approval,
    send_chapter_clips_for_approval,
    trigger_n8n_clip_approval_webhook
)

def test_telegram_approvals():
    client = TestClient(app)
    print("\n========================================================")
    print("TEST: Aprobación de Personajes y Escenarios vía Telegram")
    print("========================================================")

    # 1. Configuración de Telegram
    print("\n[1] Verificando configuración y credenciales de Telegram...")
    token, chat_id, enabled = get_telegram_config()
    assert token and len(token) > 20, "El token de Telegram debe estar configurado"
    assert chat_id, "El chat_id de Telegram debe estar configurado"
    assert enabled is True, "Telegram Approvals debe estar habilitado"
    print(f"   -> Bot Token: {token[:8]}...{token[-4:]} | Chat ID: {chat_id} | Habilitado: {enabled}")

    # 2. Endpoint /api/telegram/status
    print("\n[2] Comprobando GET /api/telegram/status...")
    res = client.get("/api/telegram/status")
    assert res.status_code == 200
    st_data = res.json()
    assert st_data["bot_configured"] is True
    assert st_data["enabled"] is True
    print(f"   -> Status OK: {st_data}")

    # 3. Parser de lenguaje natural
    print("\n[3] Comprobando parser de lenguaje natural («aprobar», «rechazar», «sí», «no», «no cuadra»)...")
    for text, expected in [
        ("aprobar", "approve"),
        ("aprobado", "approve"),
        ("sí", "approve"),
        ("si", "approve"),
        ("ok", "approve"),
        ("rechazar", "reject"),
        ("no", "reject"),
        ("no me gusta porque el estilo no cuadra", "reject"),
        ("rehacer", "redo"),
        ("repite la propuesta porque no cuadra", "redo")
    ]:
        act, _ = parse_natural_language_decision(text)
        assert act == expected, f"Fallo al parsear '{text}': esperado {expected}, obtenido {act}"
    print("   -> Parser NL validado correctamente para todas las variantes clave.")

    # 4. Comprobando envío o simulación de propuesta de personaje
    print("\n[4] Probando envío de propuesta de personaje a Telegram (Proyecto 'el_principito', personaje 'principito')...")
    res_char = client.post(
        "/api/projects/el_principito/characters/principito/send-telegram-approval",
        json={"auto_generate": False}
    )
    assert res_char.status_code == 200, f"Error en send-telegram-approval: {res_char.text}"
    char_data = res_char.json()
    print(f"   -> Respuesta de envío personaje: ok={char_data.get('ok')}, status={char_data.get('status')}")

    proj = get_project("el_principito")
    p_char = next(c for c in proj["personajes"] if c["id"] == "principito")
    assert p_char.get("estado_aprobacion") == "pendiente", "El estado debe pasar a 'pendiente'"

    # 5. Aplicar decisión: Rechazar personaje porque 'no cuadra'
    print("\n[5] Probando rechazo de personaje con feedback 'no cuadra'...")
    res_dec_rej = client.post(
        "/api/projects/el_principito/characters/principito/decision",
        json={
            "action": "reject",
            "feedback": "La vestimenta no cuadra con el relato",
            "notify_telegram": True
        }
    )
    assert res_dec_rej.status_code == 200
    assert res_dec_rej.json()["status"] == "rechazado"

    proj = get_project("el_principito")
    p_char = next(c for c in proj["personajes"] if c["id"] == "principito")
    assert p_char.get("estado_aprobacion") == "rechazado"
    assert "no cuadra" in p_char.get("motivo_rechazo", "").lower()
    print("   -> Personaje rechazado correctamente y registrado motivo de revisión.")

    # 6. Aplicar decisión: Aprobar personaje («aprobar» / «sí»)
    print("\n[6] Probando aprobación de personaje...")
    res_dec_appr = client.post(
        "/api/projects/el_principito/characters/principito/decision",
        json={
            "action": "approve",
            "notify_telegram": True
        }
    )
    assert res_dec_appr.status_code == 200
    assert res_dec_appr.json()["status"] == "aprobado"

    proj = get_project("el_principito")
    p_char = next(c for c in proj["personajes"] if c["id"] == "principito")
    assert p_char.get("estado_aprobacion") == "aprobado"
    assert p_char.get("aprobado_en") is not None
    print(f"   -> Personaje aprobado con éxito en fecha {p_char['aprobado_en']}.")

    # 7. Escenarios: Envío y Aprobación de Escenario
    print("\n[7] Probando propuesta y aprobación de escenario (Proyecto 'el_principito', escenario 'asteroide_b612')...")
    res_env = client.post(
        "/api/projects/el_principito/environments/asteroide_b612/send-telegram-approval",
        json={"auto_generate": False}
    )
    assert res_env.status_code == 200
    print(f"   -> Propuesta escenario enviada: ok={res_env.json().get('ok')}")

    # Rechazar escenario
    res_env_rej = client.post(
        "/api/projects/el_principito/environments/asteroide_b612/decision",
        json={
            "action": "reject",
            "feedback": "Faltan los baobabs y volcanes, no cuadra",
            "notify_telegram": True
        }
    )
    assert res_env_rej.status_code == 200
    assert res_env_rej.json()["status"] == "rechazado"

    # Aprobar escenario
    res_env_appr = client.post(
        "/api/projects/el_principito/environments/asteroide_b612/decision",
        json={
            "action": "approve",
            "notify_telegram": True
        }
    )
    assert res_env_appr.status_code == 200
    assert res_env_appr.json()["status"] == "aprobado"
    proj = get_project("el_principito")
    p_env = next(e for e in proj["escenarios"] if e["id"] == "asteroide_b612")
    assert p_env.get("estado_aprobacion") == "aprobado"
    print("   -> Escenario validado con ciclo completo (envío, rechazo, aprobación).")

    # 8. Simulación de Callback Query de Telegram (clic en botón inline)
    print("\n[8] Simulando clic en botón inline de Telegram (CallbackQuery 'appr:c:el_principito:el_zorro')...")
    mock_cb_update = {
        "update_id": 999991,
        "callback_query": {
            "id": "cb_test_123",
            "data": "appr:c:el_principito:el_zorro",
            "from": {"id": int(chat_id), "first_name": "TestUser"}
        }
    }
    res_hook = client.post("/api/telegram/webhook", json=mock_cb_update)
    assert res_hook.status_code == 200
    proj = get_project("el_principito")
    p_zorro = next(c for c in proj["personajes"] if c["id"] == "el_zorro")
    assert p_zorro.get("estado_aprobacion") == "aprobado"
    print("   -> CallbackQuery procesado con éxito: 'el_zorro' marcado como 'aprobado'.")

    # 9. Simulación de Mensaje de Texto en Telegram («no cuadra»)
    print("\n[9] Simulando respuesta de texto natural en Telegram («no, no cuadra la cara»)...")
    p_zorro["estado_aprobacion"] = "pendiente"
    p_zorro["propuesta_enviada_en"] = "2026-11-11T12:00:00"
    save_or_update_project(proj)

    mock_msg_update = {
        "update_id": 999992,
        "message": {
            "message_id": 5555,
            "chat": {"id": int(chat_id)},
            "text": "rechazar, no cuadra la expresión del rostro"
        }
    }
    res_hook_msg = client.post("/api/telegram/webhook", json=mock_msg_update)
    assert res_hook_msg.status_code == 200
    proj = get_project("el_principito")
    p_zorro = next(c for c in proj["personajes"] if c["id"] == "el_zorro")
    assert p_zorro.get("estado_aprobacion") == "rechazado"
    assert "no cuadra" in p_zorro.get("motivo_rechazo", "").lower()
    print("   -> Mensaje de texto procesado con éxito: detectado rechazo por 'no cuadra'.")

    # 10. Consulta de updates inmediata (/api/telegram/poll-now)
    print("\n[10] Probando endpoint /api/telegram/poll-now...")
    res_poll = client.post("/api/telegram/poll-now")
    assert res_poll.status_code == 200
    print(f"   -> Polling ejecutado correctamente: {res_poll.json()}")

    # 11. Envío de clip de escena pre-ensamblado por Telegram y trigger de webhook n8n
    print("\n[11] Probando envío de clip de escena pre-ensamblado por Telegram y Webhook n8n...")
    res_clip = client.post(
        "/api/projects/el_principito/chapters/cap_1/scenes/1/send-telegram-approval",
        json={"render_clip_if_missing": False, "trigger_n8n": True}
    )
    assert res_clip.status_code == 200, f"Error enviando clip: {res_clip.text}"
    clip_data = res_clip.json()
    assert clip_data["ok"] is True
    assert "✅ Aprobar" in clip_data["buttons_sent"]
    assert "🔄 Regenerar escena" in clip_data["buttons_sent"]
    assert clip_data["n8n_webhook"]["triggered"] is True
    print(f"   -> Clip escena #1 enviado. Botones: {clip_data['buttons_sent']} | Webhook n8n status: {clip_data['n8n_webhook'].get('status_code')}")

    # 12. Simulación de clic en botón inline 'Regenerar escena' de Telegram
    print("\n[12] Simulando clic en botón inline 'Regenerar escena' (CallbackQuery 'redo:s:el_principito:cap_1:1')...")
    mock_cb_redo = {
        "update_id": 999993,
        "callback_query": {
            "id": "cb_clip_redo_123",
            "data": "redo:s:el_principito:cap_1:1",
            "from": {"id": int(chat_id), "first_name": "TestUser"}
        }
    }
    res_redo = client.post("/api/telegram/webhook", json=mock_cb_redo)
    assert res_redo.status_code == 200
    ch_data = get_project_chapter("el_principito", "cap_1")
    sc_1 = next(s for s in ch_data["scenes"] if s["id"] == 1)
    assert sc_1.get("estado_aprobacion") in ("regenerando", "regenerar_solicitado")
    assert sc_1.get("regeneraciones_count", 0) >= 1
    print(f"   -> Botón 'Regenerar escena' procesado. Estado: {sc_1.get('estado_aprobacion')} | Regeneraciones: {sc_1.get('regeneraciones_count')}")

    # 13. Simulación de clic en botón inline 'Aprobar' de Telegram
    print("\n[13] Simulando clic en botón inline 'Aprobar' (CallbackQuery 'appr:s:el_principito:cap_1:1')...")
    mock_cb_appr = {
        "update_id": 999994,
        "callback_query": {
            "id": "cb_clip_appr_123",
            "data": "appr:s:el_principito:cap_1:1",
            "from": {"id": int(chat_id), "first_name": "TestUser"}
        }
    }
    res_appr = client.post("/api/telegram/webhook", json=mock_cb_appr)
    assert res_appr.status_code == 200
    ch_data = get_project_chapter("el_principito", "cap_1")
    sc_1 = next(s for s in ch_data["scenes"] if s["id"] == 1)
    assert sc_1.get("estado_aprobacion") == "aprobado"
    assert sc_1.get("aprobado_en") is not None
    print(f"   -> Botón 'Aprobar' procesado con éxito. Escena #1 marcada como 'aprobado'.")

    # 14. Integración n8n Webhook: /api/n8n/webhook/scene-decision y /api/n8n/webhook/send-clips
    print("\n[14] Probando endpoints de integración n8n (/api/n8n/webhook/scene-decision y send-clips)...")
    res_n8n_dec = client.post(
        "/api/n8n/webhook/scene-decision",
        json={
            "callback_data": "appr:s:el_principito:cap_1:2",
            "notify_telegram": True,
            "auto_regenerate_media": False
        }
    )
    assert res_n8n_dec.status_code == 200
    assert res_n8n_dec.json()["status"] == "aprobado"

    # Aprobar escena 3 mediante n8n webhook para completar el capítulo
    res_n8n_dec3 = client.post(
        "/api/n8n/webhook/scene-decision",
        json={
            "callback_data": "appr:s:el_principito:cap_1:3",
            "notify_telegram": True,
            "auto_regenerate_media": False
        }
    )
    assert res_n8n_dec3.status_code == 200
    assert res_n8n_dec3.json()["status"] == "aprobado"
    assert res_n8n_dec3.json()["all_scenes_approved"] is True
    print(f"   -> n8n Webhook procesó aprobaciones. all_scenes_approved={res_n8n_dec3.json()['all_scenes_approved']}")

    # 15. Verificación de estado pre-ensamblado y ensamblado final
    print("\n[15] Verificando estado pre-ensamblado 'aprobado_listo_ensamblar'...")
    ch_data = get_project_chapter("el_principito", "cap_1")
    assert ch_data.get("aprobacion_clips_status") == "aprobado_listo_ensamblar"
    print(f"   -> Capítulo 'cap_1' listo para ensamblado final: status='{ch_data.get('aprobacion_clips_status')}'")

    print("\n========================================================")
    print("¡TODAS LAS PRUEBAS DE APROBACIÓN VÍA TELEGRAM Y N8N PASARON AL 100%!")
    print("========================================================\n")

if __name__ == "__main__":
    test_telegram_approvals()
