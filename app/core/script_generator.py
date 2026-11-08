import os
import json
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

STYLE_PRESETS = {
    "cinematic": "cinematic lighting, photorealistic 8k, shot on 35mm lens, atmospheric depth of field, dramatic shadows",
    "noir_bw": "black and white film noir photography, dramatic high contrast monochrome, sharp shadows, moody lighting, classic monochrome 35mm film",
    "anime": "anime aesthetic, Makoto Shinkai style, vibrant colors, beautiful sky, high quality anime screencap, trending on Pixiv",
    "ghibli_anime": "Studio Ghibli aesthetic, Hayao Miyazaki hand-drawn anime, painterly backgrounds, warm nostalgic feel, whimsical art",
    "watercolor": "delicate watercolor and ink illustration, soft artistic color washes, storybook illustration, rich paper texture",
    "storybook_kids": "whimsical children's book illustration, vibrant friendly colors, charming storybook character art, soft lighting, family friendly, highly detailed",
    "pixar_3d": "3D animated movie render, Pixar Disney style, soft volumetric subsurface scattering, expressive character facial features, 4k 8k",
    "dark_fantasy": "dark fantasy, hyperdetailed, grimdark aesthetic, ominous lighting, mystical atmosphere, concept art, Unreal Engine 5 render",
    "cyberpunk": "cyberpunk style, neon lights, rainy reflection, high tech dystopian, blade runner aesthetic, volumetric glow",
    "vintage": "vintage 1970s film grain, warm Kodak Portra color tones, nostalgic, retro photography, authentic cinematic texture",
    "comic": "graphic novel comic illustration, bold ink lines, dynamic comic book shading, expressive colors, Frank Miller style"
}

def clean_json_string(raw: str) -> str:
    """Extrae y limpia bloques de código JSON devueltos por LLMs."""
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if match:
        return match.group(1).strip()
    return raw

def format_character_bible(characters: Optional[List[Dict[str, Any]]], fallback_desc: str = "") -> str:
    """Construye las instrucciones de la biblia de personajes para el LLM."""
    if characters and len(characters) > 0:
        lines = ["BIBLIA DE PERSONAJES RECURRENTES DEL PROYECTO:"]
        for c in characters:
            nom = c.get("nombre", "Personaje")
            rol = c.get("rol", "")
            desc = c.get("descripcion_visual", "")
            lines.append(f"- {nom} ({rol}): Rasgos visuales inmutables: {desc}")
        lines.append("\nINSTRUCCIÓN CRUCIAL DE CONSISTENCIA:")
        lines.append("Cada vez que un personaje intervenga en una escena, debes incluir OBLIGATORIAMENTE sus rasgos visuales exactos en el 'prompt_imagen' para que la IA gráfica genere siempre la misma persona.")
        return "\n".join(lines)
    elif fallback_desc.strip():
        return f"Protagonista recurrente de la serie (mantén su apariencia idéntica en cada escena): '{fallback_desc}'."
    else:
        return "Mantén coherencia en el sujeto visual de la historia a lo largo de las escenas."

def format_environment_bible(escenarios: Optional[List[Dict[str, Any]]]) -> str:
    """Construye las instrucciones de la biblia de escenarios recurrentes para el LLM."""
    if escenarios and len(escenarios) > 0:
        lines = ["BIBLIA DE ESCENARIOS Y LOCALIZACIONES RECURRENTES DEL UNIVERSO:"]
        for e in escenarios:
            nom = e.get("nombre", "Lugar")
            tipo = e.get("tipo", "")
            desc = e.get("descripcion_visual", "")
            lines.append(f"- {nom} ({tipo}): Elementos visuales clave: {desc}")
        lines.append("\nINSTRUCCIÓN CRUCIAL DE LOCALIZACIÓN:")
        lines.append("Para cada escena, identifica el escenario recurrente donde transcurre la acción e incluye OBLIGATORIAMENTE sus rasgos visuales exactos en el 'prompt_imagen' para mantener consistencia espacial.")
        return "\n".join(lines)
    return ""

def extract_character_visual_anchor(character: Dict[str, Any]) -> str:
    """
    Extrae la cápsula de identidad física inmutable en inglés de un personaje
    para anclar firmemente la coherencia visual de la escena, sin incluir
    instrucciones de hoja de modelo (turnaround/views/background).
    """
    name = character.get("nombre", "Character").strip()
    tipo = character.get("tipo", "humano").lower().strip()
    desc = character.get("descripcion_visual", "").strip()
    prompt_ret = character.get("prompt_retrato", "").strip()

    if character.get("ancla_visual"):
        return f"{name} ({character['ancla_visual']})"

    lower_name = name.lower()
    lower_desc = desc.lower()

    # Anclas canónicas predefinidas de máxima fidelidad para Platero y Yo
    if "platero" in lower_name or "burro" in lower_desc or "donkey" in lower_desc:
        return f"{name} (small fluffy silver-grey Andalusian donkey with gentle dark crystal black eyes and soft cotton-like coat, quadruped donkey on all four legs, authentic donkey anatomy, no humans)"
    elif "poeta" in lower_name or "narrador" in lower_desc:
        return f"{name} (young contemplative Spanish writer, around 25 years old, sensitive noble face, dark wavy hair, wearing a rustic raw linen shirt, dark wool waistcoat, and wide-brim Andalusian hat)"
    elif "diana" in lower_name:
        return f"{name} (agile slender graceful pure white Andalusian dog resembling a crescent moon, pure white silky coat, lively alert ears, amber eyes, quadruped on all four legs)"
    elif "darbon" in lower_name:
        return f"{name} (large burly elderly village veterinarian with red ruddy face, thick white beard, brown corduroy vest)"
    elif "lord" in lower_name:
        return f"{name} (old noble English greyhound dog, melancholic wise eyes, lean ribs visible beneath an aged brindle grey coat, grey fur around muzzle, quadruped canine on all four legs)"
    elif "canario" in lower_name:
        return f"{name} (tiny singing canary bird, radiant emerald green plumage with fresh lemon-yellow highlights, small shiny seed-like eyes, delicate beak, winged avian bird anatomy)"
    elif "niña chica" in lower_name:
        return f"{name} (petite angelic young Andalusian girl from Moguer, rosy cheeks, braided blonde hair with ribbons, wearing rustic percale dress and white ruffled apron)"
    elif "anilla" in lower_name:
        return f"{name} (Andalusian flamenco dancer woman, warm tanned skin, sparkling dark ember eyes, wavy black hair with comb, colorful ruffled layered flamenco dress and Manila shawl)"

    if prompt_ret:
        # Remover prefijos de hojas de modelo
        cleaned = re.sub(
            r"^(?:Character turnaround model sheet|Turnaround model sheet|Character model sheet|Full body character turnaround model sheet|Character concept art of|Full body character design of)[^,.:]+[,.:]\s*",
            "",
            prompt_ret,
            flags=re.IGNORECASE
        )
        # Remover vistas y fondos
        cleaned = re.sub(
            r"(?:four distinct views|multiple views|front view|three-quarters|rear back view|rear view|isolated on solid|isolated on plain|standing pose).*$",
            "",
            cleaned,
            flags=re.IGNORECASE
        ).strip().strip(",; ")
        if len(cleaned) > 20:
            return f"{name} ({cleaned})"

    if tipo == "animal":
        return f"{name} ({desc[:70]}, standing naturally on all four legs, authentic animal anatomy)"
    else:
        return f"{name} ({desc[:80]}, consistent character appearance)"

def enrich_scene_prompt_with_anchors(
    scene_prompt: str,
    characters_in_scene: Optional[List[str]] = None,
    project_characters: Optional[List[Dict[str, Any]]] = None,
    escenario_clave: Optional[str] = None,
    project_escenarios: Optional[List[Dict[str, Any]]] = None,
    style_prompt: str = ""
) -> str:
    """
    Inyecta los rasgos canónicos inmutables de los personajes que intervienen en la escena
    y el escenario clave, reforzando la coherencia frente a la IA generativa y evitando deriva.
    Si se cambian personajes o escenario, limpia las referencias previas y recompone.
    """
    clean_p = scene_prompt.strip() if scene_prompt else ""

    # 1. Limpiar de clean_p cualquier "set in [Escenario]..." previo para actualizarlo con el nuevo
    clean_p = re.sub(r"\bset in [^,]+:[^,]+(?=,|$)", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")

    # Limpiar sufijos técnicos repetidos para recomponer ordenadamente
    clean_p = re.sub(r"(?:vertical 9:16 portrait composition|masterpiece|no text|no words|no labels).*$", "", clean_p, flags=re.IGNORECASE).strip().strip(",; ")
    if style_prompt:
        clean_p = clean_p.replace(style_prompt, "").strip().strip(",; ")

    anchors = []

    # 2. Anclas de personajes en escena
    if project_characters and characters_in_scene:
        for char_name in characters_in_scene:
            c_match = next(
                (c for c in project_characters if c.get("nombre", "").lower() == char_name.lower() or c.get("id", "").lower() == char_name.lower()),
                None
            )
            if c_match:
                anchor = extract_character_visual_anchor(c_match)
                char_name_lower = c_match.get("nombre", "").lower()
                char_tokens = {t.lower() for t in re.findall(r"\w+", c_match.get("nombre", ""))}
                core_tokens = [w for w in re.findall(r"\w{5,}", anchor.lower()) if w not in ("standing", "character", "natural", "features") and w not in char_tokens]
                already = (char_name_lower in clean_p.lower()) and (any(tok in clean_p.lower() for tok in core_tokens[:3]) if core_tokens else True)
                if not already:
                    anchors.append(anchor)

    # 3. Ancla de escenario clave
    if escenario_clave and project_escenarios:
        e_match = next(
            (e for e in project_escenarios if e.get("nombre", "").lower() == escenario_clave.lower() or e.get("id", "").lower() == escenario_clave.lower()),
            None
        )
        if e_match:
            esc_txt = e_match.get("prompt_escenario") or e_match.get("descripcion_visual") or ""
            clean_esc = re.sub(r"(?:vertical 9:16 background art|masterpiece|empty scene|no people|no words|no text).*$", "", esc_txt, flags=re.IGNORECASE).strip().strip(",; ")
            if clean_esc:
                anchors.append(f"set in {e_match.get('nombre')}: {clean_esc[:95]}")

    # Composición final
    parts = []
    if anchors:
        parts.append(", ".join(anchors))
    if clean_p:
        parts.append(clean_p)
    if style_prompt and style_prompt.lower()[:25] not in clean_p.lower():
        parts.append(style_prompt)
    parts.append("vertical 9:16 portrait composition, masterpiece, no text, no words, no labels")

    final_result = ", ".join([p.strip().strip(",;") for p in parts if p.strip()])
    final_result = re.sub(r"\s*,\s*", ", ", final_result)
    return final_result

def breakdown_storyboard(
    text: str,
    character_desc: str = "",
    characters: Optional[List[Dict[str, Any]]] = None,
    escenarios: Optional[List[Dict[str, Any]]] = None,
    style_key: str = "cinematic",
    style_details: str = "",
    audiencia: str = "",
    ambiente: str = "",
    target_scenes: int = 4,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Desglosa un texto o capítulo en un conjunto ordenado de escenas con
    guion de locución y prompt visual coherente basado en la Biblia de Personajes,
    la Biblia de Escenarios Recurrentes, el público objetivo y la ambientación del universo.
    """
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style
    
    char_clause = format_character_bible(characters, character_desc)
    esc_clause = format_environment_bible(escenarios)
    aud_clause = f"Público objetivo y tono de la serie: {audiencia}. (Adapta el vocabulario, cadencia y tono emocional especialmente para esta audiencia)." if audiencia else ""
    amb_clause = f"Ambiente y universo del libro: {ambiente}. (Sitúa las acciones y escenarios dentro de este mundo)." if ambiente else ""

    system_instruction = f"""Eres un director audiovisual y guionista de vídeos cortos para TikTok, Reels y YouTube Shorts.
Tu trabajo es adaptar el texto del capítulo en exactamente {target_scenes} escenas dinámicas pensadas para formato vertical (9:16).

{aud_clause}
{amb_clause}
{char_clause}
{esc_clause}

Estilo visual global de toda la serie: {style_prompt}.

Reglas de producción:
1. 'narrador': Texto exacto que dirá la voz en off en español para esta escena (15 a 25 palabras). Debe tener gancho y ritmo ágil para retención de audiencia, con tono acorde al público objetivo.
2. 'prompt_imagen': Prompt en INGLÉS detallado para generar la imagen vertical 9:16 de esta escena. Debe describir la composición vertical, la acción, la iluminación, el escenario recurrente según la Biblia de Escenarios y los rasgos físicos EXACTOS de los personajes que aparezcan (según la Biblia de Personajes), rematando con el estilo global ({style_prompt}). No pongas textos escritos dentro de la imagen.
3. 'personajes_en_escena': Lista de nombres de los personajes que aparecen en esta escena (ej: ["Mateo"]).
4. 'escenario_clave': Nombre del escenario recurrente del universo donde ocurre la escena si corresponde, o 'Escenario específico'.
5. 'duracion_estimada': Duración estimada en segundos (ej. 4 a 7 segundos).

Devuelve ÚNICAMENTE un array JSON válido con la siguiente estructura, sin texto adicional ni markdown:
[
  {{
    "id": 1,
    "narrador": "...",
    "prompt_imagen": "...",
    "personajes_en_escena": ["..."],
    "escenario_clave": "...",
    "duracion_estimada": 5
  }}
]
"""

    user_prompt = f"Texto del capítulo a adaptar:\n\n{text}"

    # 1. Intentar con OpenAI si hay clave
    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1800
            )
            raw_content = response.choices[0].message.content or ""
            cleaned = clean_json_string(raw_content)
            scenes = json.loads(cleaned)
            if isinstance(scenes, list) and len(scenes) > 0:
                for i, sc in enumerate(scenes):
                    sc["id"] = i + 1
                    sc.setdefault("narrador", "")
                    sc.setdefault("prompt_imagen", "")
                    sc.setdefault("personajes_en_escena", [])
                    sc.setdefault("duracion_estimada", 5)
                    # Enriquecer e inyectar anclas de personajes y escenarios aprobados
                    sc["prompt_imagen"] = enrich_scene_prompt_with_anchors(
                        scene_prompt=sc["prompt_imagen"],
                        characters_in_scene=sc.get("personajes_en_escena", []),
                        project_characters=characters or [],
                        escenario_clave=sc.get("escenario_clave"),
                        project_escenarios=escenarios or [],
                        style_prompt=style_prompt
                    )
                    sc["audio_url"] = None
                    sc["image_url"] = None
                    sc["duracion_real"] = None
                return scenes
        except Exception as e:
            print(f"[AI] Error llamando a OpenAI: {e}. Activando fallback heurístico.")

    # 2. Fallback Heurístico
    return generate_fallback_storyboard(text, characters, character_desc, style_prompt, target_scenes, ambiente, escenarios)

def generate_fallback_storyboard(
    text: str,
    characters: Optional[List[Dict[str, Any]]],
    character_desc: str,
    style_prompt: str,
    target_scenes: int,
    ambiente: str = "",
    escenarios: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """Generador heurístico de escenas en caso de no contar con API Key activa."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if not sentences:
        sentences = [
            "En un mundo donde cada segundo cuenta, una decisión puede cambiarlo todo.",
            "Los secretos guardados durante años comienzan a salir a la luz.",
            "El camino hacia la verdad nunca estuvo exento de peligros.",
            "Al final, solo aquellos que se atreven a avanzar logran cruzar el umbral."
        ]

    chunk_size = max(1, len(sentences) // target_scenes)
    scenes = []

    for i in range(target_scenes):
        start = i * chunk_size
        end = start + chunk_size if i < target_scenes - 1 else len(sentences)
        scene_sentences = sentences[start:end] if start < len(sentences) else [sentences[-1]]
        narrador = " ".join(scene_sentences)
        
        char_names = [characters[0]["nombre"]] if (characters and len(characters) > 0) else []
        esc_name = escenarios[i % len(escenarios)]["nombre"] if (escenarios and len(escenarios) > 0) else None

        base_prompt = f"Scene {i+1}: action portraying {narrador[:80]}"
        enriched_prompt = enrich_scene_prompt_with_anchors(
            scene_prompt=base_prompt,
            characters_in_scene=char_names,
            project_characters=characters or [],
            escenario_clave=esc_name,
            project_escenarios=escenarios or [],
            style_prompt=style_prompt
        )

        scenes.append({
            "id": i + 1,
            "narrador": narrador,
            "prompt_imagen": enriched_prompt,
            "personajes_en_escena": char_names,
            "escenario_clave": esc_name or "General",
            "duracion_estimada": 5,
            "audio_url": None,
            "image_url": None,
            "duracion_real": None
        })

    return scenes

def rewrite_scene(
    scene_data: Dict[str, Any],
    feedback: str,
    characters: Optional[List[Dict[str, Any]]] = None,
    character_desc: str = "",
    style_key: str = "cinematic",
    style_details: str = "",
    escenarios: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Reescribe una escena específica según las indicaciones de feedback del usuario."""
    openai_key = api_key or os.getenv("OPENAI_API_KEY")
    base_style = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_prompt = f"{base_style}, {style_details.strip()}" if style_details.strip() else base_style
    char_clause = format_character_bible(characters, character_desc)

    if openai_key and openai_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            prompt = f"""Escena actual:
Narrador: {scene_data.get('narrador', '')}
Prompt Imagen: {scene_data.get('prompt_imagen', '')}

Feedback del usuario para mejorarla:
"{feedback}"

{char_clause}
Estilo visual de la serie: {style_prompt}

Devuelve ÚNICAMENTE un JSON con este formato exacto:
{{
  "narrador": "nuevo texto en español (15-25 palabras)",
  "prompt_imagen": "nuevo prompt en inglés con la descripción visual respetando la biblia de personajes y {style_prompt}"
}}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            raw = clean_json_string(response.choices[0].message.content or "")
            updated = json.loads(raw)
            scene_data["narrador"] = updated.get("narrador", scene_data["narrador"])
            new_prompt = updated.get("prompt_imagen", scene_data["prompt_imagen"])
            scene_data["prompt_imagen"] = enrich_scene_prompt_with_anchors(
                scene_prompt=new_prompt,
                characters_in_scene=scene_data.get("personajes_en_escena", []),
                project_characters=characters or [],
                escenario_clave=scene_data.get("escenario_clave"),
                project_escenarios=escenarios or [],
                style_prompt=style_prompt
            )
            scene_data["audio_url"] = None
            scene_data["image_url"] = None
            return scene_data
        except Exception as e:
            print(f"[AI] Error reescribiendo escena: {e}")

    scene_data["narrador"] = f"{scene_data['narrador']} ({feedback})"
    scene_data["prompt_imagen"] = enrich_scene_prompt_with_anchors(
        scene_prompt=f"{scene_data['prompt_imagen']}, {feedback}",
        characters_in_scene=scene_data.get("personajes_en_escena", []),
        project_characters=characters or [],
        style_prompt=style_prompt
    )
    return scene_data
