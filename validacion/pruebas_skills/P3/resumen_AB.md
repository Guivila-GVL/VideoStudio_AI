# Comparativa A/B — Propuesta #P3 (Skill #102 `10114514/consistency-reference-prompt`)

- **Proyecto:** VideoStudio AI (`2026_Proyecto_Videos`)
- **Paso estricto evaluado:** `2. Consistencia visual de personajes y escenarios`
- **Skill candidata:** `#102 10114514/consistency-reference-prompt`
- **Caso real probado:** *Platero y yo* — Capítulo 2 (*Mariposas blancas*), Escena 4 (inspección nocturna del seroncillo con el pincho de hierro).

---

## 1. Qué parte de la Skill #102 se ha adaptado y qué se ha descartado

| Componente de `10114514/consistency-reference-prompt` | Decisión | Justificación en VideoStudio AI |
| :--- | :--- | :--- |
| **Layout de Personaje de 6 Vistas sin bordes** (1/3 izq: 3 close-ups de cabeza frontal/45°/90°; 2/3 der: 3 cuerpos enteros frontal/lateral/trasera en `#FFFFFF`) | ✅ **Adoptado / Adaptado** | Supera la ficha actual de 1 vista o grid 2x2 con líneas divisorias, dando 3 ángulos faciales completos y 3 de cuerpo entero sin marcos que contaminen `rembg` o `--cref`. |
| **Esquema estructurado de 9 atributos fijos** (`age, build, hair/coat, face, skin, clothing/tack, accessories, distinguishing features, expression baseline`) | ✅ **Adoptado / Adaptado** | Fija la escala relativa (Platero = 62% de la altura del Poeta de 13 años) y evita que el LLM o el motor confundan al Guarda de Consumos con Darbón. |
| **Fichas y Prompts de Props / Accesorios Multi-Estado** (fondo blanco `#FFFFFF`, sin manos humanas, regiones por estado: cerrado vs abierto) | ✅ **Adoptado / Adaptado** | Cubre un vacío total del Paso 2: objetos narrativos clave (seroncillo/alforja con mariposas, pincho de hierro, farol) pasan a tener ficha canónica y estados definidos. |
| **Preservación de detalle en sombras nocturnas** (`For night or low-light scenes, preserve shadow details — dark areas with visible detail, no crushed blacks`) | ✅ **Adoptado / Adaptado** | Evita sombras empastadas en escenas nocturnas de acuarela y elimina frases contradictorias de sol de mediodía (`cobalt blue sky without a shadow`). |
| **Restricción fija `16:9 horizontal, Realistic real-life, No anime/2D style`** | ❌ **Descartado** | Reemplazado por el ADN dinámico de cada proyecto (`vertical 9:16` y `delicate poetic watercolor and ink` en *Platero y yo*). |

---

## 2. Comparativa ANTES vs DESPUÉS (Resultados en `validacion/pruebas_skills/P3/`)

- **Imagen ANTES:** `consistencia_ANTES_actual.png`
  - **Problemas detectados:** Inyección errónea de `Darbón` (`--cref .../darbon.jpg`) como tercer personaje; colisión lumínica por inyectar `"under a cobalt blue sky without a shadow"` en una escena nocturna; ausencia total de referencias para la alforja y el pincho de hierro; hoja de modelo con 1 solo ángulo facial.
- **Imagen DESPUÉS:** `consistencia_DESPUES_skill102.png`
  - **Mejoras verificadas:** Hojas de 6 vistas sin bordes para Platero y El Poeta (3 close-ups faciales + 3 vistas de cuerpo entero sobre `#FFFFFF`), lámina de referencia de Props en 2 estados (Seroncillo cerrado vs abierto con mariposas blancas + Pincho de hierro sin manos humanas), bloqueo del falso positivo de Darbón y preservación de detalles en sombra nocturna.
