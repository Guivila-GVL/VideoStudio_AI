import os
import argparse
import sys
try:
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
except ImportError:
    print("Error: Necesitas instalar moviepy. Ejecuta: pip install moviepy")
    sys.exit(1)

def resize_and_crop(clip, target_size=(1080, 1920)):
    """
    Escala la imagen para que cubra la pantalla de 1080x1920 (formato vertical)
    manteniendo la proporción y recortando los bordes sobrantes.
    """
    clip_ratio = clip.w / clip.h
    target_ratio = target_size[0] / target_size[1]
    
    if clip_ratio > target_ratio:
        # La imagen es más ancha de lo que necesitamos: escalamos a la altura y recortamos ancho
        resized_clip = clip.resize(height=target_size[1])
        # Centrar el recorte horizontal
        x_center = resized_clip.w / 2
        return resized_clip.crop(x1=x_center - target_size[0]/2, y1=0, x2=x_center + target_size[0]/2, y2=target_size[1])
    else:
        # La imagen es más alta: escalamos al ancho y recortamos altura
        resized_clip = clip.resize(width=target_size[0])
        y_center = resized_clip.h / 2
        return resized_clip.crop(x1=0, y1=y_center - target_size[1]/2, x2=target_size[0], y2=y_center + target_size[1]/2)

def ensamblar_video(audio_path, imagenes_dir, output_path):
    if not os.path.exists(audio_path):
        print(f"Error: No se encuentra el audio en {audio_path}")
        return

    # 1. Cargar el audio
    audio = AudioFileClip(audio_path)
    duracion_total = audio.duration
    
    # 2. Buscar las imágenes en el directorio (ordenadas alfabéticamente)
    formatos_soportados = ('.png', '.jpg', '.jpeg')
    imagenes = [os.path.join(imagenes_dir, f) for f in os.listdir(imagenes_dir) if f.lower().endswith(formatos_soportados)]
    imagenes.sort()
    
    if not imagenes:
        print(f"Error: No se encontraron imágenes en {imagenes_dir}")
        return
        
    print(f"Encontradas {len(imagenes)} imágenes. Duración del audio: {duracion_total:.2f} segundos.")
    
    # 3. Calcular duración por imagen
    duracion_por_imagen = duracion_total / len(imagenes)
    
    clips = []
    for img_path in imagenes:
        # Cargar imagen y asignar duración
        clip = ImageClip(img_path).set_duration(duracion_por_imagen)
        # Ajustar para formato vertical de Shorts/TikTok (1080x1920)
        clip = resize_and_crop(clip)
        clips.append(clip)
        
    # 4. Unir todos los clips de imagen
    video_final = concatenate_videoclips(clips, method="compose")
    
    # 5. Añadir el audio
    video_final = video_final.set_audio(audio)
    
    # 6. Renderizar el video
    print(f"Generando vídeo en: {output_path}...")
    video_final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    print("¡Vídeo ensamblado con éxito!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensamblador automático de vídeos cortos.")
    parser.add_argument("--audio", required=True, help="Ruta al archivo de audio (.mp3 o .wav)")
    parser.add_argument("--imagenes", required=True, help="Ruta a la carpeta con las imágenes")
    parser.add_argument("--output", default="video_final.mp4", help="Ruta del archivo de vídeo resultante")
    
    args = parser.parse_args()
    ensamblar_video(args.audio, args.imagenes, args.output)
