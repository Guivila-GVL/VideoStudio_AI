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

workflow_path = os.path.join(BASE_DIR, 'workflows', 'test_google_sheets_telegram.json')
if not os.path.exists(workflow_path):
    workflow_path = os.path.join(BASE_DIR, 'test_google_sheets_telegram.json')

with open(workflow_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

workflow_id = generate_random_id()
version_id = str(uuid.uuid4())
workflow_name = data.get('name', 'Test: Sheets a Telegram')

nodes_json = json.dumps(data.get('nodes', [])).replace("'", "''")
connections_json = json.dumps(data.get('connections', {})).replace("'", "''")

sql = f"""
INSERT INTO workflow_entity (id, name, active, nodes, connections, "versionId", "versionCounter", "isArchived", "triggerCount")
VALUES ('{workflow_id}', '{workflow_name}', false, '{nodes_json}'::json, '{connections_json}'::json, '{version_id}', 1, false, 0);
"""

sql_file = os.path.join(SQL_DIR, "insert_wf_test.sql")
with open(sql_file, 'w', encoding='utf-8') as f:
    f.write(sql)

print(f"Executing insertion for workflow ID: {workflow_id}")

result = subprocess.run(
    f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{sql_file}"', 
    shell=True, 
    capture_output=True, 
    text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)

if result.returncode == 0:
    print("Success! Now linking to user...")
    link_sql = f"""
    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT '{workflow_id}', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    """
    
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(link_sql)
        
    res2 = subprocess.run(
        f'docker exec -i timescaledb-db psql -U n8n -d n8n < "{sql_file}"', 
        shell=True, 
        capture_output=True, 
        text=True
    )
    print("Link STDOUT:", res2.stdout)
else:
    print("Failed to insert workflow.")
