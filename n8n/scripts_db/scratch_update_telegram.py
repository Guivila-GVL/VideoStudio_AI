import json
import subprocess
import os

SQL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sql')

sql_query = """
SELECT id, nodes FROM workflow_entity WHERE name = 'Fase 1: Agente Langchain con Memoria' LIMIT 1;
"""
with open(os.path.join(SQL_DIR, 'query_wf.sql'), 'w', encoding='utf-8') as f:
    f.write(sql_query)

result = subprocess.run(
    'docker exec -i timescaledb-db psql -U n8n -d n8n -t -c "SELECT id, nodes FROM workflow_entity WHERE name = \'Fase 1: Agente Langchain con Memoria\' LIMIT 1;"',
    shell=True,
    capture_output=True,
    text=True
)

output = result.stdout.strip()
if not output:
    print("Workflow no encontrado.")
    exit(1)

parts = output.split('|', 1)
wf_id = parts[0].strip()
nodes_str = parts[1].strip()

nodes = json.loads(nodes_str)

new_expression = """={{
  (function() {
    try {
      let raw = $json.output;
      if (typeof raw === 'string') {
        raw = raw.replace(/```json/g, '').replace(/```/g, '');
        // Si hay comillas escapadas extremas
        raw = raw.replace(/\\\\n/g, '\\n').replace(/\\\\"/g, '"');
        try { raw = JSON.parse(raw); } catch(e) {}
      }
      if (typeof raw === 'string') {
        try { raw = JSON.parse(raw); } catch(e) {}
      }
      
      let text = "¡Guion generado! 🎬\\n\\n";
      let escenas = raw.escenas;
      
      if (!Array.isArray(escenas) && raw.escenas) { 
          escenas = [raw.escenas]; 
      }
      
      if (escenas && escenas.length > 0) {
        escenas.forEach((e, i) => {
          text += `🎬 ESCENA ${i + 1}\\n`;
          text += `🗣️ Narrador: ${e.narrador}\\n`;
          text += `🎨 Prompt Imagen: ${e.prompt_imagen}\\n\\n`;
        });
      } else {
         text += "Formato distinto:\\n" + JSON.stringify(raw, null, 2) + "\\n\\n";
      }
      
      text += "¿Qué hacemos?";
      return text;
    } catch(e) {
      return "No he podido darle formato al guion. Aquí lo tienes en bruto:\\n\\n" + $json.output + "\\n\\n¿Qué hacemos?";
    }
  })()
}}"""

for node in nodes:
    if node['name'] == 'Telegram: Avisar':
        node['parameters']['text'] = new_expression

nodes_json = json.dumps(nodes, ensure_ascii=False).replace("'", "''")

update_sql = f"""
UPDATE workflow_entity 
SET nodes = '{nodes_json}'::json 
WHERE id = '{wf_id}';
"""
update_sql_file = os.path.join(SQL_DIR, 'update_wf.sql')
with open(update_sql_file, 'w', encoding='utf-8') as f:
    f.write(update_sql)

result_update = subprocess.run(
    f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{update_sql_file}"',
    shell=True,
    capture_output=True,
    text=True
)

if result_update.returncode == 0:
    print("Success updating telegram node.")
else:
    print("Failed.", result_update.stderr)
