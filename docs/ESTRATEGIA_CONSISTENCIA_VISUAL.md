# Estrategia Maestra de Consistencia Visual y Coherencia de Personajes
**Proyecto:** VideoStudio AI (`2026_Proyecto_Videos`)  
**Obra de Referencia:** *Platero y yo* (y futuras series literarias)  
**Fecha:** 11 de Noviembre de 2026  
**Autor:** Antigravity AI / VideoStudio Engineering  

---

## 1. Resumen Ejecutivo y Diagnóstico del Capítulo 1

Al concluir la producción del **Capítulo 1 ("Platero")**, se detectaron fallos críticos de continuidad visual entre las tres escenas:
1. **Inconsistencia Morfológica de Personajes:** Platero aparece con proporciones y tamaños radicalmente diferentes en cada escena (en la escena 1 llena el plano como animal grande; en la escena 2 tiene facciones y tamaño reducidos; en la escena 3 cambia de anatomía). El Narrador ("El Poeta") cambia de edad aparente, altura y fisonomía facial entre la escena 2 y la 3.
2. **Incoherencia de Escenarios y Entornos:** Moguer pasa de un paisaje idílico de acuarela con molinos a un huerto cerrado con diferente iluminación, y luego a una callejuela con un estilo pictórico distinto (menos translúcido, más digital/denso).
3. **Dispersión de Estilo Pictórico:** A pesar de solicitar *"2D traditional storybook watercolor illustration, Studio Ghibli aesthetic"*, el grano del papel, el grosor de la tinta sepia y la saturación de los colores fluctúan ostensiblemente de una imagen a otra.

### Causa Raíz Técnica
- **Generación Text-to-Image Estocástica Pura:** El motor actual (`image_engine.py`) utiliza Pollinations (o llamadas estándar a OpenAI) enviando únicamente cadenas de texto con semillas (*seeds*) aleatorias o pseudo-fijas sin condicionamiento latente.
- **Eliminación de Directivas de Consistencia:** En el código fuente actual, los parámetros `--cref` (referencia de personaje) y `<lora:...>` son eliminados deliberadamente mediante expresiones regulares (`sanitize_image_prompt`) porque las APIs gratuitas no los interpretan.
- **Ausencia de Control de Escala Espacial:** La IA generativa ajusta el sujeto principal para rellenar el lienzo vertical (9:16), perdiendo noción de la escala física real de los objetos y personajes respecto a su entorno.

---

## 2. Comparativa Técnica de Motores Gráficos y Herramientas

Para lograr que los personajes y escenarios sean **100% idénticos durante los más de 100 capítulos de *Platero y yo***, es indispensable migrar a un motor con anclaje visual determinista.

| Motor / Herramienta | Tipo | Consistencia de Personaje | Consistencia de Estilo | Viabilidad de Automatización (API) | Coste Estimado | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Pollinations (FLUX Schnell / Sana)** *(Actual)* | Gratuito | Muy baja (Pura suerte) | Baja (Deriva con cada prompt) | Excelente (HTTP GET simple) | Gratuito ($0) | ❌ **Inviable** para una serie continua. |
| **Midjourney v6.1 / v7 (con `--cref` y `--sref`)** | Pago SaaS / API | **Excelente (90-95%)** | **Excelente (95%)** | Alta (Vía TheGrid API, GoAPI o ImagineAPI) | ~$30-$60/mes (o $0.025/img API) | ⭐ **Recomendado (Vía Rápida / Máximo Arte)** |
| **FLUX.1 [Dev] + Micro-LoRA personalizada** | Pago por uso (Cloud GPU) | **Sobresaliente (98%)** | **Sobresaliente (98%)** | Excelente (Fal.ai, Replicate, Together AI) | ~$0.03/img + $2 entreno LoRA único | 🚀 **Recomendado (Máximo Control y Propiedad)** |
| **ComfyUI + IP-Adapter + ControlNet** | Local / RunPod | **Absoluta (99%)** | **Absoluta (99%)** | Media (Requiere mantener worker o servidor GPU) | ~$0.20/hora GPU o local ($0) | 🛠️ **Ideal para Composición Avanzada** |
| **Ideogram 2.0 / Leonardo.ai** | Pago SaaS / API | Buena (80-85%) | Buena (Paletas fijas) | Buena (API oficial) | ~$12-$30/mes | ⚠️ Buena alternativa, pero menor control anatómico que LoRA/Midjourney. |

---

## 3. Análisis Detallado de las Dos Mejores Alternativas

### Opción 1: Midjourney API Profesional (Vía TheGrid / GoAPI / ImagineAPI)
Midjourney cuenta con el mejor motor artístico para emular acuarela tradicional europea (*storybook watercolor*).
- **Consistencia de Personaje (`--cref`):** Se crea una única imagen canónica de Platero y del Poeta (Model Sheet frontal y lateral). En cada llamada se inyecta `--cref https://.../platero_master.jpg --cw 80` (Character Weight).
- **Consistencia de Estilo (`--sref`):** Se define un Style Reference permanente (`--sref https://.../estilo_acuarela_moguer.jpg`) o un código de estilo `--sref 1849204921`. Todas las imágenes del libro mantendrán exactamente la misma textura de papel, trazos de pincel y saturación lumínica.
- **Implementación:** Sustituir la llamada de Pollinations en `image_engine.py` por una llamada POST a la API de Midjourney (ej. GoAPI o ImagineAPI).

### Opción 2: FLUX.1 [Dev] con Micro-LoRA entrenada en Fal.ai / Replicate
Es la solución industrial por excelencia para producción audiovisual consistente:
- **Entrenamiento de LoRA Canónico:** Se generan 10-15 ilustraciones definitivas de Platero en diferentes poses pero con diseño idéntico. Se entrena un micro-LoRA (tarda 10 minutos en Fal.ai / Replicate con un coste de unos $2).
- **Activación Determinista:** En cada escena, el prompt utiliza el trigger token `platero_donkey_v1 <lora:platero:0.85>`, garantizando que el burro siempre tenga la misma cabeza, orejas, pelaje plateado y complexión.
- **Coste Ultra-eficiente:** Facturación por segundo de inferencia (~$0.025 a $0.04 por imagen vertical en alta definición).

---

## 4. Estrategia Estructural para Todo el Libro (*Pipeline de 5 Pilares*)

Para asegurar la coherencia a lo largo de todos los capítulos del libro, no basta con cambiar el motor; debemos estructurar la producción en un pipeline riguroso:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      1. BANCO DE ACTIVOS CANÓNICOS                     │
│  - Model Sheet de Personajes (Platero, Poeta, Diana, Darbón)          │
│  - Catálogo de Escenarios de Moguer (Calles, Huerto, Colinas, Azotea)  │
│  - Referencia Maestra de Estilo Pictórico (--sref / Style Bible)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                  2. PROMPT CANÓNICO CON REGLAS DE ESCALA               │
│  - 70% del prompt es inmutable (estilo + descripciones anatómicas)     │
│  - 30% restante es contextual (acción dramática + encuadre de cámara)  │
│  - Restricciones de proporción: Platero = 60-65% de la altura del niño │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│              3. GENERACIÓN POR CAPAS O CON MÁSCARA LATENTE             │
│  - Generación de Escenario de Fondo consistente                        │
│  - Integración del Personaje vía IP-Adapter / Inpainting / Rembg       │
│  - Evita que la IA redimensione los personajes según el encuadre       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│            4. AUDITORÍA Y CONTROL DE CALIDAD AUTOMÁTICO/HITL          │
│  - Auditor de similitud perceptual (CLIP / DINOv2 cosine similarity)   │
│  - Pre-aprobación en Telegram antes del render final de vídeo          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                        5. ENSAMBLAJE DE VÍDEO                          │
│  - Transiciones sutiles, animación 2.5D respetando la pintura original │
└────────────────────────────────────────────────────────────────────────┘
```

### Reglas de Escala y Proporciones
1. **Ratio de Altura Fijo:** La cruz de Platero debe situarse siempre a la altura de la cintura/pecho del Poeta niño.
2. **Plano General vs Primer Plano:** Cuando la escena requiera mostrar al burro de cerca, el prompt debe especificar explícitamente *"close-up shot on Platero's face and eyes"* en lugar de permitir que la IA agrande el cuerpo completo dentro del marco vertical.
3. **Perspectiva de la Cámara:** Mantener la cámara a la altura de los ojos de los personajes (evitar vistas cenitales o contrapicados extremos que deformen las proporciones).

---

## 5. Hoja de Ruta de Implementación Inmediata

1. **Aprobación de la Vía Técnica:**
   - Decidir entre **Midjourney API** (vía GoAPI / TheGrid) para máxima belleza artística directa, o **FLUX.1 LoRA en Fal.ai** para control programático puro sin intermediarios.
2. **Generación de los "Golden Masters" (Activos Canónicos):**
   - Aprobar definitivamente la hoja 360° de Platero y de El Poeta.
   - Guardar las URLs de referencia fijas en `proyectos/platero_y_yo/proyecto.json`.
3. **Actualización del Conector en `image_engine.py`:**
   - Incorporar el cliente de la API seleccionada (con soporte real de `--cref`, `--sref` o `image_to_image / LoRA`).
4. **Regeneración y Validación del Capítulo 1:**
   - Volver a generar las 3 escenas del Capítulo 1 aplicando la nueva arquitectura.
   - Validar que Platero y el Poeta mantengan exactamente el mismo aspecto en las colinas, el huerto y las calles de Moguer.
5. **Producción en Masa de los Siguientes Capítulos:**
   - Desplegar el flujo para los capítulos 2 a 138 con total garantía de coherencia.
