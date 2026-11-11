import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.core.project_manager import get_project, save_or_update_project
from app.core.telegram_approvals import (
    get_telegram_config,
    parse_natural_language_decision,
    apply_approval_decision,
    process_telegram_update,
    send_character_approval,
    send_environment_approval
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

    print("\n========================================================")
    print("¡TODAS LAS PRUEBAS DE APROBACIÓN VÍA TELEGRAM PASARON AL 100%!")
    print("========================================================\n")

if __name__ == "__main__":
    test_telegram_approvals()
