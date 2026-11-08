import os, json
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

with open('proyectos/platero_y_yo/proyecto.json', 'r', encoding='utf-8') as f:
    proj = json.load(f)

system_instruction = """You are a master concept artist and prompt engineer for an animation studio.
Your task is to craft an exceptional image generation prompt in 100% ENGLISH (around 350-500 characters) for a character turnaround model sheet.

CRITICAL INSTRUCTIONS:
1. PURE ENGLISH: Translate all character traits and nuances into vivid, descriptive English. Never output Spanish words.
2. SPECIES & ANATOMY FIRST:
   - For dogs/canines: MUST explicitly state 'An old noble English greyhound dog named [Name]' or similar. Must specify 'standing naturally on all four legs, quadruped canine anatomy, no humans'.
   - For birds/avians: MUST explicitly state 'A small canary bird named [Name], perched naturally, avian bird anatomy with wings, feathers, and tiny beak, no humans, no quadrupeds'.
   - For other animals: Must specify 'standing naturally on all four hooves/paws, authentic animal anatomy, no humans'.
   - For humans: Must specify 'Full body character design of [Name], [age/profession], full standing pose head to toe'.
3. 4-VIEW MODEL SHEET STANDARD (DARBÓN BASELINE):
   - MUST include: 'four distinct full-body views: full front view, side profile view, three-quarters angle, and rear back view'.
4. ARTISTIC PATTERN (WATERCOLOR STORYBOOK ILLUSTRATION):
   - MUST include: 'delicate poetic watercolor and ink storybook illustration, soft translucent color washes, visible paper grain texture, subtle sepia pencil outlines, warm Mediterranean sunlight'.
5. ISOLATION & ZERO TEXT:
   - MUST include: 'isolated on solid plain pure white background, no text, no words, no labels, no title, no arrows, vertical 9:16, masterpiece character model sheet'.

Output ONLY the prompt text, without quotes or explanations."""

results = {}
for char_id in ['lord', 'canario_verde', 'la_nina_chica', 'anilla_la_hungara']:
    char = next(c for c in proj['personajes'] if c['id'] == char_id)
    user_content = f"""Character Name: {char['nombre']}
Role: {char['rol']}
Type: {char['tipo']}
Description: {char['descripcion_visual']}
Project Style: {proj.get('estilo_visual')} - {proj.get('estilo_detalles')}"""
    
    resp = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': user_content}
        ],
        temperature=0.2
    )
    prompt = resp.choices[0].message.content.strip().strip('"\'')
    results[char_id] = prompt
    print(f"=== {char_id} ({len(prompt)} chars) ===\n{prompt}\n")

with open('scratch/generated_prompts.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
