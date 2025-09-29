import sys, os, re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import OpenAI
from retriever.retriever import WineRetriever

client = OpenAI(
    api_key="sk-efc9807bf70b4426a1ec62e790cb9697",
    base_url="https://api.deepseek.com"
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
retriever = WineRetriever(
    index_path=os.path.join(project_root, "data", "processed", "wine_embeddings.index"),
    docs_path=os.path.join(project_root, "data", "processed", "wine_docs.pkl"),
)

# ---------- Helpers to parse a single big "document" string ----------
_rx_cache = {}
_URL_CHUNKS_RX = re.compile(r'https?://.*?(?=https?://|$)', re.I)
def _re(pattern, flags=re.I):
    # tiny cache so we don't recompile the same regex 1,000 times
    key = (pattern, flags)
    if key not in _rx_cache:
        _rx_cache[key] = re.compile(pattern, flags)
    return _rx_cache[key]

def _extract_line(key, text):
    """Extract a single-line 'Key: value' from the document."""
    m = _re(rf"{re.escape(key)}:\s*(.+?)(?:\r?\n|$)").search(text or "")
    return m.group(1).strip() if m else ""

def _extract_url(key, text):
    m = _re(rf"{re.escape(key)}:\s*(https?://\S+)").search(text or "")
    return m.group(1).strip() if m else ""

def _extract_title(text):
    """
    Extract just the wine name, trimming off region and extra details.
    """
    # Try "Wine: NAME from ..." format
    m = _re(r"Wine:\s*(.+?)\s+from\b").search(text or "")
    if m:
        return m.group(1).strip()

    # If it starts like "Nicolas Brobergière Brut from ..." remove 'from' and later
    m = _re(r"^(.+?)\s+from\b").search(text or "")
    if m:
        return m.group(1).strip()

    # Fallback: cut at first period
    m = _re(r"^(.+?)\.").search(text or "")
    if m:
        return m.group(1).strip()

    return text.strip() if text else ""

def _cleanup_price(p):
    if not p: 
        return ""
    p = str(p).strip()
    # tolerate "79.0", "79 SEK", "Price: 79.0", etc.
    p = p.replace("Price:", "").strip()
    return p

def _find_url_chunks(text: str):
    if not text:
        return []
    # split into http-chunks, then further split by common delimiters
    chunks = _URL_CHUNKS_RX.findall(str(text))
    parts = []
    for ch in chunks:
        parts.extend(re.split(r'[|\s,]+', ch))
    # basic cleanup
    cleaned = []
    for p in parts:
        if not p:
            continue
        p = p.strip(' \t\r\n),.;\'"')
        if p.startswith('http'):
            cleaned.append(p)
    return cleaned

def _pick_best_image_url(text: str):
    """
    Return the best single image URL from a messy field: prefer jpg/jpeg/png/webp.
    """
    candidates = _find_url_chunks(text)
    if not candidates:
        return ""
    preferred = ('.jpg', '.jpeg', '.png', '.webp')
    for ext in preferred:
        for u in candidates:
            if u.lower().endswith(ext):
                return u
    # fallback: first http chunk
    return candidates[0]

def _pick_first_url(text: str):
    """ For non-image links (buy/permalink), just take the first valid http URL. """
    candidates = _find_url_chunks(text)
    return candidates[0] if candidates else ""

def normalize_doc(doc):
    if isinstance(doc, dict):
        txt = (doc.get("document") or "").strip()

        # Title – keep your existing title cleanup logic …
        raw_title = (doc.get("Title") or "").strip()
        title = _extract_title(raw_title) if raw_title else _extract_title(txt)
        if not title:
            title = "Unnamed wine"

        # NEW: sanitize image + permalink
        raw_img = doc.get("Image_URL") or doc.get("Image") or _extract_line("Image URL", txt)
        raw_link = doc.get("Permalink") or _extract_line("Buy here", txt)

        return {
            "title": title,
            "region": doc.get("Region") or _extract_line("Region", txt),
            "type": doc.get("Type") or _extract_line("Type", txt),
            "aromas": (
                doc.get("Aromas")
                or doc.get("Flavors")
                or _extract_line("Aromas", txt)
                or _extract_line("Flavors", txt)
            ),
            "pairing": (
                doc.get("Food_Pairings")
                or doc.get("Pairing")
                or _extract_line("Food pairings", txt)
                or _extract_line("Pairings", txt)
            ),
            "alcohol": doc.get("Alcohol") or _extract_line("Alcohol", txt),
            "price": _cleanup_price(doc.get("Price") or _extract_line("Price", txt)),
            "profile": (
                doc.get("Profile") or doc.get("Description") or _extract_line("Description", txt)
            ),
            "image": _pick_best_image_url(raw_img),
            "permalink": _pick_first_url(raw_link),
        }

    # string document case
    text = doc or ""
    return {
        "title": _extract_title(text) or "Unnamed wine",
        "region": _extract_line("Region", text),
        "type": _extract_line("Type", text),
        "aromas": _extract_line("Aromas", text) or _extract_line("Flavors", text),
        "pairing": _extract_line("Food pairings", text) or _extract_line("Pairings", text),
        "alcohol": _extract_line("Alcohol", text),
        "price": _cleanup_price(_extract_line("Price", text)),
        "profile": _extract_line("Description", text),
        "image": _pick_best_image_url(_extract_line("Image URL", text)),
        "permalink": _pick_first_url(_extract_line("Buy here", text)),
    }


def clean_markdown(text: str) -> str:
    """
    Normalize LLM markdown to a clean chat style:
    - Turn "- **Wine** - details" or "1. **Wine** - details" into "• Wine — details"
    - Strip remaining **bold**/*italic* everywhere
    - Convert ordered lists to bullets
    - Keep headings as plain text lines
    """
    if not text:
        return ""

    lines = [ln.rstrip() for ln in text.splitlines()]

    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append("")
            continue

        # 1) Headings: "### Title" / "## Title" / "# Title"  -> plain line "Title"
        m = re.match(r"^\s*#{1,6}\s*(.+)$", s)
        if m:
            out.append(m.group(1).strip())
            continue

        # 2) Bullet with bold name and hyphen details:
        #    "- **Name** - details" or "* **Name** - details"
        m = re.match(r"^\s*[-*]\s*\*\*(.+?)\*\*\s*-\s*(.+)$", s)
        if m:
            name, details = m.group(1).strip(), m.group(2).strip()
            out.append(f"• {name} — {details}")
            continue

        # 3) Numbered item with bold name and hyphen details:
        #    "1. **Name** - details"
        m = re.match(r"^\s*\d+\.\s*\*\*(.+?)\*\*\s*-\s*(.+)$", s)
        if m:
            name, details = m.group(1).strip(), m.group(2).strip()
            out.append(f"• {name} — {details}")
            continue

        # 4) Plain bullet/numbered item without the special pattern -> bulletize nicely
        if re.match(r"^\s*[-*]\s+", s):
            s = re.sub(r"^\s*[-*]\s+", "• ", s)
        elif re.match(r"^\s*\d+\.\s+", s):
            s = re.sub(r"^\s*\d+\.\s+", "• ", s)

        # 5) Strip any remaining bold/italic markers
        s = re.sub(r"\*\*(.*?)\*\*", r"\1", s)
        s = re.sub(r"\*(.*?)\*", r"\1", s)

        out.append(s)

    # Join and compact extra blank lines
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def format_wine_answer(text: str) -> str:
    """
    Turn bullet-first text like:
      "... Here are my top picks: • SAAM Pinotage • A bold choice... • Simonsig ... • ..."
    into:
      • SAAM Pinotage
         - A bold choice...
      • Simonsig Cabernet ...
         - ...
    Also removes duplicate leading paragraph if the model repeated it.
    """
    if not text:
        return ""

    # Normalize
    t = text.replace("—", "-").strip()

    # If model pasted everything twice, collapse duplicates.
    half = len(t)//2
    if len(t) > 200 and t[:half] == t[half:]:
        t = t[:half].strip()

    # Split on bullet marker the model actually uses
    parts = t.split("• ")
    if len(parts) == 1:
        return t  # no bullets detected; return as-is

    # Intro before the first bullet; keep it as a one-line lead
    intro = parts[0].strip()
    tokens = [p.strip(" \n\r\t.") for p in parts[1:] if p.strip()]

    def looks_like_name(s: str) -> bool:
        # Short-ish, starts with uppercase, ≥2 words, and not an obvious attribute
        if len(s) > 65: return False
        if not re.match(r'^[A-ZÅÄÖÉÑ]', s): return False
        if re.match(r'^(aromas?|pairs?|price|abv|alcohol|bonus|for|the|its|with)\b', s, re.I):
            return False
        return len(s.split()) >= 2

    cards = []
    current = None
    for tok in tokens:
        if looks_like_name(tok):
            if current:
                cards.append(current)
            current = {"name": tok, "details": []}
        else:
            if current is None:
                # Stray detail before we find a name; attach to intro
                intro = (intro + (" " if intro else "") + tok).strip()
            else:
                # Clean leading "- " the model sometimes uses for inline facts
                tok = re.sub(r'^\s*-\s*', '', tok)
                current["details"].append(tok)

    if current:
        cards.append(current)

    # If we somehow didn't find any names, bail out
    if not cards:
        return t

    # Build nice readable output
    out = []
    if intro:
        out.append(intro)
        out.append("")
    for c in cards:
        out.append(f"• {c['name']}")
        for d in c["details"]:
            out.append(f"   - {d}")
        out.append("")
    return "\n".join(out).rstrip()



def _extract_candidate_wine_names(text: str):
    """
    Pull likely wine names from the quick DeepSeek text. 
    Works with bullets like '• Name ...' or bolded names.
    """
    if not text:
        return []
    t = clean_markdown(text)
    names = set()

    # 1) From bullet lines: "• Name"
    for line in t.splitlines():
        s = line.strip()
        if s.startswith("•"):
            # keep up to 65 chars, stop at common separators
            name = re.sub(r"^•\s*", "", s)
            name = re.split(r"\s{2,}| - | — |:|\(|,|\. ", name)[0].strip()
            if 2 <= len(name.split()) <= 8 and re.match(r"[A-ZÅÄÖÉÑ]", name):
                names.add(name)

    # 2) Bolded names "**Name**"
    for m in re.finditer(r"\*\*([^*]+?)\*\*", t):
        cand = m.group(1).strip()
        if 2 <= len(cand.split()) <= 8 and re.match(r"[A-ZÅÄÖÉÑ]", cand):
            names.add(cand)

    # 3) Fallback: lines that look like "Name from Region"
    for m in re.finditer(r"^([A-Z][^\n]{3,65}?)\s+from\b", t, re.M):
        cand = m.group(1).strip()
        names.add(cand)

    # Light cleanup
    cleaned = []
    for n in names:
        n = re.sub(r"\s+", " ", n).strip(" -—:•")
        if len(n) >= 3:
            cleaned.append(n)
    return cleaned[:8]

def deepseek_quick(user_query: str):
    """
    Fast path: ask DeepSeek with no retrieval to get an immediate answer.
    Returns answer text + extracted candidate wine names for follow-up retrieval.
    """
    prompt = f"""You are a wine sommelier.
Answer concisely in 1–3 short paragraphs or 3–6 bullets.
Avoid markdown inside sentences (except for wine names or section titles). This wine should be listed in systembolaget, so avoid suggesting wines that are not available there.

User question: {user_query}
Answer:"""

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.choices[0].message.content
    txt = format_wine_answer(clean_markdown(raw))
    names = _extract_candidate_wine_names(txt)
    return {"answer": txt, "names": names}


def build_detailed_from_quick(user_query: str, quick_answer_text: str):
    """
    Use the quick answer to find candidate wine names, retrieve matching docs from your dataset,
    then reuse your existing RAG generator with followup_context.
    """
    names = _extract_candidate_wine_names(quick_answer_text)
    if not names:
        # fallback: just do a normal retrieval on the original query
        return answer_query_rag(user_query)

    # Retrieve matches for each name and dedupe by normalized title
    seen_titles = set()
    matched_docs = []
    for name in names:
        docs = retriever.query(name)
        for d in docs or []:
            card = normalize_doc(d)
            title_key = card["title"].strip().lower()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                matched_docs.append(d)

    if not matched_docs:
        # if nothing matched, fallback to RAG by query
        return answer_query_rag(user_query)

    # Now call your existing function but inject followup_context
    return answer_query_rag(user_query, followup_context=matched_docs)

def answer_query_rag(user_query, followup_context=None):
    """
    Retrieves top relevant wines and returns LLM-generated answer + normalized wine cards.
    """
    context_docs = followup_context if followup_context else retriever.query(user_query)
    if not context_docs:
        return {"answer": "Sorry, I couldn't find any matching wines at the moment.", "sources": [], "structured_wines": []}
    


    # Build clean context for the LLM
    stitched = []
    structured_wines = []
    for d in context_docs:
        # create UI-ready item
        card = normalize_doc(d)
        structured_wines.append(card)

        # small, LLM-friendly context
        stitched.append(
            f"Wine: {card['title']}\n"
            f"Region: {card['region']}\n"
            f"Type: {card['type']}\n"
            f"Aromas/Flavors: {card['aromas']}\n"
            f"Food pairings: {card['pairing']}\n"
            f"Alcohol: {card['alcohol']}\n"
            f"Price: {card['price']}\n"
            f"Description: {card['profile']}\n"
        )

    llm_context = "\n---\n".join(stitched)

    prompt = f"""You are a wine sommelier. 
Answer in a clear, conversational style without markdown bold inside sentences. 
Use short paragraphs and bullet points for wines. 
Bold only wine names or section titles.

Context:
{llm_context}

User question: {user_query}
Answer:"""

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    answer_raw = resp.choices[0].message.content
    answer = clean_markdown(answer_raw)          # your current cleanup
    answer = format_wine_answer(answer)    

    return {
        "answer": answer,
        "sources": [],              # optional
        "structured_wines": structured_wines
    }
