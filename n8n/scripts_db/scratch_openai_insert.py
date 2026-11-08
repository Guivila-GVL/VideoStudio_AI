import json
import uuid
import subprocess

def generate_random_id(length=16):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
SQL_DIR = os.path.join(SCRIPT_DIR, 'sql')

with open(os.path.join(BASE_DIR, 'test_google_sheets_telegram.json'), 'r', encoding='utf-8') as f:
    base_data = json.load(f)

# Modificar posiciones y añadir OpenAI
nodes = base_data['nodes']
connections = base_data['connections']

# Encontrar nodos existentes
trigger_node = next(n for n in nodes if n['name'] == 'Google Sheets Trigger')
telegram_avisar = next(n for n in nodes if n['name'] == 'Telegram: Avisar')
wait_node = next(n for n in nodes if n['name'] == 'Wait (Webhook)')
switch_node = next(n for n in nodes if n['name'] == 'Switch (Decisión)')
telegram_aprobado = next(n for n in nodes if n['name'] == 'Telegram: Confirmar Aprobado')
telegram_rechazado = next(n for n in nodes if n['name'] == 'Telegram: Confirmar Rechazo')

# Actualizar posiciones
trigger_node['position'] = [0, 0]
telegram_avisar['position'] = [400, 0]
wait_node['position'] = [600, 0]
switch_node['position'] = [800, 0]
telegram_aprobado['position'] = [1000, -100]
telegram_rechazado['position'] = [1000, 100]

# Crear nodo OpenAI
openai_node = {
    "parameters": {
        "resource": "chat",
        "operation": "create",
        "model": "gpt-4o",
        "prompt": "={{ $('Google Sheets Trigger').first().json.Texto_Capitulo }}",
        "systemMessage": "Eres un director de vídeo experto. Divide el texto del usuario en 2 a 5 escenas.\n\nReglas:\n- Devuelve ÚNICAMENTE un objeto JSON puro (sin markdown, sin bloques ```json).\n- El JSON debe tener una propiedad 'escenas' que sea un array.\n- Cada escena debe tener:\n  'narrador': el texto que se leerá en off (español).\n  'prompt_imagen': descripción en inglés hiper-detallada para Midjourney.\n\nSi notas que esto es un reintento, intenta generar una versión ligeramente diferente.",
        "options": {
            "temperature": 0.8
        }
    },
    "name": "OpenAI (Generar Guion)",
    "type": "n8n-nodes-base.openAi",
    "typeVersion": 1,
    "position": [200, 0]
}

nodes.append(openai_node)

# Cambiar texto de Telegram Avisar para mostrar el resultado de OpenAI
telegram_avisar['parameters']['text'] = "={{ '¡Borrador generado por OpenAI!\\n\\n' + JSON.stringify($json.message.content) + '\\n\\n¿Qué hacemos?' }}"

# Actualizar conexiones
connections = {
    "Google Sheets Trigger": {
        "main": [
            [
                {
                    "node": "OpenAI (Generar Guion)",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "OpenAI (Generar Guion)": {
        "main": [
            [
                {
                    "node": "Telegram: Avisar",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Telegram: Avisar": {
        "main": [
            [
                {
                    "node": "Wait (Webhook)",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Wait (Webhook)": {
        "main": [
            [
                {
                    "node": "Switch (Decisión)",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Switch (Decisión)": {
        "main": [
            [
                {
                    "node": "Telegram: Confirmar Aprobado",
                    "type": "main",
                    "index": 0
                }
            ],
            [
                {
                    "node": "Telegram: Confirmar Rechazo",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    },
    "Telegram: Confirmar Rechazo": {
        "main": [
            [
                {
                    "node": "OpenAI (Generar Guion)",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
}

new_workflow = {
    "name": "Fase 1: OpenAI + Bucle Ciego",
    "nodes": nodes,
    "connections": connections
}

out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'workflows', 'flujo_fase1_openai.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(new_workflow, f, indent=2, ensure_ascii=False)

# Insertar en BD
workflow_id = generate_random_id()
version_id = str(uuid.uuid4())
workflow_name = "Fase 1: OpenAI + Bucle Ciego"

nodes_json = json.dumps(nodes, ensure_ascii=False).replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")

sql = f"""
INSERT INTO workflow_entity (id, name, active, nodes, connections, "versionId", "versionCounter", "isArchived", "triggerCount")
VALUES ('{workflow_id}', '{workflow_name}', false, '{nodes_json}'::json, '{connections_json}'::json, '{version_id}', 1, false, 0);
"""

sql_file = os.path.join(SQL_DIR, "insert_wf_openai.sql")
with open(sql_file, 'w', encoding='utf-8') as f:
    f.write(sql)

result = subprocess.run(
    f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{sql_file}"', 
    shell=True, 
    capture_output=True, 
    text=True
)

if result.returncode == 0:
    print("Success! Now linking to user...")
    link_sql = f"""
    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT '{workflow_id}', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    """
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(link_sql)
        
    subprocess.run(
        f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{sql_file}"', 
        shell=True
    )
    print("Link done.")
else:
    print("Failed.", result.stderr)
