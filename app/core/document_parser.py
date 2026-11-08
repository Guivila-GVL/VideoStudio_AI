import io
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

def extract_pages_and_text(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Extrae tanto el texto continuo como el desglose estructurado página a página
    de un archivo PDF (.pdf), Word (.docx) o Texto plano (.txt, .md).
    """
    ext = Path(filename).suffix.lower()
    pages: List[Dict[str, Any]] = []

    if ext == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(reader.pages):
            p_text = (page.extract_text() or "").strip()
            w_count = len(p_text.split())

            # Detectar una primera línea o título representativo de la página
            lines = [
                l.strip() for l in p_text.split("\n") 
                if l.strip() and len(l.strip()) > 3 
                and not l.strip().isdigit() 
                and not l.strip().startswith("-")
                and not l.strip().startswith("?")
            ]
            first_line = lines[0][:50].strip() if lines else f"Página {idx + 1}"
            first_line = re.sub(r"\s+", " ", first_line)

            pages.append({
                "page_number": idx + 1,
                "title": f"Pág. {idx + 1}: {first_line}",
                "short_title": first_line,
                "text": p_text,
                "word_count": w_count
            })
        full_text = "\n\n".join([p["text"] for p in pages if p["text"]])
        return pages, full_text

    elif ext == ".docx":
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        # Segmentar en páginas lógicas de ~250-300 palabras ideales para episodios
        current_chunk: List[str] = []
        curr_words = 0
        p_num = 1
        for par in paragraphs:
            pw = len(par.split())
            current_chunk.append(par)
            curr_words += pw
            if curr_words >= 250:
                p_text = "\n\n".join(current_chunk)
                first_line = current_chunk[0][:50]
                pages.append({
                    "page_number": p_num,
                    "title": f"Pág. {p_num}: {first_line}",
                    "short_title": first_line,
                    "text": p_text,
                    "word_count": curr_words
                })
                p_num += 1
                current_chunk = []
                curr_words = 0

        if current_chunk:
            p_text = "\n\n".join(current_chunk)
            pages.append({
                "page_number": p_num,
                "title": f"Pág. {p_num}: {current_chunk[0][:50]}",
                "short_title": current_chunk[0][:50],
                "text": p_text,
                "word_count": curr_words
            })

        full_text = "\n\n".join(paragraphs)
        return pages, full_text

    elif ext in (".txt", ".md"):
        try:
            raw = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw = file_bytes.decode("latin-1", errors="ignore")

        paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]
        current_chunk = []
        curr_words = 0
        p_num = 1
        for par in paragraphs:
            pw = len(par.split())
            current_chunk.append(par)
            curr_words += pw
            if curr_words >= 250:
                p_text = "\n\n".join(current_chunk)
                first_line = current_chunk[0][:50]
                pages.append({
                    "page_number": p_num,
                    "title": f"Pág. {p_num}: {first_line}",
                    "short_title": first_line,
                    "text": p_text,
                    "word_count": curr_words
                })
                p_num += 1
                current_chunk = []
                curr_words = 0

        if current_chunk:
            p_text = "\n\n".join(current_chunk)
            pages.append({
                "page_number": p_num,
                "title": f"Pág. {p_num}: {current_chunk[0][:50]}",
                "short_title": current_chunk[0][:50],
                "text": p_text,
                "word_count": curr_words
            })

        if not pages and raw.strip():
            pages.append({
                "page_number": 1,
                "title": "Pág. 1: Texto Completo",
                "short_title": "Texto Completo",
                "text": raw.strip(),
                "word_count": len(raw.split())
            })

        return pages, raw

    else:
        raise ValueError(f"Formato no soportado: '{ext}'. Utiliza archivos .docx, .pdf, .txt o .md.")

def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """Extrae el texto completo de un archivo (mantiene compatibilidad hacia atrás)."""
    _, text = extract_pages_and_text(file_bytes, filename)
    return text

def detect_chapters(full_text: str) -> List[Dict[str, Any]]:
    """
    Analiza el texto de un libro o manuscrito y detecta divisiones
    por capítulos o secciones lógicas mediante múltiples estrategias:
    1. Palabras clave explícitas (Capítulo, Chapter, Acto, Escena, etc.)
    2. Números romanos o arábigos con título (ej: 'I. Platero', '1 - El Comienzo')
    3. Cabeceras en mayúsculas destacadas
    4. Segmentación inteligente en episodios lógicos de ~300-500 palabras si el texto es continuo.
    """
    clean_text = full_text.strip()
    if not clean_text:
        return []

    # Estrategia 1: Patrones explícitos y números romanos/ordinales
    chapter_pattern = (
        r"(?im)^(?:(?:cap[íi]tulo|chapter|parte|acto|cuadro|escena|episodio)\s+(?:\d+|[ivxlcdm]+)"
        r"|(?:[ivxlcdm]{1,8}\.?\s+[-–—]?\s*[A-ZÁÉÍÓÚÑa-záéíóúñ][^\n]{2,60})"
        r"|(?:\d{1,3}\.?\s+[-–—]\s*[A-ZÁÉÍÓÚÑa-záéíóúñ][^\n]{2,60}))"
        r"(?:[:\.\s\-]+[^\n]*)?"
    )
    
    matches = list(re.finditer(chapter_pattern, clean_text))

    # Si encontramos al menos 2 divisiones claras
    if len(matches) >= 2:
        chapters = []
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            title = re.sub(r"\s+", " ", title)
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
            
            content = clean_text[start:end].strip()
            lines = content.split("\n", 1)
            body = lines[1].strip() if len(lines) > 1 else lines[0].strip()
            
            words = len(body.split())
            if words > 10:  # Ignorar capítulos vacíos
                chapters.append({
                    "index": len(chapters) + 1,
                    "title": title,
                    "text": body,
                    "word_count": words
                })
        if len(chapters) >= 2:
            return chapters

    # Estrategia 2: Segmentación inteligente en episodios lógicos por párrafos
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if len(p.strip()) > 30]
    total_words = len(clean_text.split())

    if total_words > 400 and len(paragraphs) >= 2:
        chapters = []
        current_chunk = []
        current_words = 0
        part_idx = 1

        for p in paragraphs:
            p_words = len(p.split())
            current_chunk.append(p)
            current_words += p_words

            if current_words >= 250:
                body = "\n\n".join(current_chunk)
                first_sentence = p.split(".")[0].strip()[:40]
                chapters.append({
                    "index": part_idx,
                    "title": f"Episodio {part_idx}: {first_sentence}...",
                    "text": body,
                    "word_count": current_words
                })
                part_idx += 1
                current_chunk = []
                current_words = 0

        if current_chunk:
            body = "\n\n".join(current_chunk)
            if chapters and current_words < 120:
                chapters[-1]["text"] += "\n\n" + body
                chapters[-1]["word_count"] += current_words
            else:
                chapters.append({
                    "index": part_idx,
                    "title": f"Episodio {part_idx}: Conclusión",
                    "text": body,
                    "word_count": current_words
                })

        if len(chapters) >= 2:
            return chapters

    # Estrategia 3: Fallback a documento completo
    return [{
        "index": 1,
        "title": "Texto Completo",
        "text": clean_text,
        "word_count": total_words
    }]

def parse_document(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Procesa un documento subido, extrae el texto, el desglose página a página y los capítulos."""
    pages, text = extract_pages_and_text(file_bytes, filename)
    words = len(text.split())
    chapters = detect_chapters(text)

    return {
        "filename": filename,
        "total_words": words,
        "total_characters": len(text),
        "total_pages": len(pages),
        "pages": pages,
        "full_text": text,
        "chapters_count": len(chapters),
        "chapters": chapters
    }
