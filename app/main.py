import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Path as FPath
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from app.core.script_generator import breakdown_storyboard, rewrite_scene, enrich_scene_prompt_with_anchors, STYLE_PRESETS
from app.core.tts_engine import synthesize_speech, list_voices
from app.core.image_engine import generate_image, save_uploaded_image
from app.core.video_renderer import render_final_video
from app.core.project_manager import (
    list_all_projects,
    get_project,
    save_or_update_project,
    upload_project_document,
    save_project_chapter,
    list_project_chapters,
    get_project_chapter,
    list_video_history,
    update_env_settings,
    get_env_settings,
    analyze_book_with_ai,
    generate_character_portrait,
    craft_character_portrait_prompt,
    remove_character_background,
    save_character_portrait_upload,
    delete_character_from_project,
    craft_environment_prompt,
    generate_environment_image,
    save_environment_upload,
    delete_environment_from_project,
    get_project_document_content,
    delete_project,
    delete_project_chapter,
    batch_import_chapters_from_doc,
    sync_project_style,
    delete_project_video,
    recommend_narrator_with_ai,
    slugify
)
from app.core.coherence_auditor import audit_and_heal_characters, audit_and_heal_environments
from app.core.document_parser import parse_document

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MEDIA_DIR = STATIC_DIR / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
PROYECTOS_DIR = BASE_DIR.parent / "proyectos"
PROYECTOS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(
    title="VideoStudio AI - Creador de Vídeos Cortos",
    description="Estudio integral de producción para TikTok, Shorts y Reels con arquitectura de Proyectos/Libros y Human-in-the-Loop.",
    version="2.0.0"
)

# Servir archivos estáticos y datos de proyectos (personajes y multimedia)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/proyectos_data", StaticFiles(directory=str(PROYECTOS_DIR)), name="proyectos_data")

# Modelos Pydantic
class CharacterModel(BaseModel):
    id: Optional[str] = None
    nombre: str
    rol: Optional[str] = ""
    tipo: Optional[str] = "humano"
    descripcion_visual: str
    imagen_url: Optional[str] = None
    prompt_retrato: Optional[str] = None

class EscenarioModel(BaseModel):
    id: Optional[str] = None
    nombre: str
    tipo: Optional[str] = "exterior_urbano"
    descripcion_visual: str = ""
    imagen_url: Optional[str] = None
    prompt_escenario: Optional[str] = None

class ProjectModel(BaseModel):
    id: Optional[str] = None
    titulo: str
    descripcion: Optional[str] = ""
    audiencia: Optional[str] = "Todos los públicos"
    ambiente: Optional[str] = ""
    estilo_visual: str = "cinematic"
    estilo_detalles: Optional[str] = ""
    voz_defecto: str = "openai_fable"
    perfil_narrador: Optional[Dict[str, Any]] = None
    personajes_recurrentes_texto: Optional[str] = ""
    personajes: List[CharacterModel] = []
    escenarios: Optional[List[Dict[str, Any]]] = []

class TestNarratorVoiceRequest(BaseModel):
    voice_id: str
    sample_text: str

class SaveNarratorRequest(BaseModel):
    perfil_narrador: Dict[str, Any]
    voz_defecto: Optional[str] = None

class AnalyzeBookRequest(BaseModel):
    text: Optional[str] = ""
    recurrent_chars_hint: Optional[str] = None

class GeneratePortraitRequest(BaseModel):
    character_id: str
    prompt_override: Optional[str] = None
    sin_fondo: Optional[bool] = True
    formato_vista: Optional[str] = "giro_360"
    descripcion_visual: Optional[str] = None

class OptimizeCharPromptRequest(BaseModel):
    descripcion_visual: Optional[str] = None
    formato_vista: Optional[str] = "giro_360"
    sin_fondo: Optional[bool] = True
    nombre: Optional[str] = None
    rol: Optional[str] = None
    tipo: Optional[str] = None

class SyncStyleRequest(BaseModel):
    estilo_visual: Optional[str] = None
    estilo_detalles: Optional[str] = None
    regenerate_all: Optional[bool] = False

class GenerateEnvironmentRequest(BaseModel):
    environment_id: str
    prompt_override: Optional[str] = None

class StoryboardRequest(BaseModel):
    project_id: Optional[str] = None
    chapter_title: Optional[str] = "Capítulo"
    text: str
    characters: Optional[List[Dict[str, Any]]] = None
    escenarios: Optional[List[Dict[str, Any]]] = None
    character_desc: Optional[str] = ""
    style_key: Optional[str] = "cinematic"
    style_details: Optional[str] = ""
    audiencia: Optional[str] = ""
    ambiente: Optional[str] = ""
    target_scenes: int = 4

class RewriteSceneRequest(BaseModel):
    scene: Dict[str, Any]
    feedback: str
    characters: Optional[List[Dict[str, Any]]] = None
    character_desc: Optional[str] = ""
    style_key: Optional[str] = "cinematic"
    style_details: Optional[str] = ""

class TTSRequest(BaseModel):
    text: str
    voice_key: str = "eleven_george"
    provider: Optional[str] = None
    custom_voice_id: Optional[str] = None

class ImageRequest(BaseModel):
    prompt: str
    provider: str = "flux"
    seed: Optional[int] = None
    reference_image: Optional[str] = None

class InjectAnchorsRequest(BaseModel):
    scene: Dict[str, Any]
    characters: Optional[List[Dict[str, Any]]] = None
    escenarios: Optional[List[Dict[str, Any]]] = None
    style_key: Optional[str] = "cinematic"
    style_details: Optional[str] = ""

class RenderVideoRequest(BaseModel):
    title: str = "Mi Video Short"
    project_id: Optional[str] = None
    chapter_id: Optional[str] = None
    scenes: List[Dict[str, Any]]
    enable_subtitles: bool = True
    enable_ken_burns: bool = True

class SaveChapterRequest(BaseModel):
    project_id: str
    chapter_id: Optional[str] = None
    titulo: str
    texto_original: Optional[str] = ""
    scenes: Optional[List[Dict[str, Any]]] = None
    video_url: Optional[str] = None
    duracion: Optional[float] = None
    origen_tipo: Optional[str] = "manual"
    origen_ref: Optional[str] = ""
    orden: Optional[int] = None

class BatchImportChaptersRequest(BaseModel):
    source: Optional[str] = "pages"  # "pages" o "chapters"
    max_items: Optional[int] = 60


class SettingsRequest(BaseModel):
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    POLLINATIONS_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None

# 1. Rutas Principales
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return index_file.read_text(encoding="utf-8")

@app.get("/api/status")
async def get_system_status():
    openai_key = os.getenv("OPENAI_API_KEY", "")
    eleven_key = os.getenv("ELEVENLABS_API_KEY", "")
    pollinations_key = os.getenv("POLLINATIONS_API_KEY", "")
    return {
        "openai_configured": bool(openai_key and openai_key.startswith("sk-")),
        "elevenlabs_configured": bool(eleven_key),
        "pollinations_configured": bool(pollinations_key),
        "styles_available": list(STYLE_PRESETS.keys()),
        "media_count": len(list(MEDIA_DIR.glob("*.*")))
    }

@app.get("/api/voices")
async def get_voices():
    return list_voices()

# 2. Gestión de Proyectos (Capa 1: Proyecto / Libro)
@app.get("/api/projects")
async def api_list_projects():
    return list_all_projects()

@app.get("/api/projects/{project_id}")
async def api_get_project(project_id: str):
    try:
        return get_project(project_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@app.delete("/api/projects/{project_id}")
async def api_delete_project(project_id: str):
    try:
        ok = delete_project(project_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        return {"success": True, "message": f"Proyecto '{project_id}' eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/documents/content")
async def api_get_project_document_content(project_id: str, filename: Optional[str] = None):
    try:
        res = get_project_document_content(project_id, filename)
        return {"success": True, "document": res}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def api_save_project(req: ProjectModel):
    try:
        saved = save_or_update_project(req.model_dump())
        return {"success": True, "project": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze-book")
async def api_analyze_book(project_id: str, req: AnalyzeBookRequest):
    text_to_use = (req.text or "").strip()
    if not text_to_use:
        try:
            doc_content = get_project_document_content(project_id)
            if doc_content and doc_content.get("full_text"):
                text_to_use = doc_content["full_text"].strip()
        except Exception:
            pass
    if not text_to_use:
        raise HTTPException(status_code=400, detail="El texto del libro o fragmento es obligatorio o debe existir un manuscrito en documentos/.")
    try:
        analysis = analyze_book_with_ai(
            text=text_to_use,
            project_id=project_id,
            recurrent_chars_hint=req.recurrent_chars_hint
        )
        return {"success": True, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/narrator")
def get_project_narrator_endpoint(project_id: str):
    """Devuelve el perfil del narrador, la voz seleccionada y el catálogo categorizado de voces."""
    try:
        project = get_project(project_id)
        narrator = project.get("perfil_narrador", {})
        voices = list_voices()
        return {
            "success": True,
            "perfil_narrador": narrator,
            "voz_defecto": project.get("voz_defecto", narrator.get("voz_recomendada", "openai_fable")),
            "catalog": voices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/narrator/save")
def save_project_narrator_endpoint(project_id: str, req: SaveNarratorRequest):
    """Guarda el perfil del narrador y la voz asignada en proyecto.json."""
    try:
        project = get_project(project_id)
        project["perfil_narrador"] = req.perfil_narrador
        if req.voz_defecto:
            project["voz_defecto"] = req.voz_defecto
        elif req.perfil_narrador.get("voz_recomendada"):
            project["voz_defecto"] = req.perfil_narrador["voz_recomendada"]
        updated = save_or_update_project(project)
        return {
            "success": True,
            "project": updated,
            "perfil_narrador": updated.get("perfil_narrador"),
            "voz_defecto": updated.get("voz_defecto")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/narrator/test-voice")
def test_narrator_voice_endpoint(project_id: str, req: TestNarratorVoiceRequest):
    """Genera en tiempo real una muestra de audio sintetizada para audición del narrador."""
    try:
        sample = req.sample_text.strip()
        if not sample:
            sample = "Platero es pequeño, peludo, suave; tan blando por fuera, que se diría todo de algodón, que no lleva huesos."
        res = synthesize_speech(text=sample, voice_key=req.voice_id)
        return {
            "success": True,
            "url": res["url"],
            "duration": res["duration"],
            "provider": res.get("provider", "openai")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/narrator/recommend-ai")
def recommend_narrator_ai_endpoint(project_id: str):
    """Recomienda con IA el perfil psicológico y la voz idónea según el manuscrito."""
    try:
        narrator = recommend_narrator_with_ai(project_id)
        return {"success": True, "perfil_narrador": narrator}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/sync-style")
async def api_sync_project_style(project_id: str, req: SyncStyleRequest):
    try:
        res = sync_project_style(
            project_id=project_id,
            new_style=req.estilo_visual,
            new_details=req.estilo_detalles,
            regenerate_all=bool(req.regenerate_all)
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/characters/generate-portrait")
async def api_generate_char_portrait(project_id: str, req: GeneratePortraitRequest):
    try:
        res = generate_character_portrait(
            project_id=project_id,
            character_id=req.character_id,
            prompt_override=req.prompt_override,
            sin_fondo=req.sin_fondo if req.sin_fondo is not None else True,
            formato_vista=req.formato_vista or "giro_360",
            descripcion_visual=req.descripcion_visual
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/characters/{character_id}/remove-bg")
async def api_remove_char_bg(project_id: str, character_id: str):
    try:
        res = remove_character_background(project_id, character_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/characters/{character_id}/optimize-prompt")
async def api_optimize_char_prompt(project_id: str, character_id: str, req: Optional[OptimizeCharPromptRequest] = None):
    try:
        proj = get_project(project_id)
        char = next(
            (c for c in proj.get("personajes", []) if c.get("id") == character_id or slugify(c.get("nombre", "")) == character_id),
            None
        )
        if not char:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")

        formato_vista = "giro_360"
        sin_fondo = True

        if req:
            if req.descripcion_visual is not None and req.descripcion_visual.strip():
                char["descripcion_visual"] = req.descripcion_visual.strip()
            if req.nombre is not None and req.nombre.strip():
                char["nombre"] = req.nombre.strip()
            if req.rol is not None:
                char["rol"] = req.rol.strip()
            if req.tipo is not None:
                char["tipo"] = req.tipo.strip().lower()
            if req.formato_vista is not None:
                formato_vista = req.formato_vista
                char["formato_vista"] = formato_vista
            if req.sin_fondo is not None:
                sin_fondo = req.sin_fondo
                char["sin_fondo"] = sin_fondo

        crafted = craft_character_portrait_prompt(
            char,
            proj,
            formato_vista=formato_vista,
            sin_fondo=sin_fondo,
            force_refresh=True
        )
        char["prompt_retrato"] = crafted
        save_or_update_project(proj)
        return {"success": True, "prompt_retrato": crafted, "character": char}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/characters/{character_id}/upload-portrait")
async def api_upload_char_portrait(project_id: str, character_id: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        res = save_character_portrait_upload(project_id, character_id, content)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}/characters/{character_id}")
async def api_delete_character(project_id: str, character_id: str):
    try:
        res = delete_character_from_project(project_id, character_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Escenarios Recurrentes del Entorno
@app.post("/api/projects/{project_id}/environments/generate")
async def api_generate_environment(project_id: str, req: GenerateEnvironmentRequest):
    try:
        res = generate_environment_image(project_id, req.environment_id, req.prompt_override)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/environments/{environment_id}/optimize-prompt")
async def api_optimize_env_prompt(project_id: str, environment_id: str):
    try:
        proj = get_project(project_id)
        esc = next(
            (e for e in proj.get("escenarios", []) if e.get("id") == environment_id or slugify(e.get("nombre", "")) == environment_id),
            None
        )
        if not esc:
            raise HTTPException(status_code=404, detail="Escenario no encontrado")
        crafted = craft_environment_prompt(esc, proj)
        esc["prompt_escenario"] = crafted
        save_or_update_project(proj)
        return {"success": True, "prompt_escenario": crafted, "environment": esc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/environments/{environment_id}/upload")
async def api_upload_env_image(project_id: str, environment_id: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        res = save_environment_upload(project_id, environment_id, content)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/projects/{project_id}/environments/{environment_id}")
async def api_delete_environment(project_id: str, environment_id: str):
    try:
        res = delete_environment_from_project(project_id, environment_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Auditoría y Autocorrección de Coherencia Visual (Personajes y Escenarios)
@app.post("/api/projects/{project_id}/audit-characters")
async def api_audit_characters(project_id: str, auto_heal: bool = Query(True)):
    try:
        res = audit_and_heal_characters(project_id=project_id, auto_heal=auto_heal)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/audit-environments")
async def api_audit_environments(project_id: str, auto_heal: bool = Query(True)):
    try:
        res = audit_and_heal_environments(project_id=project_id, auto_heal=auto_heal)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Documentos (Carga de Word .docx / PDF / TXT)
@app.post("/api/projects/{project_id}/documents/upload")
async def api_upload_project_document(project_id: str, file: UploadFile = File(...)):
    try:
        content = await file.read()
        res = upload_project_document(project_id, content, file.filename)
        return {"success": True, "document": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Capítulos y Storyboard (Capa 2: Episodio / Vídeo)
@app.post("/api/storyboard/generate")
async def api_generate_storyboard(req: StoryboardRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="El texto base es obligatorio.")
    try:
        scenes = breakdown_storyboard(
            text=req.text,
            characters=req.characters,
            escenarios=req.escenarios,
            character_desc=req.character_desc or "",
            style_key=req.style_key or "cinematic",
            style_details=req.style_details or "",
            audiencia=req.audiencia or "",
            ambiente=req.ambiente or "",
            target_scenes=req.target_scenes
        )
        return {"success": True, "scenes": scenes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/storyboard/rewrite-scene")
async def api_rewrite_scene(req: RewriteSceneRequest):
    try:
        updated = rewrite_scene(
            scene_data=req.scene,
            feedback=req.feedback,
            characters=req.characters,
            character_desc=req.character_desc or "",
            style_key=req.style_key or "cinematic",
            style_details=req.style_details or ""
        )
        return {"success": True, "scene": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/storyboard/inject-anchors")
async def api_inject_anchors(req: InjectAnchorsRequest):
    try:
        style_prompt = STYLE_PRESETS.get(req.style_key, STYLE_PRESETS["cinematic"])
        if req.style_details:
            style_prompt = f"{style_prompt}, {req.style_details}"
        enriched = enrich_scene_prompt_with_anchors(
            scene_prompt=req.scene.get("prompt_imagen", ""),
            characters_in_scene=req.scene.get("personajes_en_escena", []),
            project_characters=req.characters or [],
            escenario_clave=req.scene.get("escenario_clave"),
            project_escenarios=req.escenarios or [],
            style_prompt=style_prompt
        )
        req.scene["prompt_imagen"] = enriched
        return {"success": True, "scene": req.scene}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/chapters")
async def api_save_chapter(project_id: str, req: SaveChapterRequest):
    try:
        data = req.model_dump()
        saved = save_project_chapter(project_id, data)
        return {"success": True, "chapter": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/chapters")
async def api_list_chapters(project_id: str):
    return list_project_chapters(project_id)

@app.get("/api/projects/{project_id}/chapters/{chapter_id}")
async def api_get_chapter(project_id: str, chapter_id: str):
    try:
        return get_project_chapter(project_id, chapter_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Capítulo no encontrado")

@app.delete("/api/projects/{project_id}/chapters/{chapter_id}")
async def api_delete_chapter(project_id: str, chapter_id: str):
    try:
        ok = delete_project_chapter(project_id, chapter_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Capítulo no encontrado")
        return {"success": True, "message": f"Capítulo '{chapter_id}' eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/chapters/batch-import")
async def api_batch_import_chapters(project_id: str, req: BatchImportChaptersRequest):
    try:
        chapters = batch_import_chapters_from_doc(project_id, source=req.source, max_items=req.max_items)
        return {"success": True, "chapters": chapters, "count": len(chapters)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 5. Generación Multimedia y Render
@app.post("/api/tts/generate")
async def api_generate_tts(req: TTSRequest):
    try:
        res = synthesize_speech(
            text=req.text,
            voice_key=req.voice_key,
            provider=req.provider,
            custom_voice_id=req.custom_voice_id
        )
        return {"success": True, **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/generate")
async def api_generate_image(req: ImageRequest):
    try:
        res = generate_image(
            prompt=req.prompt,
            provider=req.provider,
            seed=req.seed,
            reference_image=req.reference_image
        )
        return {"success": True, **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/image/upload")
async def api_upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        res = save_uploaded_image(contents)
        return {"success": True, **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video/render")
async def api_render_video(req: RenderVideoRequest):
    try:
        result = render_final_video(
            scenes=req.scenes,
            project_title=req.title,
            enable_subtitles=req.enable_subtitles,
            enable_ken_burns=req.enable_ken_burns,
            project_id=req.project_id,
            chapter_id=req.chapter_id
        )
        # Si pertenece a un proyecto y capítulo, actualizarlo
        if req.project_id and req.chapter_id:
            save_project_chapter(req.project_id, {
                "id": req.chapter_id,
                "titulo": req.title,
                "scenes": req.scenes,
                "video_url": result["video_url"],
                "duracion": result["duration"],
                "peso_mb": result.get("size_mb")
            })

        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/videos/history")
async def api_get_video_history(project_id: Optional[str] = Query(None)):
    return list_video_history(project_id=project_id)

@app.delete("/api/projects/{project_id}/videos/{filename}")
async def api_delete_video(project_id: str, filename: str):
    try:
        res = delete_project_video(project_id, filename)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def api_get_settings():
    try:
        return get_env_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings/save")
async def api_save_settings(req: SettingsRequest):
    settings_dict = {}
    if req.OPENAI_API_KEY is not None:
        settings_dict["OPENAI_API_KEY"] = req.OPENAI_API_KEY
    if req.GEMINI_API_KEY is not None:
        settings_dict["GEMINI_API_KEY"] = req.GEMINI_API_KEY
    if req.ELEVENLABS_API_KEY is not None:
        settings_dict["ELEVENLABS_API_KEY"] = req.ELEVENLABS_API_KEY
    if req.POLLINATIONS_API_KEY is not None:
        settings_dict["POLLINATIONS_API_KEY"] = req.POLLINATIONS_API_KEY
    if req.HUGGINGFACE_API_KEY is not None:
        settings_dict["HUGGINGFACE_API_KEY"] = req.HUGGINGFACE_API_KEY

    try:
        res = update_env_settings(settings_dict)
        return {"success": True, "settings": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
