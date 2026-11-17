import os
import re
import time
import uuid
import urllib.parse
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

MEDIA_DIR = Path(__file__).resolve().parent.parent / "static" / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
LAST_POLLINATIONS_CALL = 0

def crop_and_resize_to_square(input_path: Path, output_path: Path, target_size: int = 1024):
    """Ajusta una imagen a un lienzo cuadrado 1:1 (1024x1024) sin recortar ni deformar."""
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        w, h = img.size
        if w == target_size and h == target_size:
            img.save(output_path, "JPEG", quality=92)
            return
        scale = min(target_size / w, target_size / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (target_size, target_size), (255, 255, 255))
        x_offset = (target_size - new_w) // 2
        y_offset = (target_size - new_h) // 2
        canvas.paste(resized, (x_offset, y_offset))
        canvas.save(output_path, "JPEG", quality=92)

def crop_and_resize_to_vertical(input_path: Path, output_path: Path, fit_mode: str = "crop"):
    """
    Ajusta una imagen para adaptarse exactamente al formato vertical 9:16 (1080x1920).
    - 'crop': Escala y recorta bordes sobrantes (ideal para fondos y escenas de video que llenan la pantalla).
    - 'contain': Escala manteniendo la imagen 100% visible sin recortar nada, añadiendo márgenes del color del papel (ideal para hojas de modelo de personajes).
    """
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        # Eliminar posible marca de agua en los últimos píxeles inferiores solo en modo 'crop'
        if fit_mode == "crop" and img.height > 100:
            trim_px = max(30, int(img.height * 0.035))
            img = img.crop((0, 0, img.width, img.height - trim_px))

        if fit_mode == "contain":
            # Escalar para que quepa completamente dentro de TARGET_WIDTH x TARGET_HEIGHT
            scale = min(TARGET_WIDTH / img.width, TARGET_HEIGHT / img.height)
            new_w = max(1, int(img.width * scale))
            new_h = max(1, int(img.height * scale))
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Muestrear el color de fondo del borde (papel de acuarela / lienzo blanco)
            sample_color = img.getpixel((min(10, img.width - 1), min(10, img.height - 1)))
            canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), color=sample_color)
            x_offset = (TARGET_WIDTH - new_w) // 2
            y_offset = (TARGET_HEIGHT - new_h) // 2
            canvas.paste(resized, (x_offset, y_offset))
            canvas.save(output_path, "JPEG", quality=95)
            return

        target_ratio = TARGET_WIDTH / TARGET_HEIGHT
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            # Más ancha: escalar según alto y recortar lados
            new_height = TARGET_HEIGHT
            new_width = int(new_height * img_ratio)
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            x_offset = (new_width - TARGET_WIDTH) // 2
            cropped = resized.crop((x_offset, 0, x_offset + TARGET_WIDTH, TARGET_HEIGHT))
        else:
            # Más alta o igual: escalar según ancho y recortar arriba/abajo
            new_width = TARGET_WIDTH
            new_height = int(new_width / img_ratio)
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            y_offset = (new_height - TARGET_HEIGHT) // 2
            cropped = resized.crop((0, y_offset, TARGET_WIDTH, y_offset + TARGET_HEIGHT))

        cropped.save(output_path, "JPEG", quality=92)

def extract_seed_from_prompt(prompt: str) -> Optional[int]:
    """Extrae una semilla determinista combinada a partir de [seed_escenario:...] y [seed_personaje:...] presentes en el prompt."""
    if not prompt:
        return None
    env_seeds = [int(x) for x in re.findall(r"\[seed_escenario:(\d+)\]", prompt, flags=re.IGNORECASE)]
    char_seeds = [int(x) for x in re.findall(r"\[seed_personaje:(\d+)\]", prompt, flags=re.IGNORECASE)]
    if env_seeds and char_seeds:
        return ((env_seeds[0] + char_seeds[0]) % 900000) + 100000
    if char_seeds:
        return char_seeds[0]
    if env_seeds:
        return env_seeds[0]
    return None


def sanitize_image_prompt(prompt: str, max_chars: int = 2000) -> str:
    """Limpia y normaliza un prompt para evitar errores en motores de difusión sin recortar detalles."""
    # Remover directivas técnicas (--cref / --cw / <lora:...> / etiquetas [seed_...] y [Transición...]) del texto plano enviado a APIs estándar
    cleaned_raw = re.sub(r"--cref\s+\S+(?:\s+--cw\s+\d+)?", "", prompt or "", flags=re.IGNORECASE)
    cleaned_raw = re.sub(r"<lora:[^>]+>", "", cleaned_raw, flags=re.IGNORECASE)
    cleaned_raw = re.sub(r"\[(?:seed_personaje|seed_escenario|Transici[óo]n|Escena)[^\]]*\]", "", cleaned_raw, flags=re.IGNORECASE)
    cleaned = " ".join(cleaned_raw.strip().split())
    # Eliminar posibles citas o caracteres problemáticos
    cleaned = cleaned.replace('"', '').replace("'", "")
    if len(cleaned) > max_chars:
        cut = cleaned[:max_chars]
        if "," in cut:
            cleaned = cut.rsplit(",", 1)[0].strip()
        else:
            cleaned = cut.rsplit(" ", 1)[0].strip()
    return cleaned

def resolve_reference_image_info(reference_image: Optional[str]) -> Dict[str, Any]:
    """Resuelve una referencia visual (--cref / imagen_url) tanto si es URL remota como ruta local del proyecto."""
    if not reference_image:
        return {"reference_url": None, "local_path": None, "exists": False}
    clean_ref = reference_image.split("?")[0].strip()
    base_dir = Path(__file__).resolve().parent.parent.parent
    if clean_ref.startswith("/proyectos_data/"):
        rel = clean_ref[len("/proyectos_data/"):]
        local_candidate = base_dir / "proyectos" / rel
        return {
            "reference_url": clean_ref,
            "local_path": str(local_candidate) if local_candidate.exists() else None,
            "exists": local_candidate.exists()
        }
    elif clean_ref.startswith("proyectos/"):
        local_candidate = base_dir / clean_ref
        return {
            "reference_url": f"/proyectos_data/{clean_ref[len('proyectos/'):]}",
            "local_path": str(local_candidate) if local_candidate.exists() else None,
            "exists": local_candidate.exists()
        }
    local_direct = Path(clean_ref)
    if local_direct.exists() and local_direct.is_file():
        return {
            "reference_url": clean_ref,
            "local_path": str(local_direct),
            "exists": True
        }
    return {
        "reference_url": clean_ref,
        "local_path": None,
        "exists": clean_ref.startswith("http")
    }

_REMBG_SESSION = None

def get_rembg_session():
    """Obtiene una sesión cacheada de rembg con el modelo u2netp (ultraligero y rápido)."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            import rembg
            _REMBG_SESSION = rembg.new_session("u2netp")
        except Exception as e:
            print(f"[REMBG] Error inicializando modelo u2netp: {e}")
            _REMBG_SESSION = False
    return _REMBG_SESSION if _REMBG_SESSION is not False else None

def remove_image_background(input_path: Path, output_png_path: Path) -> bool:
    """
    Elimina el fondo de una imagen y la guarda en formato PNG transparente de alta calidad.
    Utiliza el modelo u2netp para recorte limpio de personajes y objetos.
    """
    try:
        import rembg
        session = get_rembg_session()
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            if session:
                nobg_img = rembg.remove(img, session=session)
            else:
                nobg_img = rembg.remove(img)
            
            output_png_path.parent.mkdir(parents=True, exist_ok=True)
            nobg_img.save(output_png_path, format="PNG")
            return True
    except Exception as e:
        print(f"[REMBG] Falló la eliminación de fondo: {e}")
        return False

def _build_fal_image_input(ref_info: Dict[str, Any]) -> Optional[str]:
    """Convierte una referencia local a Data URI base64 o devuelve la URL remota para Fal.ai."""
    if not ref_info or not ref_info.get("exists"):
        return None
    local_path = ref_info.get("local_path")
    if local_path and Path(local_path).exists():
        import base64
        ext = Path(local_path).suffix.lower().lstrip(".")
        mime = "image/png" if ext == "png" else "image/jpeg"
        with open(local_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    ref_url = ref_info.get("reference_url") or ""
    if ref_url.startswith("http"):
        return ref_url
    return None


def _generate_image_fal_flux(
    prompt: str,
    final_path: Path,
    temp_download_path: Path,
    web_url: str,
    ref_info: Dict[str, Any],
    seed: Optional[int] = None,
    fit_mode: str = "crop",
    extra_ref_infos: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Genera una imagen usando Fal.ai (FLUX.1 Dev, FLUX Kontext Pro o Kontext Multi si hay personaje + escenario)."""
    fal_key = os.getenv("FAL_KEY", "").strip()
    if not fal_key:
        raise ValueError("FAL_KEY no está configurada en .env. Configúrala en Ajustes (⚙️) para usar el motor FLUX.")

    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json"
    }

    fal_ref_image = _build_fal_image_input(ref_info)
    fal_ref_list: List[str] = []
    if fal_ref_image:
        fal_ref_list.append(fal_ref_image)
    for ex_info in (extra_ref_infos or []):
        ex_uri = _build_fal_image_input(ex_info)
        if ex_uri and ex_uri not in fal_ref_list:
            fal_ref_list.append(ex_uri)

    aspect = "1:1" if fit_mode == "square" else ("9:16" if fit_mode != "contain" else None)

    if len(fal_ref_list) >= 2 and fit_mode == "crop":
        model_id = "fal-ai/flux-pro/kontext/max/multi"
        multi_prompt = (
            "Combine the exact character appearance(s) from the first reference image(s) into the setting and architecture "
            "of the last environment reference image, rendered in a unified full-bleed 9:16 storybook illustration style "
            f"with a complete painted sky and zero white margins: {prompt}"
        )[:1950]
        payload: Dict[str, Any] = {
            "prompt": multi_prompt,
            "image_urls": fal_ref_list[:4],
            "output_format": "jpeg",
        }
        if aspect:
            payload["aspect_ratio"] = aspect
    elif fal_ref_image:
        model_id = "fal-ai/flux-pro/kontext"
        effective_prompt = prompt
        if fit_mode == "crop":
            effective_prompt = (
                "Keep the exact character design and appearance from the reference image, "
                "placing the character naturally into this full-bleed 9:16 storybook scene "
                f"(replace any plain white background with the described scenery and full sky): {prompt}"
            )[:1950]
        payload = {
            "prompt": effective_prompt,
            "image_url": fal_ref_image,
            "output_format": "jpeg"
        }
        if aspect:
            payload["aspect_ratio"] = aspect
    else:
        model_id = "fal-ai/flux/dev"
        image_size = {"width": 1024, "height": 1024} if fit_mode in ("contain", "square") else {"width": 768, "height": 1344}
        payload = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "output_format": "jpeg"
        }

    if seed is not None:
        payload["seed"] = int(seed)

    endpoint = f"https://fal.run/{model_id}"
    resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200 and model_id == "fal-ai/flux-pro/kontext/max/multi" and fal_ref_image:
        # Fallback a kontext individual si multi no está disponible
        model_id = "fal-ai/flux-pro/kontext"
        fb_payload: Dict[str, Any] = {
            "prompt": (
                "Keep the exact character design and appearance from the reference image, "
                f"placing the character naturally into this full-bleed 9:16 storybook scene: {prompt}"
            )[:1950],
            "image_url": fal_ref_image,
            "output_format": "jpeg",
        }
        if aspect:
            fb_payload["aspect_ratio"] = aspect
        if seed is not None:
            fb_payload["seed"] = int(seed)
        resp = requests.post(f"https://fal.run/{model_id}", headers=headers, json=fb_payload, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"Error en Fal.ai ({model_id}) HTTP {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    images = data.get("images") or []
    if not images or not images[0].get("url"):
        raise RuntimeError(f"Fal.ai ({model_id}) no devolvió URL de imagen: {data}")

    img_resp = requests.get(images[0]["url"], timeout=60)
    if img_resp.status_code != 200:
        raise RuntimeError(f"No se pudo descargar la imagen generada por Fal.ai (HTTP {img_resp.status_code})")

    with open(temp_download_path, "wb") as f:
        f.write(img_resp.content)
    if fit_mode == "square":
        crop_and_resize_to_square(temp_download_path, final_path)
    else:
        crop_and_resize_to_vertical(temp_download_path, final_path, fit_mode=fit_mode)
    if temp_download_path.exists():
        temp_download_path.unlink()

    provider_tag = "fal_flux_kontext_multi" if "multi" in model_id else ("fal_flux_kontext" if fal_ref_image else "fal_flux_dev")
    return {
        "url": web_url,
        "provider": provider_tag,
        "file_path": str(final_path),
        "reference_used": ref_info,
        "references_count": len(fal_ref_list),
        "seed": data.get("seed")
    }


def generate_image(
    prompt: str,
    provider: str = "basic",
    seed: Optional[int] = None,
    reference_image: Optional[str] = None,
    fit_mode: str = "crop",
    reference_images: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Genera una imagen vertical a partir de un prompt utilizando el proveedor seleccionado ('basic' o 'flux').
    Permite inyectar una o varias imágenes de referencia (personajes + escenario de fondo).
    """
    filename = f"img_{uuid.uuid4().hex[:10]}.jpg"
    final_path = MEDIA_DIR / filename
    temp_download_path = MEDIA_DIR / f"temp_{filename}"
    web_url = f"/static/media/{filename}"

    if seed is None:
        seed = extract_seed_from_prompt(prompt)
    clean_prompt = sanitize_image_prompt(prompt, max_chars=2000)

    all_refs = [r for r in (reference_images or []) if r]
    if reference_image and reference_image not in all_refs:
        all_refs.insert(0, reference_image)
    primary_ref = all_refs[0] if all_refs else reference_image
    ref_info = resolve_reference_image_info(primary_ref)
    extra_ref_infos = [resolve_reference_image_info(r) for r in all_refs[1:]]

    provider_norm = (provider or "basic").strip().lower()

    # 0. Motor dedicado FLUX (Fal.ai: FLUX.1 Dev / Kontext Pro / Kontext Multi)
    if provider_norm in ("flux", "fal", "fal_flux", "fal_flux_dev", "fal_flux_kontext"):
        return _generate_image_fal_flux(
            prompt=clean_prompt,
            final_path=final_path,
            temp_download_path=temp_download_path,
            web_url=web_url,
            ref_info=ref_info,
            seed=seed,
            fit_mode=fit_mode,
            extra_ref_infos=extra_ref_infos,
        )

    openai_key = os.getenv("OPENAI_API_KEY")
    pollinations_key = os.getenv("POLLINATIONS_API_KEY")

    # 1. OpenAI Image Generation (gpt-image-1-mini / chatgpt-image-latest)
    if openai_key and openai_key.startswith("sk-"):
        openai_models = ["gpt-image-1-mini", "chatgpt-image-latest", "gpt-image-2"]
        for o_model in openai_models:
            try:
                from openai import OpenAI
                import base64
                client = OpenAI(api_key=openai_key)
                response = client.images.generate(
                    model=o_model,
                    prompt=clean_prompt,
                    size="1024x1536",
                    n=1
                )
                img_data = response.data[0]
                if getattr(img_data, "b64_json", None):
                    with open(temp_download_path, "wb") as f:
                        f.write(base64.b64decode(img_data.b64_json))
                    crop_and_resize_to_vertical(temp_download_path, final_path, fit_mode=fit_mode)
                    if temp_download_path.exists():
                        temp_download_path.unlink()
                    return {"url": web_url, "provider": f"openai_{o_model}", "file_path": str(final_path), "reference_used": ref_info}
                elif getattr(img_data, "url", None):
                    resp = requests.get(img_data.url, timeout=40)
                    if resp.status_code == 200:
                        with open(temp_download_path, "wb") as f:
                            f.write(resp.content)
                        crop_and_resize_to_vertical(temp_download_path, final_path, fit_mode=fit_mode)
                        if temp_download_path.exists():
                            temp_download_path.unlink()
                        return {"url": web_url, "provider": f"openai_{o_model}", "file_path": str(final_path), "reference_used": ref_info}
            except Exception as e:
                print(f"[IMAGE] OpenAI {o_model} no disponible: {e}. Probando siguiente opción...")

    # 2. Generación de respaldo con Pollinations (FLUX / Turbo / Sana)
    global LAST_POLLINATIONS_CALL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    if pollinations_key and pollinations_key.strip():
        headers["Authorization"] = f"Bearer {pollinations_key.strip()}"
        models_to_try = ["flux", "turbo", "sana"]
    else:
        models_to_try = ["flux", "sana"]
        # Respetar de antemano el cooldown de 45s por IP del tier gratuito para evitar errores 402
        elapsed = time.time() - LAST_POLLINATIONS_CALL
        if elapsed < 46:
            wait_needed = int(46 - elapsed)
            print(f"[POLLINATIONS] Respetando ritmo del tier gratuito (esperando {wait_needed}s)...")
            time.sleep(wait_needed)

    errors = []

    for model_name in models_to_try:
        try:
            encoded_prompt = urllib.parse.quote(clean_prompt)
            seed_param = f"&seed={seed}" if seed is not None else ""
            key_param = f"&key={pollinations_key.strip()}" if pollinations_key and pollinations_key.strip() else ""
            nologo_param = "&nologo=true"
            image_param = f"&image={urllib.parse.quote(reference_image)}" if (reference_image and reference_image.startswith("http")) else ""
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&model={model_name}{nologo_param}{seed_param}{image_param}{key_param}"

            resp = requests.get(pollinations_url, headers=headers, timeout=90)

            # Si nos topamos con el límite gratuito (1 imagen cada 45s por IP)
            if resp.status_code in (402, 429):
                retry_wait = 46
                try:
                    import re
                    match = re.search(r"Retry after (\d+)s", resp.text)
                    if match:
                        retry_wait = max(46, int(match.group(1)) + 3)
                except Exception:
                    pass
                print(f"[POLLINATIONS] Límite por IP alcanzado en '{model_name}'. Esperando {retry_wait}s de enfriamiento...")
                time.sleep(retry_wait)
                # Reintentar la misma petición tras el enfriamiento completo
                resp = requests.get(pollinations_url, headers=headers, timeout=90)

            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(temp_download_path, "wb") as f:
                    f.write(resp.content)
                crop_and_resize_to_vertical(temp_download_path, final_path, fit_mode=fit_mode)
                if temp_download_path.exists():
                    temp_download_path.unlink()
                return {"url": web_url, "provider": model_name, "file_path": str(final_path), "reference_used": ref_info}
            else:
                errors.append(f"{model_name}: HTTP {resp.status_code}")
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
        finally:
            LAST_POLLINATIONS_CALL = time.time()

    print(f"[IMAGE] No se pudo generar imagen en Pollinations: {errors}")

    # 3. Lienzo estilizado vertical de respaldo con texto informativo (NUNCA fotos aleatorias de portátiles)
    try:
        from PIL import ImageDraw
        # Crear lienzo artístico oscuro elegante (degradado azul medianoche a pizarra)
        img = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), color=(20, 26, 40))
        draw = ImageDraw.Draw(img)
        # Dibujar marco decorativo
        draw.rectangle([40, 40, TARGET_WIDTH - 40, TARGET_HEIGHT - 40], outline=(60, 80, 120), width=4)
        img.save(final_path, "JPEG", quality=90)
        return {
            "url": web_url,
            "provider": "fallback_placeholder",
            "file_path": str(final_path),
            "reference_used": ref_info,
            "warning": f"Servicio de imagen temporalmente no disponible ({'; '.join(errors)}). Configura una API key en Ajustes."
        }
    except Exception:
        blank = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), color=(25, 30, 45))
        blank.save(final_path, "JPEG")
        return {"url": web_url, "provider": "placeholder", "file_path": str(final_path), "reference_used": ref_info}

def save_uploaded_image(file_bytes: bytes) -> Dict[str, Any]:
    """Guarda una imagen subida manualmente por el usuario y la adapta a 9:16."""
    filename = f"img_upload_{uuid.uuid4().hex[:10]}.jpg"
    final_path = MEDIA_DIR / filename
    temp_path = MEDIA_DIR / f"temp_{filename}"
    web_url = f"/static/media/{filename}"

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    crop_and_resize_to_vertical(temp_path, final_path)
    if temp_path.exists():
        temp_path.unlink()

    return {"url": web_url, "provider": "upload", "file_path": str(final_path)}
