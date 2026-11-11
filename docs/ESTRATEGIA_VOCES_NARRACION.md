# Estrategia de Selección de Voces y Narración en Español Nativo 🎙️

**Proyecto:** VideoStudio AI (`2026_Proyecto_Videos`)  
**Fecha:** 11 de Noviembre de 2026  
**Autor:** Antigravity (Google DeepMind Agentic Coding)  
**Estado:** Implementado y Verificado en Producción  
**Referencia OneNote:** `Desarrollo Proyectos` -> `VideoStudio AI` -> `04. Análisis y Estrategia de Selección de Voces y Narración en Español Nativo`

---

## 1. Diagnóstico del Problema: ¿Por qué todas las opciones sonaban en inglés?

Durante la producción narrativa de obras literarias como *Platero y yo* (donde el narrador es un muchacho lírico de 12-14 años que dialoga con su burrito), el usuario reportó que:
> *"Todos los personajes que me da las opciones para la narración se nota que tienen acento inglés, aunque sea de una persona, de un niño de 12 años... Se nota que no son españoles. ¿Cómo podemos hacer tener más opciones? ¿Qué es lo que deberíamos plantear ahí? Quizá tener algo de pago para esta aplicación..."*

### Causa Raíz Técnica
Tras analizar el motor `tts_engine.py` y consultar las APIs de síntesis en tiempo real, se identificaron tres causas concurrentes:

1. **Arquitectura Fonética de OpenAI TTS (`tts-1` / `tts-1-hd`):**
   - Las 6 voces base de OpenAI (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`) están entrenadas casi exclusivamente con grabaciones de actores estadounidenses en lengua inglesa.
   - Cuando el modelo sintetiza texto en español, impone la prosodia, entonación, aspiración de consonantes oclusivas ($p, t, k$) y vocales diptongadas propias del inglés americano. Aunque entienda las palabras, suena indefectiblemente a un extranjero angloparlante hablando español ("guiri").

2. **Personas Anglosajonas en ElevenLabs Multilingual v2:**
   - En el catálogo por defecto figuraban voces como *Liam* (joven estadounidense), *Will* (joven estadounidense), *George* (narrador británico de 55 años), *Charlie* (australiano) y *Sarah* (americana).
   - El modelo `eleven_multilingual_v2` está diseñado expresamente para preservar el timbre y el acento nativo del actor original. Por tanto, cuando *Liam* o *George* leen texto en español, reproducen deliberadamente el acento anglosajón nativo del actor.

3. **Bloqueo de la Librería de Voces en Cuentas Gratuitas de ElevenLabs (HTTP 402):**
   - ElevenLabs cuenta con voces comunitarias nativas de España magníficas (ej. *Tom - Joven Español*, *Pedro Alvera*, *Álvaro Sereno*).
   - Sin embargo, una prueba técnica con la API de ElevenLabs devolvió:
     ```json
     {"detail":{"type":"payment_required","code":"paid_plan_required","message":"Free users cannot use library voices via the API. Please upgrade your subscription to use this voice.","status":"payment_required"}}
     ```
   - Las cuentas gratuitas de ElevenLabs tienen **bloqueado el uso de voces de librería vía API**. Solo permiten invocar las voces por defecto anglosajonas o voces clonadas dentro de la propia cuenta.

---

## 2. Comparativa de Soluciones y Modelos de Coste

Para garantizar narraciones con acento 100% nativo de España (peninsular) y adaptables a timbres de niños o adolescentes, se definen cuatro vías de actuación:

| Solución | Calidad Acústica | Acento | Disponibilidad / Coste | Adecuación para Narrador Joven (12-14a) |
| :--- | :--- | :--- | :--- | :--- |
| **Microsoft Edge-TTS Neural** *(Implementada)* | ⭐⭐⭐⭐ (Alta - Azure) | 🇪🇸 100% Castellano Nativo | **0€ (Gratuito, sin API Key, sin límites)** | **Excelente:** Modulación de `pitch: +12Hz` y `rate: -3%` crea timbre juvenil natural. |
| **ElevenLabs Voice Cloning** | ⭐⭐⭐⭐⭐ (Hiperrealista) | 🇪🇸 100% Español Nativo | **0€ (3 slots gratuitos en cuenta actual)** | **Excelente:** Requiere subir 1-2 min de audio de un actor/niño español al panel web. |
| **ElevenLabs Plan de Pago (Starter $5/m)** | ⭐⭐⭐⭐⭐ (Hiperrealista) | 🇪🇸 100% Castellano Nativo | **$5/mes (~30.000 caracteres)** | **Excelente:** Desbloquea la librería comunitaria con voces juveniles nativas (ej: *Tom*). |
| **OpenAI TTS (`tts-1`)** | ⭐⭐⭐ (Media) | 🇺🇸 Anglosajón foráneo | Pago por token ($0.015 / 1K car.) | **Inadecuada:** No posee voces con fonética castellana nativa. |

---

## 3. Implementación Realizada en VideoStudio AI

### 3.1. Integración de Microsoft Edge-TTS en `tts_engine.py`
Se ha añadido soporte de primer nivel para síntesis neural de Microsoft Edge-TTS con ejecución concurrente segura en hilo independiente:
- **`edge_alvaro_joven`:** Voz `es-ES-AlvaroNeural` modulada con `pitch="+12Hz"` y `rate="-3%"`. Genera un muchacho de 12-14 años lírico, tierno y reflexivo, perfecto para el narrador de *Platero y yo*.
- **`edge_alvaro`:** Voz `es-ES-AlvaroNeural` estándar (`pitch="+0Hz"`, `rate="+0%"`), ideal para narradores adultos y documentales.
- **`edge_elvira`:** Voz `es-ES-ElviraNeural`, timbre femenino cálido peninsular para cuentos y relatos tiernos.
- **`edge_ximena`:** Voz `es-ES-XimenaNeural`, timbre juvenil dinámico.

### 3.2. Activación de Voz Clonada Española en ElevenLabs
- Se ha identificado y activado en el catálogo la voz `eleven_ZtGDHPi9jPEEuRGCBOY5` (*Narración Clásica ES*), configurada en la cuenta personal del usuario y validada con retorno HTTP 200 vía API sin coste de librería.

### 3.3. Reestructuración de la Interfaz y Pastillas de Audición Rápida
- **Dropdown Categorizado:** Se ha creado una categoría destacada en la cabecera:  
  `🇪🇸 Voces Nativas en Español (España Peninsular - Sin Acento Inglés)`  
  separada explícitamente de las voces multilingües anglosajonas.
- **Pastillas de 1 Clic (`index.html`):** Los botones de audición rápida ahora permiten comparar al instante:
  1. `🇪🇸 Álvaro Joven (12-14a Nativo)` (Edge-TTS)
  2. `🇪🇸 Álvaro (Castellano)` (Edge-TTS)
  3. `🇪🇸 Elvira (España)` (Edge-TTS)
  4. `🎙️ Voz Narración (ElevenLabs)` (Voz de cuenta personal)
  5. `🌐 Fable (OpenAI)` (Voz con fonética anglosajona)

### 3.4. Actualización del Recomendador IA y Configuración de Proyectos
- En `project_manager.py` (`recommend_narrator_with_ai`), se sustituyó la recomendación estocástica de `openai_fable` por `edge_alvaro_joven` para *Platero y yo*, asignándole tono lírico y timbre de 12-14 años en español peninsular nativo.
- El archivo `proyectos/platero_y_yo/proyecto.json` se actualizó fijando `edge_alvaro_joven` como voz por defecto.

---

## 4. Guía para el Usuario: Cómo Añadir Más Voces de Niño/Joven en ElevenLabs

Si el usuario desea contar con voces hiperrealistas adicionales en ElevenLabs:

### Opción A (100% Gratuita - Clonación Instantánea):
1. Entrar en [elevenlabs.io](https://elevenlabs.io) con la cuenta vinculada en el archivo `.env`.
2. Ir a **Voices** -> **Add Voice** -> **Instant Voice Cloning**.
3. Grabar o subir un clip de 1 a 3 minutos de un niño o actor de voz hablando en español de España sin ruido de fondo.
4. Ponerle de nombre, por ejemplo, `Niño Moguer Español`.
5. Al guardar, VideoStudio AI detectará automáticamente la nueva voz en `/api/voices` y estará disponible en el desplegable sin necesidad de ningún plan de pago.

### Opción B (Plan de Pago - Desbloqueo de Voice Library):
1. Contratar el plan **Starter** de ElevenLabs ($5/mes).
2. Podrá añadir con un solo clic a su biblioteca las voces comunitarias peninsulares más aclamadas:
   - `B0r3rOF9WOwQ4BBKhRWO` (*Tom - Calm & Clarity*): Joven narrador de España.
   - `Zn20oa3A71BRv09u2T0m` (*Pedro Alvera*): Cuentacuentos peninsular.
   - `Fm7BveXW2pOo1gtPxYfM` (*Álvaro Sereno*): Barítono castellano.
3. Estas voces responderán de inmediato en la API sin el error 402.

---

## 5. Verificación Técnica Ejecutada

1. **Prueba Unitaria de Síntesis:**
   - Síntesis de muestra de *Platero y yo* con `edge_alvaro_joven`: `audio_e635f3c206.mp3`, duración real 6.72s calculada con ffprobe, sin errores.
2. **Prueba de Endpoint REST:**
   - `POST /api/projects/platero_y_yo/narrator/test-voice` ejecutado con éxito (Status 200).
3. **Batería de Pruebas de Integración:**
   - Todos los 12 pasos de `tests/test_api.py` verificados al 100%.
