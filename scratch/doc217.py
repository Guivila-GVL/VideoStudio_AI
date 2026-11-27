p = 'docs/PROCESO_PROYECTO.md'
t = open(p, encoding='utf-8').read()
old = "- **Programas / Archivos:** `proyectos/banco_consistencia_global.json, docs/ESTRATEGIA_CONSISTENCIA_VISUAL.md`\n- **Skills utilizadas:** `Ninguna`"
if old not in t:
    old = old.replace("\n", "\r\n")
assert old in t
nl = "\r\n" if "\r\n" in old else "\n"
new = ("- **Programas / Archivos:** `proyectos/banco_consistencia_global.json, docs/ESTRATEGIA_CONSISTENCIA_VISUAL.md, app/core/consistency_reference_skill.py, app/core/project_manager.py (get_skill102_reference_prompts), GET /api/projects/{id}/consistency-reference-prompts, tests/test_skill102_consistency.py, validacion/pruebas_skills/P3/`" + nl +
       "- **Skills utilizadas:** `#102 10114514/consistency-reference-prompt (hoja de personaje 6 vistas sobre #FFFFFF sin marcos, perfil de 9 atributos, fichas de props multi-estado y preservación de sombras en escenas nocturnas; adoptada definitivamente tras prueba A/B P3, tarea 217)`")
open(p, 'w', encoding='utf-8', newline='').write(t.replace(old, new))
print("doc ok")
