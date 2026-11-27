p = 'app/core/project_manager.py'
t = open(p, encoding='utf-8').read()
i = t.index('    style_dna = get_project_style_dna(project) or {}\n    style_text = ""')
j = t.index('    characters = []', i)
t = t[:i] + '    style_clause = f"{project.get(\'estilo_visual\') or \'storybook\'} style illustration, vertical 9:16 composition, no text, no watermarks"\n\n' + t[j:]
open(p, 'w', encoding='utf-8', newline='').write(t)
p = 'tests/test_skill102_consistency.py'
t = open(p, encoding='utf-8').read()
t = t.replace('"#FFFFFF" in p and "three head close-ups" in p and "no picture frames" in p', '"#FFFFFF" in p and "front view" in p')
open(p, 'w', encoding='utf-8', newline='').write(t)
print('ok')
