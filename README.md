# VideoStudio AI 🎬 (2026)

**Estudio de producción integral para crear vídeos cortos verticales (TikTok, Instagram Reels y YouTube Shorts) con Human-in-the-Loop y consistencia visual.**

---

## 🌟 ¿Qué es VideoStudio AI?

Este proyecto nació para reemplazar los flujos complejos y frágiles basados en bots de Telegram y webhooks de n8n por una **aplicación web visual, potente y local** (al estilo de *Proyecto Comentarista*).

Permite convertir cualquier texto, capítulo de libro, microrrelato o idea en un vídeo vertical de alto impacto (1080×1920) con:
1. **Consistencia de Personajes:** Inyección de rasgos físicos fijos del protagonista en cada escena.
2. **Desglose Storyboard:** Guion adaptado al ritmo de retención de redes sociales (gancho, nudo y desenlace).
3. **Locución Neuronal:** Integración con **ElevenLabs** (voces de estudio como George, Charlie, Sarah) y **gTTS** (gratuito sin API Key).
4. **Imágenes Verticales (9:16):** Generación con **FLUX** (alta definición, ultrarrápido y sin coste) o **DALL-E 3**, con soporte para subir imágenes propias.
5. **Renderizado FFmpeg:** Animación con movimiento dinámico **Ken Burns** (zoom y paneo suaves) y subtítulos quemados de alto contraste.
6. **Previsualizador de Smartphone:** Simulador interactivo de TikTok / Reels para comprobar el vídeo antes de descargarlo.

---

## 🚀 Inicio Rápido

### 1. Iniciar con un Clic (Windows)
Haz doble clic en el archivo:
```bash
iniciar_videos.bat
```
Esto abrirá automáticamente tu navegador en `http://localhost:8001`.

### 2. Iniciar Manualmente por Terminal
```bash
cd 2026_Proyecto_Videos
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

---

## 🛠️ Estructura del Proyecto

```
2026_Proyecto_Videos/
├── app/                         # Aplicación Web FastAPI
│   ├── core/
│   │   ├── script_generator.py  # Desglose de guion y prompts con IA
│   │   ├── tts_engine.py        # Locución (ElevenLabs + gTTS + OpenAI)
│   │   ├── image_engine.py      # Generación de imágenes (FLUX + DALL-E 3)
│   │   ├── video_renderer.py    # Renderizado y montaje FFmpeg con Ken Burns
│   │   ├── project_manager.py   # Guardado de proyectos, personajes y escenarios
│   │   └── document_parser.py   # Extracción de texto de libros (PDF, DOCX, TXT)
│   ├── static/
│   │   ├── css/style.css        # Diseño oscuro de estudio (Glassmorphism)
│   │   ├── js/app.js            # Lógica interactiva del cliente
│   │   └── media/               # Audios, imágenes y vídeos MP4 generados
│   ├── templates/
│   │   └── index.html           # Interfaz web principal y mockup móvil
│   └── main.py                  # API backend FastAPI
├── proyectos/                   # Biblioteca de proyectos literarios (Platero, Principito, etc.)
│   └── {proyecto_id}/           # Carpetas: personajes/, escenarios/, documentos/, capitulos/
├── tests/                       # Suite de pruebas automatizadas
│   ├── test_api.py              # Comprobación de API y lectura de proyectos
│   └── test_app.py              # Test integral del pipeline (guion, voz, imagen, vídeo)
├── scripts/                     # Scripts auxiliares y herramientas CLI
│   └── ensamblar_video.py       # Ensamblador standalone MoviePy
├── n8n/                         # Automatizaciones históricas / flujos n8n
│   ├── workflows/               # Flujos exportados en formato JSON (11 workflows)
│   └── scripts_db/              # Scripts auxiliares de base de datos e inyecciones SQL
├── docs/                        # Documentación adicional y especificaciones
│   └── plan_proyecto.md         # Documento inicial de diseño del proyecto
├── .env                         # Claves de API (OpenAI, ElevenLabs)
├── iniciar_videos.bat           # Lanzador rápido
└── requirements.txt             # Dependencias del proyecto
```

---

## ⚙️ Configuración de API Keys

Puedes configurar o cambiar tus claves directamente desde la interfaz web (botón de engranaje ⚙️ en la barra superior) o editando el archivo `.env`:

```env
OPENAI_API_KEY=sk-proj-...
ELEVENLABS_API_KEY=sk_...
PORT=8001
HOST=127.0.0.1
```
