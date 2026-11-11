import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Añadir directorio raíz del proyecto al sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app

def test_api():
    client = TestClient(app)
    
    print("=== TEST API: 1. Comprobando ruta principal (UI) ===")
    res = client.get("/")
    assert res.status_code == 200, f"Error en GET /: {res.status_code}"
    assert "VideoStudio AI" in res.text
    print("[OK] UI cargada correctamente (Status 200)")

    print("\n=== TEST API: 2. Comprobando lista de proyectos en disco ===")
    res = client.get("/api/projects")
    assert res.status_code == 200, f"Error en GET /api/projects: {res.status_code}"
    proyectos = res.json()
    assert isinstance(proyectos, list), "La respuesta debe ser una lista"
    print(f"[OK] {len(proyectos)} proyectos encontrados en la carpeta 'proyectos/':")
    for p in proyectos:
        print(f"   - {p.get('id')} ({p.get('titulo')})")
    assert len(proyectos) >= 3, "Se esperaban al menos 3 proyectos"

    print("\n=== TEST API: 3. Comprobando lectura de un proyecto específico ===")
    res = client.get("/api/projects/platero_y_yo")
    assert res.status_code == 200, f"Error en GET /api/projects/platero_y_yo: {res.status_code}"
    data = res.json()
    assert data["id"] == "platero_y_yo"
    print(f"[OK] Proyecto 'platero_y_yo' cargado con {len(data.get('capitulos', []))} capítulos")

    print("\n=== TEST API: 4. Comprobando endpoint de voces disponibles ===")
    res = client.get("/api/voices")
    assert res.status_code == 200
    voces = res.json()
    print(f"[OK] {len(voces)} voces configuradas")

    print("\n=== TEST API: 5. Comprobando endpoint de estado del sistema ===")
    res = client.get("/api/status")
    assert res.status_code == 200
    status_data = res.json()
    estilos = status_data.get("styles_available", [])
    print(f"[OK] Estado verificado: {len(estilos)} estilos disponibles, {status_data.get('media_count')} archivos en media/")

    print("\n=== TEST API: 6. Comprobando lectura y desglose del manuscrito (pages & chapters) ===")
    res = client.get("/api/projects/platero_y_yo/documents/content")
    assert res.status_code == 200, f"Error en GET documents/content: {res.status_code}"
    doc_data = res.json()["document"]
    pages = doc_data.get("pages", [])
    chapters_detected = doc_data.get("chapters", [])
    print(f"[OK] Manuscrito analizado: {doc_data.get('total_pages')} paginas y {len(chapters_detected)} secciones detectadas")
    assert len(pages) > 0, "Debe haber paginas extraidas del PDF"
    assert "page_number" in pages[0]
    assert "text" in pages[0]

    print("\n=== TEST API: 7. Comprobando creacion, lectura y eliminacion de un capitulo ===")
    test_cap = {
        "project_id": "platero_y_yo",
        "titulo": "Capitulo Test CI",
        "texto_original": "Platero es pequeno, peludo, suave; tan blando por fuera...",
        "origen_tipo": "page",
        "origen_ref": "1",
        "orden": 1,
        "scenes": [
            {
                "id": 1,
                "narrador": "Platero es pequeno y suave.",
                "prompt_imagen": "Cute silver donkey in a meadow, watercolor, 9:16 vertical",
                "duracion_estimada": 5
            }
        ]
    }
    save_res = client.post("/api/projects/platero_y_yo/chapters", json=test_cap)
    assert save_res.status_code == 200
    saved_cap = save_res.json()["chapter"]
    cap_id = saved_cap["id"]
    print(f"[OK] Capitulo guardado con ID: {cap_id} y status '{saved_cap.get('status', 'storyboard')}'")

    list_res = client.get("/api/projects/platero_y_yo/chapters")
    assert list_res.status_code == 200
    caps = list_res.json()
    assert any(c["id"] == cap_id for c in caps), "El capitulo debe aparecer en el arbol de capitulos"
    print(f"[OK] Arbol de capitulos contiene {len(caps)} capitulo(s)")

    del_res = client.delete(f"/api/projects/platero_y_yo/chapters/{cap_id}")
    assert del_res.status_code == 200
    print(f"[OK] Capitulo {cap_id} eliminado correctamente")

    print("\n=== TEST API: 8. Comprobando importacion en lote (batch-import) ===")
    batch_res = client.post("/api/projects/platero_y_yo/chapters/batch-import", json={"source": "chapters", "max_items": 4})
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    count = batch_data.get("count", 0)
    print(f"[OK] Importacion en lote ejecutada con exito: {count} capitulos creados")
    assert count > 0, "Debe haber importado al menos 1 capitulo"

    # Limpiar únicamente los capitulos importados de prueba por el test
    for c in batch_data.get("chapters", []):
        if c["id"].startswith("cap_sec_") or c["id"].startswith("cap_pag_"):
            client.delete(f"/api/projects/platero_y_yo/chapters/{c['id']}")
    print(f"[OK] Limpieza de capitulos de prueba completada")

    print("\n=== TEST API: 9. Comprobando inyeccion de anclas de consistencia visual (/api/storyboard/inject-anchors) ===")
    inject_req = {
        "scene": {
            "id": 1,
            "narrador": "Platero camina por el prado de flores.",
            "prompt_imagen": "A fluffy donkey walking in a meadow with flowers",
            "personajes_en_escena": ["Platero"],
            "escenario_clave": "Las Colinas y el Molino de Viento"
        },
        "characters": [
            {
                "id": "platero",
                "nombre": "Platero",
                "tipo": "animal_cuadrupedo",
                "descripcion_visual": "Platero es pequeño, peludo, suave; tan blando por fuera que se diría todo de algodón."
            }
        ],
        "escenarios": [
            {
                "id": "colinas_molino_viento",
                "nombre": "Las Colinas y el Molino de Viento",
                "descripcion_visual": "Colinas andaluzas con olivos y molino de viento tradicional."
            }
        ],
        "style_key": "watercolor"
    }
    inj_res = client.post("/api/storyboard/inject-anchors", json=inject_req)
    assert inj_res.status_code == 200, f"Error en inject-anchors: {inj_res.status_code}"
    inj_data = inj_res.json()
    new_prompt = inj_data["scene"]["prompt_imagen"]
    assert "Platero" in new_prompt
    assert "Colinas" in new_prompt or "Molino" in new_prompt
    assert "9:16" in new_prompt
    print(f"[OK] Inyeccion de anclas validada con éxito:")
    print(f"   Prompt resultante: {new_prompt[:120]}...")

    print("\n=== TEST API: 10. Comprobando capitulo 1 renderizado y fichero de video ===")
    cap1_res = client.get("/api/projects/platero_y_yo/chapters/cap_01_platero")
    assert cap1_res.status_code == 200, "El capitulo 1 debe existir"
    cap1 = cap1_res.json()
    assert cap1.get("video_url"), "El capitulo 1 debe tener video_url asignada"
    video_clean_path = cap1["video_url"].split("?")[0].lstrip("/")
    if video_clean_path.startswith("proyectos_data/"):
        video_abs_path = PROJECT_ROOT / "proyectos" / video_clean_path[len("proyectos_data/"):]
    else:
        video_abs_path = PROJECT_ROOT / "app" / video_clean_path
    assert video_abs_path.exists(), f"El archivo de video {video_abs_path} debe existir en disco"
    assert video_abs_path.stat().st_size > 500000, "El archivo de video debe tener un tamaño válido (>500KB)"
    print(f"[OK] Video validado: {cap1['video_url']} ({video_abs_path.stat().st_size / (1024*1024):.2f} MB, duracion {cap1.get('duracion')}s)")

    print("\n=== TEST API: 11. Comprobando Banco de Consistencia de Personajes (--cref / LoRA) y acceso desde Generador de Prompts ===")
    bank_res = client.get("/api/character-bank")
    assert bank_res.status_code == 200, f"Error en GET /api/character-bank: {bank_res.status_code}"
    bank_data = bank_res.json()
    assert bank_data["success"] is True
    assert bank_data["total_personajes"] >= 13
    assert bank_data["referencias_listas"] == bank_data["total_personajes"], "Todas las hojas de referencia deben existir en disco"
    print(f"[OK] Banco Global de Consistencia: {bank_data['referencias_listas']}/{bank_data['total_personajes']} personajes con hoja de referencia verificada en disco")

    # Verificar banco por proyecto y actualización de parámetros --cref / LoRA
    p_bank_res = client.get("/api/projects/platero_y_yo/character-bank")
    assert p_bank_res.status_code == 200
    p_bank = p_bank_res.json()
    assert p_bank["referencias_listas"] == 8
    platero_ref = next(c for c in p_bank["personajes"] if c["id"] == "platero")
    assert "--cref /proyectos_data/platero_y_yo/personajes/platero.jpg" in platero_ref["cref_directive"]
    assert "<lora:" in platero_ref["lora_directive"]

    # Verificar que el generador de prompts accede automáticamente a las hojas de referencia guardadas en disco (incluso sin pasarle 'characters' en el request)
    inj_bank_res = client.post("/api/storyboard/inject-anchors", json={
        "project_id": "platero_y_yo",
        "scene": {
            "id": 1,
            "narrador": "Platero y Diana pasean juntos al amanecer.",
            "prompt_imagen": "Walking together in the morning light",
            "personajes_en_escena": ["Platero", "Diana"],
            "escenario_clave": "Las Colinas y el Molino de Viento"
        },
        "style_key": "watercolor",
        "include_technical_flags": True
    })
    assert inj_bank_res.status_code == 200
    inj_scene = inj_bank_res.json()["scene"]
    assert len(inj_scene.get("referencias_personajes", [])) == 2
    assert inj_scene["reference_image"] is not None
    assert "--cref /proyectos_data/platero_y_yo/personajes/platero.jpg" in inj_scene["prompt_tecnico_cref"]
    assert "<lora:" in inj_scene["prompt_tecnico_cref"]
    print(f"[OK] Generador de prompts accedio al Banco de Consistencia e inyecto referencias: {inj_scene['prompt_tecnico_cref'][:140]}...")

    print("\n=== TEST API: 12. Comprobando Voces Nativas Espanolas y Sintesis de Narrador ===")
    narrator_res = client.get("/api/projects/platero_y_yo/narrator")
    assert narrator_res.status_code == 200
    narrator_info = narrator_res.json()
    assert narrator_info["success"] is True
    assert narrator_info["voz_defecto"] == "edge_alvaro_joven"

    # Test voz sintetizada en tiempo real con edge_alvaro_joven
    test_voice_res = client.post("/api/projects/platero_y_yo/narrator/test-voice", json={
        "voice_id": "edge_alvaro_joven",
        "sample_text": "Platero es pequeno, peludo, suave; tan blando por fuera, que se diria todo de algodon."
    })
    assert test_voice_res.status_code == 200
    voice_audio = test_voice_res.json()
    assert voice_audio["success"] is True
    assert voice_audio["provider"] == "edge"
    assert voice_audio["duration"] > 0
    print(f"[OK] Sintesis de voz en espanol nativo verificada con exito: {voice_audio['url']} ({voice_audio['duration']}s)")

    print("\n[EXITO] Todos los tests de la API, Consistencia Visual, Pipeline y Voces Espanolas pasaron al 100%!")

if __name__ == "__main__":
    test_api()

