# Mapa de Proceso — Videos

> Documento vivo estándar del proyecto (`docs/PROCESO_PROYECTO.md`).
> Última actualización: 27/11/2026 13:26. Se actualiza cada vez que cambian los pasos, programas o skills implicadas.

## Paso 1: Ingesta de libro/capítulo y guion Storyboard
- **Descripción:** Transforma un capítulo literario o idea en un guion vertical con gancho, nudo y desenlace optimizado para retención.
- **Programas / Archivos:** `app/core/, docs/plan_proyecto.md`
- **Skills utilizadas:** `04_NotebookLM_Antigravity`

## Paso 2: Consistencia visual de personajes y escenarios
- **Descripción:** Define rasgos físicos fijos del protagonista y escenarios para mantener coherencia en todas las escenas del vídeo.
- **Programas / Archivos:** `proyectos/banco_consistencia_global.json, docs/ESTRATEGIA_CONSISTENCIA_VISUAL.md, app/core/consistency_reference_skill.py, app/core/project_manager.py, app/core/script_generator.py, tests/test_consistency_skill102.py`
- **Skills utilizadas:** `#102 10114514/consistency-reference-prompt` (adoptada definitivamente, prueba A/B P3 validada: hoja de 6 vistas sin bordes opt-in con formato_vista=seis_vistas, perfiles de 9 atributos, fichas de props multi-estado y regla de preservación de sombras en escenas nocturnas aplicada automáticamente en craft_environment_prompt y enrich_scene_prompt_with_anchors; evidencias en validacion/pruebas_skills/P3)

## Paso 3: Aprobación Human-in-the-Loop vía Telegram
- **Descripción:** Envía propuestas visuales por Telegram con botones (Aprobar/Rechazar/Rehacer) y procesa respuestas en lenguaje natural.
- **Programas / Archivos:** `proyectos/telegram_wizard_state.json, n8n/workflows/`
- **Skills utilizadas:** `02_n8n_Antigravity`

## Paso 4: Generación de imágenes verticales (9:16)
- **Descripción:** Genera escenas en formato vertical con FLUX, Pollinations o DALL-E 3 a partir de los prompts aprobados.
- **Programas / Archivos:** `app/main.py, scratch/`
- **Skills utilizadas:** `Ninguna`

## Paso 5: Locución neuronal y narración de audio
- **Descripción:** Genera en producción la pista de voz narrada con Edge Neural, ElevenLabs o gTTS aplicando por defecto las 3 mejoras adoptadas de wind-comic (`services/tts.service.ts`): 1) modulación emocional por frase (velocidad y tono dinámicos), 2) voz diferenciada para narrador y personajes en diálogos, y 3) timestamps exactos por frase (`.sentences.json`) y por palabra (`.words.json`) para subtítulos sincronizados.
- **Programas / Archivos:** `app/core/tts_engine.py, app/main.py, docs/ESTRATEGIA_VOCES_NARRACION.md, validacion/pruebas_skills/P1/`
- **Skills utilizadas:** `#87 ChrisChen667788/wind-comic (patrón services/tts.service.ts)`

## Paso 6: Ensamblado y renderizado FFmpeg (Ken Burns + Subtítulos)
- **Descripción:** Une imágenes, audio, efecto Ken Burns (zoom/paneo) y subtítulos quemados en un MP4 final 1080x1920.
- **Programas / Archivos:** `scripts/ensamblar_video.py`
- **Skills utilizadas:** `Ninguna`

## Paso 7: Previsualización móvil y cierre de hitos
- **Descripción:** Revisión en simulador TikTok/Reels, exportación y registro del hito del proyecto.
- **Programas / Archivos:** `app/templates/, docs/REGISTRO_HITOS.md`
- **Skills utilizadas:** `03_Gestion_Proyecto`
