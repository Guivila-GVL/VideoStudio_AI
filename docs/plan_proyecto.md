# Plan de Producción: Serie de Vídeos Cortos (Historia/Capítulos)

## 1. Objetivo del Proyecto
Crear un flujo de trabajo para producir una serie de vídeos cortos (formato vertical para TikTok, Instagram Reels, YouTube Shorts) basados en textos literarios (capítulos cortos de un libro, poemas o historias). El elemento clave será mantener una narrativa continua y la **consistencia de los personajes** a lo largo de los diferentes episodios.

---

## 2. Flujo de Trabajo (Pipeline) Propuesto con Revisiones (Semi-Automático)

Para lograr un proceso automático pero que te permita tener control de calidad, usaremos un modelo de **"Human-in-the-Loop"** (Humano en el medio). El proceso se pausará en puntos clave para que tú apruebes o pidas cambios antes de gastar créditos en el siguiente paso.

El flujo ideal con **n8n + Google Sheets/Airtable** sería:

1. **Adaptación del Texto a Guion:** 
   - n8n lee el capítulo y usa ChatGPT/Claude para generar el guion y los prompts de las imágenes.
   - *Punto de Control 1:* n8n guarda el resultado en un Google Sheet y te envía un mensaje por Telegram ("Guion listo para revisar"). Tú lo lees, lo corriges si hace falta y marcas una casilla como "Aprobado".
2. **Generación de Voz (Voiceover) e Imágenes:** 
   - Al marcar "Aprobado", n8n automáticamente envía el texto a ElevenLabs para la voz y los prompts a Midjourney para las imágenes.
   - *Punto de Control 2:* n8n te envía por Telegram los audios y las fotos generadas. Tienes botones para "Aprobar" o "Regenerar imagen 3".
3. **Animación de Imágenes (Video):** 
   - Una vez aprobadas las fotos, n8n las envía a Runway/Luma para darles movimiento.
4. **Edición y Ensamblaje:** 
   - Un script une la voz, los clips de vídeo animados, música de fondo y subtítulos.
   - *Punto de Control 3:* Recibes el MP4 final para darle el visto bueno antes de publicar.
5. **Programación/Publicación:** Automatizar la subida a las redes sociales.

---

## 3. ¿Cómo Mantener la Consistencia de los Personajes?

Para que los personajes sean idénticos en el capítulo 1 y en el capítulo 50, aplicaremos estas estrategias:

### A. Si usamos Midjourney (Recomendado)
- **Hoja de Personaje (Character Sheet):** Antes de empezar la serie, generaremos una imagen de referencia perfecta para cada personaje principal (rostro claro, ropa neutra o característica). Guardaremos la URL de esa imagen.
- **Parámetro `--cref` (Character Reference):** En la automatización, cada vez que n8n le pida a Midjourney crear una escena con el protagonista, le añadirá al final del prompt el código `--cref URL_DE_LA_IMAGEN --cw 100`. Esto fuerza a la IA a calcar la cara, el peinado y la ropa del personaje original en cualquier nueva pose o fondo.

### B. Si usamos Stable Diffusion (Alternativa Pro)
- **FaceID / IP-Adapter:** Es una tecnología que permite inyectar una cara específica en cualquier imagen generada.
- **Entrenamiento de LoRA:** Si es un proyecto muy a largo plazo, podemos entrenar un modelo pequeño (LoRA) con 15 fotos de nuestro personaje. Así, con solo escribir `<lora:mi_personaje>`, la IA lo dibujará perfecto siempre.

### C. Consistencia en el Prompt (Texto)
El LLM (ChatGPT) que genera los prompts estará programado con unas "Instrucciones de Sistema" que le obligarán a describir siempre al personaje con las mismas palabras clave exactas (ej: *"hombre de 30 años, pelo castaño corto, chaqueta de cuero roja"*), lo cual ayuda enormemente a la IA gráfica a no desviarse.

---

## 4. Herramientas Propuestas

- **Orquestación y Revisiones:** **n8n** (concreta los flujos) + **Telegram** (para botones de aprobar/rechazar) + **Google Sheets** (como base de datos del estado de cada capítulo).
- **Adaptación de Guion:** OpenAI (GPT-4o) o Anthropic (Claude 3.5 Sonnet).
- **Generación de Voz:** **ElevenLabs** (permite clonar una voz y usarla idéntica en todos los capítulos).
- **Generación de Imágenes:** **Midjourney** (v6) mediante API no oficial, o **Stable Diffusion** vía API.
- **Animación de Vídeo:** **Runway Gen-3 Alpha** o **Luma Dream Machine**.
- **Ensamblaje Automático:** Scripts en **Python (MoviePy / FFmpeg)**.

---

## 5. Estimación de Costes (por episodio de ~60 segundos)

*Cálculo aproximado asumiendo el uso de APIs comerciales y un vídeo final de unos 60 segundos.*

| Fase | Herramienta | Coste Estimado por Vídeo |
| :--- | :--- | :--- |
| **Guion (LLM)** | ChatGPT API / Claude | ~$0.02 - $0.05 |
| **Voz** | ElevenLabs | ~$0.20 - $0.30 |
| **Imágenes** | Midjourney (Suscripción plana) | ~$0.10 (prorrateado) |
| **Vídeo** | Runway / Luma (API o créditos) | ~$1.00 - $2.00 |
| **Total Estimado** | | **~$1.32 - $2.45 por vídeo** |

---

## 6. Próximos Pasos

Dime si este enfoque de **Telegram + Google Sheets para las aprobaciones** te parece cómodo, y si la estrategia de **Midjourney (`--cref`)** te convence para mantener a los personajes. 

Si te parece bien, el siguiente paso podría ser hacer un pequeño esquema de cómo sería el flujo exacto en n8n o probar a generar la "Hoja de Personaje" de prueba.
