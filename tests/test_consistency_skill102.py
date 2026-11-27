"""Tests de la integración en producción de la Skill #102 en el Paso 2 (Consistencia visual)."""
from app.core.consistency_reference_skill import (
    SHADOW_PRESERVATION_CLAUSE,
    apply_shadow_preservation,
    build_six_view_sheet_prompt,
    is_low_light_text,
)
from app.core.project_manager import craft_character_portrait_prompt, craft_environment_prompt
from app.core.script_generator import enrich_scene_prompt_with_anchors


def test_low_light_detection_and_idempotence():
    assert is_low_light_text("camino al anochecer")
    assert not is_low_light_text("bright sunny plaza")
    p = apply_shadow_preservation("a path at night")
    assert SHADOW_PRESERVATION_CLAUSE in p
    assert apply_shadow_preservation(p) == p
    assert apply_shadow_preservation("sunny plaza") == "sunny plaza"


def test_six_view_sheet_prompt():
    p = build_six_view_sheet_prompt("Platero: grey donkey", "watercolor")
    assert "#FFFFFF" in p and "front view" in p and "rear back" in p and "no dividing border lines" in p


def test_enrich_scene_prompt_night_gets_shadow_rule():
    out = enrich_scene_prompt_with_anchors("a boy walks at night under the moon")
    assert "preserve shadow details" in out
    day = enrich_scene_prompt_with_anchors("a boy walks in a sunny plaza")
    assert "preserve shadow details" not in day


def test_environment_prompt_night_and_day():
    night = craft_environment_prompt({"nombre": "Camino", "descripcion_visual": "camino de noche con luna"}, {})
    assert "preserve shadow details" in night
    day = craft_environment_prompt({"nombre": "Plaza", "descripcion_visual": "plaza soleada"}, {})
    assert "preserve shadow details" not in day


def test_character_six_views_optin_and_default_unchanged():
    ch = {"nombre": "Platero", "descripcion_visual": "burro plateado", "tipo": "animal"}
    six = craft_character_portrait_prompt(ch, {}, formato_vista="seis_vistas")
    assert "#FFFFFF" in six and "front view" in six
    default = craft_character_portrait_prompt(ch, {})
    assert "Three-quarter angle" in default
