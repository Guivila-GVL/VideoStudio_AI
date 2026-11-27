import urllib.request, json, sys
def call(m, path, body):
    r = urllib.request.Request("http://127.0.0.1:8002/api/tasks/217/"+path, data=json.dumps(body).encode("utf-8"), method=m, headers={"Content-Type":"application/json; charset=utf-8"})
    print(urllib.request.urlopen(r, timeout=60).read().decode("utf-8")[:300])
k = sys.argv[1]
if k=="1": call("PATCH","progress",{"progress_pct":20,"stage":"plan","current_step":"Ya se ha pensado en cómo implementarlo: exponer en producción la skill #102 (hoja 6 vistas, props, sombras nocturnas) vía get_skill102_reference_prompts + endpoint, heredando el ADN visual del proyecto"})
if k=="2": call("PATCH","progress",{"progress_pct":50,"stage":"development","current_step":"Comienza el desarrollo: project_manager.get_skill102_reference_prompts, endpoint /consistency-reference-prompts, tests/test_skill102_consistency.py y PROCESO_PROYECTO.md"})
if k=="3": call("PATCH","progress",{"progress_pct":80,"stage":"validation","current_step":"Ha acabado el desarrollo y ahora comienza la validación: pytest completo del proyecto"})
