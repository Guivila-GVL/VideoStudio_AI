import os
import json
from pathlib import Path

base_dir = Path("proyectos/platero_y_yo")
esc_dir = base_dir / "escenarios"
char_dir = base_dir / "personajes"

# 1. Clean all discordant scenarios
for f in esc_dir.glob("*.*"):
    print("Removing discordant scenario:", f.name)
    f.unlink()

# 2. Clean discordant characters
for f in char_dir.glob("*.*"):
    if f.name in ["darbon.jpg", "diana.jpg", "platero.jpg"]:
        print("Preserving gold standard watercolor sheet:", f.name)
        continue
    print("Removing discordant/stale character file:", f.name)
    f.unlink()

# 3. Update proyecto.json
meta_file = base_dir / "proyecto.json"
with open(meta_file, "r", encoding="utf-8") as f:
    data = json.load(f)

for p in data.get("personajes", []):
    pid = p.get("id")
    if pid in ["darbon", "diana", "platero"]:
        p["imagen_url"] = f"/proyectos_data/platero_y_yo/personajes/{pid}.jpg"
    else:
        p["imagen_url"] = None

for e in data.get("escenarios", []):
    e["imagen_url"] = None

with open(meta_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Paso 1 completado con éxito.")
