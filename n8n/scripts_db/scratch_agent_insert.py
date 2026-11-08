import json
import uuid
import subprocess
import os

SQL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql')

def generate_random_id(length=16):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

nodes = []

# 1. Google Sheets Trigger
nodes.append({
    "parameters": {
        "pollTimes": {"item": [{"mode": "everyMinute"}]},
        "documentId": {
            "__rl": True,
            "value": "1frOoJEpplnjSKdgjg0vbCtBQhaxrYglSCocvn2C2F-4",
            "mode": "list",
            "cachedResultName": "Generador de Vídeos"
        },
        "sheetName": {
            "__rl": True,
            "value": "gid=0",
            "mode": "list",
            "cachedResultName": "Texto_Inicial"
        },
        "event": "rowAdded"
    },
    "name": "Google Sheets Trigger",
    "type": "n8n-nodes-base.googleSheetsTrigger",
    "typeVersion": 1,
    "position": [0, 0],
    "id": str(uuid.uuid4())
})

# 2. Code Node (Memoria)
code_js = """
let history = "";
try {
  let prevCode = $('Gestionar Historial').last();
  let previousHistory = prevCode ? (prevCode.json.history || "") : "";
  let lastDraft = $('OpenAI').last().json.message.content;
  
  let waitNode = $('Wait (Webhook Feedback)').last();
  let feedback = "Corregir (sin detalles)";
  if (waitNode && waitNode.json) {
    feedback = (waitNode.json.query && waitNode.json.query.feedback) || (waitNode.json.body && waitNode.json.body.feedback) || feedback;
  }
  
  history = previousHistory + "\\n\\n--- INTENTO ANTERIOR ---\\n" + lastDraft + "\\n\\n--- FEEDBACK DEL USUARIO ---\\n" + feedback;
} catch (e) {
  history = ""; // Primera ejecución
}
return { history: history };
"""
nodes.append({
    "parameters": {
        "jsCode": code_js
    },
    "name": "Gestionar Historial",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [200, 0],
    "id": str(uuid.uuid4())
})

# 3. OpenAI
nodes.append({
    "parameters": {
        "resource": "chat",
        "operation": "create",
        "model": "gpt-4o",
        "prompt": "={{ 'Texto original: ' + $('Google Sheets Trigger').first().json.Texto_Capitulo + '\\n\\n' + $json.history }}",
        "systemMessage": "Eres un director de vídeo experto. Divide el texto del usuario en escenas lógicas.\\n\\nReglas:\\n- Devuelve ÚNICAMENTE un objeto JSON puro (sin markdown, sin etiquetas ```json).\\n- El JSON debe tener una propiedad 'escenas' que sea un array.\\n- Cada escena debe tener:\\n  'narrador': el texto a locutar (español).\\n  'prompt_imagen': descripción visual ultra detallada (inglés).\\n\\nSi hay historial de intentos anteriores y feedback, adapta la nueva versión exactamente a las correcciones pedidas, manteniendo el formato JSON estricto.",
        "options": {
            "temperature": 0.7
        }
    },
    "name": "OpenAI",
    "type": "n8n-nodes-base.openAi",
    "typeVersion": 1,
    "position": [400, 0],
    "id": str(uuid.uuid4())
})

# 4. Telegram Avisar
nodes.append({
    "credentials": {
        "telegramApi": {
            "id": "telegram-cred-123",
            "name": "Bot2_Video_bot"
        }
    },
    "parameters": {
        "chatId": "7156474626",
        "text": "={{ '¡Guion generado!\\n\\n' + JSON.stringify($json.message.content) + '\\n\\n¿Qué hacemos?' }}",
        "replyMarkup": "inlineKeyboard",
        "inlineKeyboard": {
            "rows": [
                {
                    "row": {
                        "buttons": [
                            {
                                "text": "✅ Aprobar",
                                "url": "={{ $execution.resumeUrl }}?status=approved"
                            },
                            {
                                "text": "🔄 Corregir (Nota de voz)",
                                "url": "={{ $execution.resumeUrl }}?status=rejected"
                            }
                        ]
                    }
                }
            ]
        }
    },
    "name": "Telegram: Avisar",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.1,
    "position": [600, 0],
    "id": str(uuid.uuid4())
})

# 5. Wait 1
nodes.append({
    "parameters": {
        "resume": "webhook",
        "options": {}
    },
    "name": "Wait (Webhook Aprobación)",
    "type": "n8n-nodes-base.wait",
    "typeVersion": 1.1,
    "webhookId": str(uuid.uuid4()),
    "position": [800, 0],
    "id": str(uuid.uuid4())
})

# 6. Switch
nodes.append({
    "parameters": {
        "rules": {
            "values": [
                {
                    "conditions": {
                        "options": {"caseSensitive": True},
                        "conditions": [{"leftValue": "={{ $json.query.status }}", "rightValue": "approved", "operator": {"type": "string", "operation": "equals"}}],
                        "combinator": "and"
                    },
                    "renameOutput": True,
                    "outputKey": "Aprobado"
                },
                {
                    "conditions": {
                        "options": {"caseSensitive": True},
                        "conditions": [{"leftValue": "={{ $json.query.status }}", "rightValue": "rejected", "operator": {"type": "string", "operation": "equals"}}],
                        "combinator": "and"
                    },
                    "renameOutput": True,
                    "outputKey": "Rechazado"
                }
            ]
        }
    },
    "name": "Switch (Decisión)",
    "type": "n8n-nodes-base.switch",
    "typeVersion": 3,
    "position": [1000, 0],
    "id": str(uuid.uuid4())
})

# 7. Telegram Aprobado
nodes.append({
    "credentials": {
        "telegramApi": {
            "id": "telegram-cred-123",
            "name": "Bot2_Video_bot"
        }
    },
    "parameters": {
        "chatId": "7156474626",
        "text": "¡Perfecto! Guion aprobado. Avanzando a la siguiente fase..."
    },
    "name": "Telegram: Confirmar Aprobado",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.1,
    "position": [1200, -100],
    "id": str(uuid.uuid4())
})

# 8. Telegram Pedir Feedback
nodes.append({
    "credentials": {
        "telegramApi": {
            "id": "telegram-cred-123",
            "name": "Bot2_Video_bot"
        }
    },
    "parameters": {
        "chatId": "7156474626",
        "text": "Has rechazado el guion. Por favor, mándame una nota de voz explicándome qué quieres cambiar.\\n(El sistema guardará tu respuesta y regenerará el guion automáticamente)."
    },
    "name": "Telegram: Pedir Voice",
    "type": "n8n-nodes-base.telegram",
    "typeVersion": 1.1,
    "position": [1200, 100],
    "id": str(uuid.uuid4())
})

# 9. Google Sheets Guardar URL
nodes.append({
    "credentials": {
        "googleSheetsOAuth2Api": {
            "id": "S3I8PdYk18jMX8jG",
            "name": "Google Sheets Trigger account"
        }
    },
    "parameters": {
        "operation": "update",
        "documentId": {
            "__rl": True,
            "value": "1frOoJEpplnjSKdgjg0vbCtBQhaxrYglSCocvn2C2F-4",
            "mode": "list"
        },
        "sheetName": {
            "__rl": True,
            "value": "gid=0",
            "mode": "list"
        },
        "columns": {
            "mappingMode": "defineBelow",
            "value": {
                "Webhook_Feedback": "={{ $execution.resumeUrl }}"
            }
        },
        "options": {}
    },
    "name": "Google Sheets (Guardar URL)",
    "type": "n8n-nodes-base.googleSheets",
    "typeVersion": 4,
    "position": [1400, 100],
    "id": str(uuid.uuid4())
})

# 10. Wait Feedback
nodes.append({
    "parameters": {
        "resume": "webhook",
        "options": {}
    },
    "name": "Wait (Webhook Feedback)",
    "type": "n8n-nodes-base.wait",
    "typeVersion": 1.1,
    "webhookId": str(uuid.uuid4()),
    "position": [1600, 100],
    "id": str(uuid.uuid4())
})


connections = {
    "Google Sheets Trigger": {"main": [[{"node": "Gestionar Historial", "type": "main", "index": 0}]]},
    "Gestionar Historial": {"main": [[{"node": "OpenAI", "type": "main", "index": 0}]]},
    "OpenAI": {"main": [[{"node": "Telegram: Avisar", "type": "main", "index": 0}]]},
    "Telegram: Avisar": {"main": [[{"node": "Wait (Webhook Aprobación)", "type": "main", "index": 0}]]},
    "Wait (Webhook Aprobación)": {"main": [[{"node": "Switch (Decisión)", "type": "main", "index": 0}]]},
    "Switch (Decisión)": {
        "main": [
            [{"node": "Telegram: Confirmar Aprobado", "type": "main", "index": 0}],
            [{"node": "Telegram: Pedir Voice", "type": "main", "index": 0}]
        ]
    },
    "Telegram: Pedir Voice": {"main": [[{"node": "Google Sheets (Guardar URL)", "type": "main", "index": 0}]]},
    "Google Sheets (Guardar URL)": {"main": [[{"node": "Wait (Webhook Feedback)", "type": "main", "index": 0}]]},
    "Wait (Webhook Feedback)": {"main": [[{"node": "Gestionar Historial", "type": "main", "index": 0}]]}
}

new_workflow = {
    "name": "Fase 1: Agente con Memoria (Voz)",
    "nodes": nodes,
    "connections": connections
}

out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'workflows', 'flujo_fase1_agente.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(new_workflow, f, indent=2, ensure_ascii=False)

# Insertar en BD
workflow_id = generate_random_id()
version_id = str(uuid.uuid4())
workflow_name = "Fase 1: Agente con Memoria (Voz)"

nodes_json = json.dumps(nodes, ensure_ascii=False).replace("'", "''")
connections_json = json.dumps(connections, ensure_ascii=False).replace("'", "''")

sql = f"""
INSERT INTO workflow_entity (id, name, active, nodes, connections, "versionId", "versionCounter", "isArchived", "triggerCount")
VALUES ('{workflow_id}', '{workflow_name}', false, '{nodes_json}'::json, '{connections_json}'::json, '{version_id}', 1, false, 0);
"""

sql_file = os.path.join(SQL_DIR, "insert_wf_agent.sql")
with open(sql_file, 'w', encoding='utf-8') as f:
    f.write(sql)

result = subprocess.run(
    f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{sql_file}"', 
    shell=True, 
    capture_output=True, 
    text=True
)

if result.returncode == 0:
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
    print("Success inserting Workflow 1.")
else:
    print("Failed.", result.stderr)
