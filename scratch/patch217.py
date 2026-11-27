p = 'app/core/consistency_reference_skill.py'
t = open(p, encoding='utf-8').read()
if 'exclude_characters' not in t:
    a = '    is_night_or_low_light: bool = True,\n    style_clause'
    assert a in t
    t = t.replace(a, '    is_night_or_low_light: bool = True,\n    exclude_characters: Optional[List[str]] = None,\n    style_clause')
    b = '    parts.append("Strict character lock: exclude unrelated database characters (NO Darbón the white-bearded veterinarian)")'
    assert b in t
    t = t.replace(b, '    excl = ["Darbón the white-bearded veterinarian"] if exclude_characters is None else exclude_characters\n    if excl:\n        parts.append("Strict character lock: exclude unrelated database characters (NO " + ", NO ".join(excl) + ")")')
    open(p, 'w', encoding='utf-8', newline='').write(t)
p = 'app/core/project_manager.py'
t = open(p, encoding='utf-8').read()
a = 'is_night_or_low_light=False, style_clause=style_clause'
assert a in t
t = t.replace(a, 'is_night_or_low_light=False, exclude_characters=[], style_clause=style_clause')
a = '+ ", no text, no watermarks"'
assert a in t
t = t.replace(a, '+ ", vertical 9:16 composition, no text, no watermarks"')
open(p, 'w', encoding='utf-8', newline='').write(t)
print("patched")
