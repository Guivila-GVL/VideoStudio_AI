# Scripts Auxiliares y Herramientas CLI

Este directorio contiene herramientas independientes ejecutables desde línea de comandos:

- **`ensamblar_video.py`**: Script independiente basado en MoviePy para unir pistas de audio y secuencias de imágenes en formato vertical 9:16 (1080x1920) con reescalado y recorte inteligente.
  - Uso:
    ```bash
    python scripts/ensamblar_video.py --audio ruta/al/audio.mp3 --imagenes ruta/a/carpeta_fotos --output video_final.mp4
    ```
