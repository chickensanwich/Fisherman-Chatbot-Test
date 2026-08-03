from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from neo4j import GraphDatabase
from pymongo import MongoClient
from deep_translator import GoogleTranslator
import requests
import langdetect
langdetect.DetectorFactory.seed = 0  # deterministic detection on short/ambiguous chat text
import os
import sys
import json
import re
import uuid
import hashlib
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from fastapi import File, UploadFile
from google.cloud import speech as gcp_speech

load_dotenv()

app = FastAPI(title="FisherMen Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent
app.mount("/css", StaticFiles(directory=BASE_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=BASE_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")
if (BASE_DIR / "tts_audio").exists():
    app.mount("/tts_audio", StaticFiles(directory=BASE_DIR / "tts_audio"), name="tts_audio")

@app.get("/")
async def root():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/settings-page")
async def serve_settings_page():
    return FileResponse(BASE_DIR / "settings.html")

@app.get("/admin-page")
async def serve_admin_page():
    return FileResponse(BASE_DIR / "admin.html")

# ====================== CONFIG ======================
# Defaults to Ollama's hosted Cloud API (no local `ollama serve` process to run
# on a host like Render). Point OLLAMA_URL back at http://localhost:11434/api/chat
# for local development against a locally running Ollama instead.
OLLAMA_URL     = os.getenv("OLLAMA_URL", "https://ollama.com/api/chat")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
MODEL_NAME    = "nemotron-3-super:cloud"
SYSTEM_PROMPT = """You are an expert fishing assistant.

Your primary directive is to answer the user's questions based EXCLUSIVELY on the provided [DATABASE FACTS].

FORMATTING RULE (read this first, it overrides your default habits): Write the entire answer as plain prose - ordinary paragraphs made of full sentences, joined with words like "and", "as well as", or commas. You are FORBIDDEN from using bullet points, numbered lists, dashes, asterisks, markdown bold/headings, or a line break between items, even when the facts would naturally group into a list. For example, if the facts are that X is forbidden, Y is forbidden, and Z is forbidden, write "X, Y, and Z are forbidden" as one sentence - do NOT put X, Y, and Z on separate lines or after dashes. This rule applies no matter what language you are answering in.

CRITICAL INSTRUCTIONS:
1. NO GREETINGS: DO NOT introduce yourself. DO NOT say "Hello" or "I am a chatbot." Start your response IMMEDIATELY with the answer.
2. SYNONYM RESOLUTION & LOGIC: Logically connect the user's intent to the facts. If the user asks for the "best", "right", or "good" bait/gear, and the database says a bait "attracts" or a gear "is suitable for" that fish, treat that as the correct answer.
3. MULTI-HOP DEDUCTION: If a user asks what fish are in a location, and the database says Location A has River B, and River B contains Fish C, you must deduce that Fish C is found in Location A.
4. NO HALLUCINATION: Do not invent fish species, baits, locations, or seasons that are not in the [DATABASE FACTS].
5. MISSING INFORMATION: If the [DATABASE FACTS] genuinely do not contain the answer, politely state that you do not have that specific information. Do not guess.
6. CONCISENESS: Keep your answers brief, direct, and highly accurate.
7. PLAIN PROSE ONLY: Follow the FORMATTING RULE above in every response, in every language - no bullet points, numbered lists, or markdown, ever. This keeps the answer's structure identical before and after translation, since translating a bulleted list into Bengali/Indonesian tends to collapse it into a paragraph anyway - writing prose from the start avoids that inconsistency between languages.
"""
NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "nej4nej4")


def _ollama_headers() -> dict:
    return {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}


# ====================== GOOGLE CLOUD SPEECH-TO-TEXT ======================
speech_client = None

def _get_speech_client():
    global speech_client
    if speech_client is None:
        speech_client = gcp_speech.SpeechClient()
    return speech_client

# ====================== MONGODB STORAGE ======================
# Users, chats, feedback, contributions, settings and admin config live in
# MongoDB Atlas (free M0 tier) rather than local JSON files or Neo4j. A host like Render's
# free tier has no persistent disk, so anything written to local files is
# lost on restart/redeploy; Neo4j stays dedicated to the fishing knowledge
# graph only, not this operational data.
MONGODB_URI = os.getenv("MONGODB_URI", "")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI environment variable is required (MongoDB Atlas connection string).")

_mongo_client = MongoClient(MONGODB_URI)
_mongo_db     = _mongo_client["fisherman"]

_DEFAULTS = {
    "neo4j_mode":           "local",
    "neo4j_uri":            NEO4J_URI,
    "neo4j_user":           NEO4J_USER,
    "neo4j_password":       NEO4J_PASSWORD,
    "neo4j_cloud_uri":      "",
    "neo4j_cloud_user":     "",
    "neo4j_cloud_password": "",
    "tunnel_hostname":      "",
    "tunnel_token":         "",
    "ollama_url":           OLLAMA_URL,
    "model_name":           MODEL_NAME,
    "google_creds_path":    os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
    "system_prompt":        SYSTEM_PROMPT,
}


def _load_settings() -> dict:
    stored = _mongo_db.settings.find_one({"_id": "app_settings"}) or {}
    stored.pop("_id", None)
    return {**_DEFAULTS, **stored}


def _save_settings_file(data: dict) -> None:
    _mongo_db.settings.replace_one({"_id": "app_settings"}, {**data, "_id": "app_settings"}, upsert=True)


def _apply_settings(s: dict) -> None:
    global neo4j_driver, OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT
    OLLAMA_URL    = s["ollama_url"]
    MODEL_NAME    = s["model_name"]
    SYSTEM_PROMPT = s.get("system_prompt") or SYSTEM_PROMPT
    if s.get("google_creds_path"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = s["google_creds_path"]
    if s.get("neo4j_mode") == "cloud":
        uri      = s.get("neo4j_cloud_uri", "")
        user     = s.get("neo4j_cloud_user", "")
        password = s.get("neo4j_cloud_password", "")
    else:
        uri      = s["neo4j_uri"]
        user     = s["neo4j_user"]
        password = s["neo4j_password"]
    try:
        neo4j_driver.close()
    except Exception:
        pass
    neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))


# Boot: apply persisted settings (if any) over the compiled defaults
_apply_settings(_load_settings())

# ====================== ADMIN AUTH ======================
def _load_admin_password() -> str:
    config = _mongo_db.admin_config.find_one({"_id": "admin_config"})
    return (config or {}).get("admin_password", "admin")

async def require_admin(x_admin_password: str = Header(...)) -> None:
    if x_admin_password != _load_admin_password():
        raise HTTPException(status_code=401, detail="Invalid admin password.")

# ====================== DATABASES ======================
# neo4j_driver is initialised inside _apply_settings above


def _load_users() -> list:
    return list(_mongo_db.users.find({}, {"_id": 0}))


def _save_users(users: list) -> None:
    _mongo_db.users.delete_many({})
    if users:
        _mongo_db.users.insert_many([dict(u) for u in users])


def _load_feedbacks() -> list:
    return list(_mongo_db.feedbacks.find({}, {"_id": 0}))


def _save_feedbacks(feedbacks: list) -> None:
    _mongo_db.feedbacks.delete_many({})
    if feedbacks:
        _mongo_db.feedbacks.insert_many([dict(f) for f in feedbacks])


def _load_chats() -> list:
    return list(_mongo_db.chats.find({}, {"_id": 0}))


def _save_chats(chats: list) -> None:
    _mongo_db.chats.delete_many({})
    if chats:
        _mongo_db.chats.insert_many([dict(c) for c in chats])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_identifier(name: str) -> str:
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
        raise HTTPException(status_code=400, detail=f"Invalid identifier '{name}': use letters, digits, underscores only.")
    return name


def _get_element_id(entity) -> str:
    if hasattr(entity, 'element_id'):
        return entity.element_id
    return str(entity.id)


# ====================== AUTH DEPENDENCY ======================
async def require_approved_user(x_fisherman_id: str = Header(...)) -> str:
    users = _load_users()
    user  = next((u for u in users if u["fishermanId"] == x_fisherman_id), None)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown Fisherman ID.")
    if user["status"] == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval.")
    if user["status"] == "rejected":
        raise HTTPException(status_code=403, detail="Account rejected. Contact support.")
    return x_fisherman_id


# ====================== MODELS ======================
class ChatRequest(BaseModel):
    message: str
    chat_id: str

class SignupRequest(BaseModel):
    name: str
    fishermanId: str
    country: str
    location: str
    password: str

class LoginRequest(BaseModel):
    fishermanId: str
    password: str

class FeedbackRequest(BaseModel):
    type: str
    reason: str = ""
    comments: str = ""
    message: str = ""
    userQuestion: str = ""

class TitleUpdate(BaseModel):
    title: str

class PinUpdate(BaseModel):
    pinned: bool

class CreateNodeRequest(BaseModel):
    label: str
    properties: dict = {}

class UpdateNodeRequest(BaseModel):
    node_id: str
    properties: dict

class CreateRelationshipRequest(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    properties: dict = {}


# ====================== LANGUAGE & KNOWLEDGE GRAPH ======================
# Indonesia is the primary deployment/testing market; English is the secondary
# option; Bangla is kept working as a legacy option only. Any language the
# detector isn't sure about (or doesn't recognize) should fall back to
# Indonesian, not English, since that's what real users will actually send.
SUPPORTED_LANGS = {"id", "en", "bn"}
DEFAULT_LANG = "id"

LANG_NAME = {"id": "Bahasa Indonesia", "en": "English", "bn": "Bangla"}

FALLBACK_REPLY = {
    "id": "Informasi ini belum tersedia saat ini.",
    "bn": "এই তথ্য আমার কাছে এখন নেই।",
    "en": "I don't have that information right now.",
}
ERROR_REPLY = {
    "id": "Maaf, terjadi masalah internal.",
    "bn": "দুঃখিত, একটি অভ্যন্তরীণ সমস্যা হয়েছে।",
    "en": "Sorry, an internal error occurred.",
}


_BENGALI_SCRIPT_RE = re.compile(r'[ঀ-৿]')

# Used only as a tie-breaker when langdetect calls a message Indonesian/Bengali
# but it's structurally an English sentence with one foreign/local word mixed
# in (e.g. a knowledge-graph entity name like "punggawa") - langdetect judges
# the whole message by that one word otherwise. Deliberately short: common
# function words are enough to signal "this sentence is built in English/
# Indonesian", without trying to be a real language classifier.
_ENGLISH_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "tell", "me", "about",
    "how", "when", "where", "why", "who", "which", "do", "does", "did", "can",
    "could", "would", "should", "i", "you", "we", "they", "it", "this", "that",
    "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "best",
    "good", "your",
}
_INDONESIAN_STOPWORDS = {
    "apa", "bagaimana", "kapan", "di", "mengapa", "kenapa", "siapa", "yang",
    "adalah", "ini", "itu", "dan", "atau", "tapi", "tetapi", "ke", "dari",
    "untuk", "dengan", "saya", "anda", "kami", "kita", "mereka", "tidak",
    "juga", "akan", "sudah", "bisa", "dapat", "apakah", "ada", "paling",
}


def _looks_structurally_english(text: str) -> bool:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    en_hits = sum(1 for w in words if w in _ENGLISH_STOPWORDS)
    id_hits = sum(1 for w in words if w in _INDONESIAN_STOPWORDS)
    return en_hits >= 2 and en_hits > id_hits


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return DEFAULT_LANG
    # Bengali uses its own Unicode block, so this is unambiguous - skip
    # langdetect entirely when we can already tell from the script alone.
    # langdetect is unreliable on short/mixed-language text (e.g. it has
    # misclassified plain Bengali sentences as Indonesian), so avoid relying
    # on it for the one case we can resolve with certainty up front.
    if _BENGALI_SCRIPT_RE.search(text):
        return "bn"
    try:
        detected = langdetect.detect(text.strip())
    except Exception:
        return DEFAULT_LANG

    # langdetect misfires when an otherwise-English sentence contains a
    # single foreign/local word (very common here, since KG entity names are
    # frequently Indonesian terms like "punggawa"). If the sentence is
    # clearly built from English function words with no competing Indonesian
    # ones, trust that over the raw guess. Genuinely ambiguous/short text
    # (no clear English signal either) still falls through to the existing
    # "default to Indonesian" behavior below via resolve_lang.
    if detected != "en" and _looks_structurally_english(text):
        return "en"
    return detected


def resolve_lang(detected_lang: str) -> str:
    """Collapse langdetect's raw guess to one of our supported languages.
    Anything we don't explicitly support (including misfires on short/
    ambiguous text) defaults to Indonesian rather than English."""
    return detected_lang if detected_lang in SUPPORTED_LANGS else DEFAULT_LANG


def translate(text: str, source: str, target: str) -> str:
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except Exception as e:
        print(f"[TRANSLATION ERROR] {e}")
        return text


def extract_database_keywords_via_llm(user_message: str) -> list:
    try:
        prompt = f"""You are an expert entity extraction AI for a fishing community Knowledge Graph.
Your task is to extract ONLY the specific entities explicitly mentioned in the user's message.

CRITICAL RULES:
1. ONLY EXTRACT WHAT IS THERE: Extract exactly what the user asks about. Do NOT guess answers. If the user asks "What bait is used for Blackfish?", extract ONLY 'Blackfish'.
2. OPEN ENTITY EXTRACTION: You must extract ANY fish, gear, location, bait, weather, activity, social role, custom, ritual, rule, or belief mentioned by the user, EVEN IF it is not in the example list below.
   Here are EXAMPLES of known entities and how to categorize them (but do not restrict yourself ONLY to this list):
   - Fish Examples: Catla (কাতলা / Ikan Catla), Rohu (রুই / Ikan Rohu), Vetki (ভেটকি / barramundi / Kakap Putih), Hilsa (ইলিশ / Ikan Hilsa), Chingri (চিংড়ি / shrimp / Udang).
   - Water/Weather Examples: Clean Water (পরিষ্কার / Air Bersih), Murky Water (ঘোলা / Air Keruh), Stormy (Badai).
   - Gear & Bait Examples: Cast Net (Jala), Fishing Net (জাল / Jaring), Hook and Line (হুক / বর্শী / Kail dan Senar), Shrimp (চিংড়ির টোপ / Umpan Udang), Dough Bait (আটা / Umpan Adonan).
   - Location Examples: Chandpur (চাঁদপুর), Padma River (পদ্মা / Sungai Padma), Bay of Bengal (বঙ্গোপসাগর / Teluk Benggala).
   - Time/Activity Examples: September (সেপ্টেম্বর), Full Moon (পূর্ণিমা / Bulan Purnama), Night Fishing (রাতে / Memancing Malam).
   - Social/Cultural Examples (from Indonesian fishing communities): Patrons (Punggawa), Fishing Cooperative (Koperasi), Barzanji, Parappo, Apparuru (pre-departure rituals).
3. ALIAS RESOLUTION: Use the examples above to map common Bengali or Indonesian names to their English equivalents if they match — this applies to social/cultural terms exactly the same as fish/gear terms. 'Punggawa' must be extracted as 'Patrons', 'Koperasi' as 'Fishing Cooperative', etc., since that is the name these entities are stored under. If a user mentions a completely new fish like 'Blackfish', 'ব্লাকফিশ', or 'Ikan Hitam', simply extract 'Blackfish'.
4. FORMAT: Output ONLY a clean, comma-separated list of English keywords in Title Case. No explanations.

Example 1:
Text: রুই মাছ ধরার জন্য কোন টোপ সবচেয়ে ভালো?
Keywords: Rohu

Example 2:
Text: চাঁদপুরে গেলে কোন নদীতে কী কী মাছ পাওয়া যেতে পারে?
Keywords: Chandpur

Example 3:
Text: সেপ্টেম্বরে নদীতে মাছ ধরার ক্ষেত্রে কি কোনো নিষেধাজ্ঞা আছে?
Keywords: September, River Fishing

Example 4:
Text: Umpan apa yang paling bagus untuk menangkap ikan Rohu?
Keywords: Rohu

Example 5:
Text: Kalau pergi ke Chandpur, sungai mana saja yang banyak ikannya?
Keywords: Chandpur

Example 6:
Text: Apakah ada larangan memancing di sungai pada bulan September?
Keywords: September, River Fishing

Text: {user_message}
Keywords:"""

        response = requests.post(OLLAMA_URL, headers=_ollama_headers(), json={
            "model": MODEL_NAME,
            "keep_alive": -1,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=40)
        
        response.raise_for_status()
        data = response.json()
        
        content = ""
        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"].strip()
        elif "response" in data:
            content = data["response"].strip()
            
        if '</think>' in content:
            content = content.split('</think>')[-1]
        content = content.replace('<think>', '')
        
        content = content.replace('`', '').replace('\n', ',') 
        
        raw_keywords = [
            kw.strip() for kw in content.split(',') 
            if kw.strip() and '<' not in kw and '>' not in kw
        ]
        
        if len(raw_keywords) == 1 and ' ' in raw_keywords[0] and ',' not in content:
            raw_keywords = [kw.strip() for kw in raw_keywords[0].split(' ')]
            
        final_keywords = [kw for kw in raw_keywords if len(kw) > 2]
                    
        return final_keywords
            
    except Exception as e:
        print(f"[LLM KEYWORD EXTRACTION FAILED]: {e}")

    return []


# ====================== DYNAMIC ENTITY RESOLUTION ======================
# The knowledge graph is populated by a separate document-ingestion pipeline we
# don't control. It names entities as verbatim phrases extracted from source
# documents (in whatever language/wording the source used), so a static alias
# list in the keyword-extraction prompt above can never keep up with new
# documents. Instead, we fetch what's actually in the graph right now and ask
# an LLM to match the user's message against those real names directly - this
# keeps working as new entities are ingested, with no further code changes.
_known_entity_names_cache = {"names": [], "fetched_at": 0.0}
_KNOWN_ENTITY_NAMES_TTL_SECONDS = 300


def get_known_entity_names() -> list:
    now = datetime.now(timezone.utc).timestamp()
    if _known_entity_names_cache["names"] and now - _known_entity_names_cache["fetched_at"] < _KNOWN_ENTITY_NAMES_TTL_SECONDS:
        return _known_entity_names_cache["names"]

    try:
        with neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n.name IS NOT NULL AND NOT labels(n)[0] IN ['Document', 'Chunk']
                RETURN DISTINCT n.name AS name
                LIMIT 500
                """
            )
            names = [record["name"] for record in result]
        _known_entity_names_cache["names"]      = names
        _known_entity_names_cache["fetched_at"]  = now
        return names
    except Exception as e:
        print(f"[FETCH KNOWN ENTITY NAMES FAILED]: {e}")
        return _known_entity_names_cache["names"]


def resolve_keywords_to_known_entities(user_message: str, raw_keywords: list, known_names: list) -> list:
    if not known_names:
        return []

    try:
        names_list = "\n".join(f"- {n}" for n in known_names)
        prompt = f"""You are matching a user's message to known entities from a knowledge graph.

Below is a list of entity names that currently exist in the knowledge graph. They may be in English, Indonesian, or Bengali, and may be short names or full descriptive phrases extracted from documents:
{names_list}

User's message: {user_message}
Candidate keywords already extracted: {', '.join(raw_keywords) if raw_keywords else '(none)'}

Task: Identify which of the entity names above (copy them EXACTLY as written, do not paraphrase or translate them) the user's message is asking about or clearly related to. Consider that a local-language term in the user's message may correspond to a differently-named entity in the list (e.g. an Indonesian social/cultural term matching an English-named entity). Only include an entity if it is clearly relevant - do not guess.

Output ONLY a comma-separated list of the matched entity names, copied exactly as they appear above. If none match, output NONE."""

        response = requests.post(OLLAMA_URL, headers=_ollama_headers(), json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1}
        }, timeout=40)
        response.raise_for_status()
        data = response.json()

        content = ""
        if "message" in data and "content" in data["message"]:
            content = data["message"]["content"].strip()
        elif "response" in data:
            content = data["response"].strip()

        if not content or content.strip().upper() == "NONE":
            return []

        known_names_lower = {n.lower(): n for n in known_names}
        resolved = []
        for candidate in content.split(","):
            candidate = candidate.strip()
            if candidate.lower() in known_names_lower:
                resolved.append(known_names_lower[candidate.lower()])
        return resolved
    except Exception as e:
        print(f"[ENTITY RESOLUTION FAILED]: {e}")
        return []


def query_knowledge_graph(user_message: str) -> str:

    # Keyword extraction (LLM) and fetching known entity names (Neo4j, usually
    # served from cache) don't depend on each other - run them concurrently
    # instead of back-to-back to shave a full round trip off every request.
    with ThreadPoolExecutor(max_workers=2) as executor:
        keywords_future = executor.submit(extract_database_keywords_via_llm, user_message)
        names_future    = executor.submit(get_known_entity_names)
        raw_keywords    = keywords_future.result()
        known_names     = names_future.result()

    stop_words = {"food", "bait", "fish", "fishing", "catch", "river", "water", "gear", "net", "how", "what", "where", "best", "the", "a", "an"}
    keywords = [kw for kw in raw_keywords if kw.lower() not in stop_words]

    # The entity-resolution LLM call exists to bridge cases where the extracted
    # keyword doesn't match a graph entity's name at all (translations, local
    # terms, etc). The Cypher match below considers a keyword a hit whenever a
    # node's name CONTAINS it as a substring (not exact equality) - mirror that
    # same test here, otherwise minor extraction variation (e.g. singular vs
    # plural) makes this check fail even though the query would've matched fine,
    # defeating the whole point of skipping the extra call.
    known_names_lower = {n.lower() for n in known_names}
    def _already_matches(kw: str) -> bool:
        kw_lower = kw.lower()
        return any(kw_lower in name for name in known_names_lower)

    if keywords and all(_already_matches(kw) for kw in keywords):
        resolved_names = []
    else:
        resolved_names = resolve_keywords_to_known_entities(user_message, keywords, known_names)

    for name in resolved_names:
        if name not in keywords:
            keywords.append(name)

    print(f"DEBUG UNIVERSAL LLM KEYWORDS SEARCHING FOR: {keywords}")

    if not keywords:
        return ""
        
    grouped_facts = {}

    with neo4j_driver.session() as session:
        result = session.run(
            """
            MATCH (n)
            WHERE any(kw IN $keywords WHERE toLower(toString(n.name)) =~ ('(?i).*' + toLower(kw) + '.*'))
            WITH n LIMIT 3

            OPTIONAL MATCH path = (n)-[*1..2]-(m)

            // Score the path: Prioritize ending on High-Value answers. Curated domain
            // labels (FishSpecies, Bait, ...) score highest; generic KGNode entities
            // (from document ingestion: Group, Belief, Rule, Ritual, ...) score neutral;
            // Document/Chunk nodes (ingestion plumbing, not facts) score lowest.
            WITH path,
                 CASE
                     WHEN labels(m)[0] IN ['Document', 'Chunk'] THEN 0
                     WHEN labels(m)[0] IN ['FishSpecies', 'Bait', 'Gear', 'Constraint', 'SafetySignal'] THEN 2
                     ELSE 1
                 END as relevance
            ORDER BY relevance DESC
            LIMIT 35

            UNWIND (CASE WHEN path IS NULL THEN [null] ELSE relationships(path) END) AS r
            WITH DISTINCT r
            WHERE r IS NOT NULL
              AND NOT type(r) IN ['HAS_CHUNK', 'MENTIONS']
              AND startNode(r).name IS NOT NULL
              AND endNode(r).name IS NOT NULL
            RETURN
                CASE
                    WHEN labels(startNode(r))[0] = 'KGNode' AND startNode(r).type IS NOT NULL THEN startNode(r).type
                    WHEN size(labels(startNode(r))) > 0 THEN labels(startNode(r))[0]
                    ELSE 'Entity'
                END AS start_label,
                startNode(r).name AS start_name,
                type(r) AS r_type,
                CASE
                    WHEN labels(endNode(r))[0] = 'KGNode' AND endNode(r).type IS NOT NULL THEN endNode(r).type
                    WHEN size(labels(endNode(r))) > 0 THEN labels(endNode(r))[0]
                    ELSE 'Entity'
                END AS end_label,
                endNode(r).name AS end_name
            """,
            keywords=keywords
        )

        matched_entity_names = set()
        for record in result:
            start_label = record["start_label"]
            start_name = record["start_name"]
            end_label = record["end_label"]
            end_name = record["end_name"]
            clean_rel = record["r_type"].lower().replace("_", " ")

            matched_entity_names.add(start_name)
            matched_entity_names.add(end_name)

            entity_key = f"[{start_label}] '{start_name}'"

            if entity_key not in grouped_facts:
                grouped_facts[entity_key] = set()

            grouped_facts[entity_key].add(f"[{clean_rel}] {end_label} '{end_name}'")


    context_lines = []
    for entity, facts in grouped_facts.items():
        fact_string = f"- {entity} -> " + " | ".join(list(facts))
        context_lines.append(fact_string)

    final_context = "Relevant database facts:\n" + "\n".join(context_lines) if context_lines else ""

    # The user's own wording (or its machine translation) frequently won't
    # match these entity names exactly - a local term, an alias, or a mangled
    # translation. Explicitly tell the answer-generation LLM these entities
    # ARE what the question is about, so it doesn't decline just because the
    # surface wording differs from the facts it was just given.
    if final_context and matched_entity_names:
        final_context += (
            "\n\nNote: the user's message may refer to the entities above using "
            "different wording (a local term, an alias, or a mistranslation) - "
            "treat the following as confirmed relevant to their question and use "
            f"the facts above to answer: {', '.join(sorted(matched_entity_names))}."
        )

    return final_context

# ====================== AUTO-GENERATE CHAT TITLE ======================
async def generate_chat_title(user_message: str, bot_reply: str, lang: str = DEFAULT_LANG) -> str:
    try:
        title_lang = LANG_NAME.get(lang, LANG_NAME[DEFAULT_LANG])
        prompt = f"""Create a short, clear, and appropriate title (maximum 6 words) in {title_lang} for this chat.
Context:
User's first message: {user_message}
Assistant's reply: {bot_reply[:300]}

Title (return only the title, do not give any explanation or quotation marks):"""


        response = requests.post(OLLAMA_URL, headers=_ollama_headers(), json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }, timeout=40)
        response.raise_for_status()
        data  = response.json()
        title = ""
        if "message" in data and "content" in data["message"]:
            title = data["message"]["content"].strip()
        elif "response" in data:
            title = data["response"].strip()

        title = title.replace('"', '').replace("'", "").strip()
        if len(title) > 60:
            title = title[:57] + "..."
        if title:
            return title
    except Exception as e:
        print(f"Title generation failed: {e}")

    fallback = user_message.strip()[:50]
    return fallback + "..." if len(fallback) == 50 else fallback


# ====================== AUTH ENDPOINTS ======================
@app.post("/signup")
async def signup(request: SignupRequest):
    users = _load_users()
    if any(u["fishermanId"] == request.fishermanId for u in users):
        raise HTTPException(status_code=409, detail="Fisherman ID already registered.")
    users.append({
        "fishermanId":    request.fishermanId,
        "name":           request.name,
        "country":        request.country,
        "location":       request.location,
        "password_hash":  _hash_password(request.password),
        "status":         "pending",
        "created_at":     datetime.now(timezone.utc).isoformat(),
    })
    _save_users(users)
    return {"status": "pending", "message": "Account submitted for approval. Please wait for admin review."}


@app.post("/login")
async def login(request: LoginRequest):
    users = _load_users()
    user  = next((u for u in users if u["fishermanId"] == request.fishermanId), None)
    if not user or user["password_hash"] != _hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid Fisherman ID or password.")
    if user["status"] == "pending":
        raise HTTPException(status_code=403, detail="Your account is pending admin approval.")
    if user["status"] == "rejected":
        raise HTTPException(status_code=403, detail="Your account has been rejected. Please contact support.")
    return {
        "status":      "approved",
        "name":        user["name"],
        "fishermanId": user["fishermanId"],
        "country":     user["country"],
        "location":    user["location"],
    }


# ====================== ADMIN USER MANAGEMENT ======================
@app.post("/admin/verify")
async def verify_admin(_: None = Depends(require_admin)):
    return {"status": "ok"}


@app.get("/admin/pending-users")
async def get_pending_users(_: None = Depends(require_admin)):
    users   = _load_users()
    pending = [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in users if u["status"] == "pending"
    ]
    return pending


@app.post("/admin/approve/{fisherman_id}")
async def approve_user(fisherman_id: str, _: None = Depends(require_admin)):
    users = _load_users()
    user  = next((u for u in users if u["fishermanId"] == fisherman_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user["status"] = "approved"
    _save_users(users)
    return {"status": "approved", "fishermanId": fisherman_id}


@app.post("/admin/reject/{fisherman_id}")
async def reject_user(fisherman_id: str, _: None = Depends(require_admin)):
    users = _load_users()
    user  = next((u for u in users if u["fishermanId"] == fisherman_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user["status"] = "rejected"
    _save_users(users)
    return {"status": "rejected", "fishermanId": fisherman_id}


# ====================== GOOGLE CLOUD SPEECH-TO-TEXT ======================
@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    x_fisherman_id: str = Header(...)
):
    await require_approved_user(x_fisherman_id)

    audio_content = await audio.read()
    content_type  = (audio.content_type or "audio/webm").lower()
    encoding = (
        gcp_speech.RecognitionConfig.AudioEncoding.OGG_OPUS
        if "ogg" in content_type
        else gcp_speech.RecognitionConfig.AudioEncoding.WEBM_OPUS
    )

    try:
        recognition_audio = gcp_speech.RecognitionAudio(content=audio_content)
        config = gcp_speech.RecognitionConfig(
            encoding=encoding,
            language_code="id-ID",
            alternative_language_codes=["en-US", "bn-BD"],
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        response = await asyncio.to_thread(
            _get_speech_client().recognize,
            config=config,
            audio=recognition_audio,
        )

        if not response.results:
            return {"text": "", "language": DEFAULT_LANG}

        transcript = " ".join(
            result.alternatives[0].transcript
            for result in response.results
        )
        detected_lang_bcp47 = response.results[0].language_code
        if detected_lang_bcp47.startswith("bn"):
            lang = "bn"
        elif detected_lang_bcp47.startswith("en"):
            lang = "en"
        else:
            lang = "id"
        return {"text": transcript.strip(), "language": lang}

    except Exception as e:
        print(f"Google Cloud STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ====================== CHAT HISTORY ======================
@app.get("/chats")
async def get_user_chats(x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    chats = [c for c in _load_chats() if c.get("user_id") == x_fisherman_id]
    chats.sort(key=lambda c: (not c.get("pinned", False), c.get("updated_at", "")), reverse=True)
    return chats[:50]


@app.post("/chats")
async def create_new_chat(x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    now = _now_iso()
    chat_doc = {
        "chat_id":    str(uuid.uuid4()),
        "user_id":    x_fisherman_id,
        "title":      "নতুন চ্যাট",
        "messages":   [],
        "pinned":     False,
        "created_at": now,
        "updated_at": now,
    }
    chats = _load_chats()
    chats.append(chat_doc)
    _save_chats(chats)
    return {"chat_id": chat_doc["chat_id"], "title": "নতুন চ্যাট"}


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    chats = _load_chats()
    chat = next((c for c in chats if c["chat_id"] == chat_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.get("user_id") != x_fisherman_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this chat")
    _save_chats([c for c in chats if c["chat_id"] != chat_id])
    return {"status": "deleted", "message": "Chat successfully deleted"}


@app.get("/chats/{chat_id}")
async def get_chat_by_id(chat_id: str, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    chats = _load_chats()
    chat = next((c for c in chats if c["chat_id"] == chat_id and c.get("user_id") == x_fisherman_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or no permission")
    return chat


@app.put("/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, body: TitleUpdate, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    chats = _load_chats()
    chat = next((c for c in chats if c["chat_id"] == chat_id and c.get("user_id") == x_fisherman_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or no permission")
    chat["title"] = body.title.strip() or "Untitled Chat"
    _save_chats(chats)
    return {"status": "success", "title": chat["title"]}


@app.put("/chats/{chat_id}/pin")
async def toggle_pin_chat(chat_id: str, body: PinUpdate, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    chats = _load_chats()
    chat = next((c for c in chats if c["chat_id"] == chat_id and c.get("user_id") == x_fisherman_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found or no permission")
    chat["pinned"] = body.pinned
    _save_chats(chats)
    return {"status": "success", "pinned": body.pinned}


# ====================== CHAT MESSAGE SAVING ======================
def save_chat_message(fisherman_id: str, chat_id: str, user_message: str, bot_reply: str):
    chats = _load_chats()
    chat = next((c for c in chats if c["chat_id"] == chat_id and c.get("user_id") == fisherman_id), None)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    now = _now_iso()
    chat["messages"].extend([
        {"sender": "user", "content": user_message, "timestamp": now},
        {"sender": "bot",  "content": bot_reply,    "timestamp": now},
    ])
    chat["updated_at"] = now
    _save_chats(chats)


# ====================== MAIN CHAT ENDPOINT ======================
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks, x_fisherman_id: str = Header(...)):
    fisherman_id = await require_approved_user(x_fisherman_id)
    user_message = request.message.strip()
    chat_id      = request.chat_id

    detected_lang     = detect_language(user_message)
    lang              = resolve_lang(detected_lang)
    needs_translation = lang in {"id", "bn"}

    # Input translation and the KG lookup don't depend on each other - run them
    # concurrently instead of back-to-back.
    kg_task = asyncio.to_thread(query_knowledge_graph, user_message)
    if needs_translation:
        english_message, kg_context = await asyncio.gather(
            asyncio.to_thread(translate, user_message, lang, "en"),
            kg_task,
        )
    else:
        english_message = user_message
        kg_context       = await kg_task

    print(f"\n=== DEBUG: detected_lang={detected_lang} resolved_lang={lang} ===")
    print("=== DEBUG: CONTEXT SENT TO LLM ===")
    print(kg_context)
    print("==================================\n")

    async def auto_update_title_if_default(reply_text: str):

        chats_current = _load_chats()
        current_chat = next((c for c in chats_current if c["chat_id"] == chat_id), None)
        if current_chat and current_chat.get("title") == "নতুন চ্যাট":
            new_title = await generate_chat_title(user_message, reply_text, lang)
            if new_title:
                current_chat["title"] = new_title
                _save_chats(chats_current)

    # Chat-title generation is cosmetic sidebar metadata, not part of the answer
    # the user is waiting on - run it after the response is sent instead of
    # making them wait through a 4th LLM call for it.
    if not kg_context:
        fallback_reply = FALLBACK_REPLY.get(lang, FALLBACK_REPLY[DEFAULT_LANG])
        save_chat_message(fisherman_id, chat_id, user_message, fallback_reply)
        background_tasks.add_task(auto_update_title_if_default, fallback_reply)
        return {"reply": fallback_reply, "lang": lang}

   
    # Machine translation can mangle a specific term (e.g. a local/foreign name
    # that also appears verbatim in [DATABASE FACTS]) into an unrelated English
    # word, which then stops the model from connecting its own retrieved facts
    # back to the question. Including the untranslated original alongside the
    # translated message lets the model bridge that gap itself when needed.
    user_content = english_message
    if needs_translation and english_message != user_message:
        user_content = (
            f"{english_message}\n\n"
            f"(Original message before translation, in case any term above was "
            f"mistranslated: {user_message})"
        )

    llm_messages = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\n[DATABASE FACTS]\n{kg_context}"
        },
        {
            "role": "user",
            "content": user_content
        }
    ]

   
    try:
        response = await asyncio.to_thread(
            requests.post,
            OLLAMA_URL,
            headers=_ollama_headers(),
            json={
                "model": MODEL_NAME,
                "messages": llm_messages,
                "stream": False,
                "options": {"temperature": 0.3} 
            },
            timeout=45
        )
        response.raise_for_status()
        data = response.json()
        
        bot_reply_en = ""
        if "message" in data and "content" in data["message"]:
            bot_reply_en = data["message"]["content"].strip()
        elif "response" in data:
            bot_reply_en = data["response"].strip()

        final_reply = translate(bot_reply_en, "en", lang) if needs_translation else bot_reply_en


        save_chat_message(fisherman_id, chat_id, user_message, final_reply)
        background_tasks.add_task(auto_update_title_if_default, final_reply)

        return {"reply": final_reply, "lang": lang}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[LLM GENERATION FAILED]: {e}")
        error_reply = ERROR_REPLY.get(lang, ERROR_REPLY[DEFAULT_LANG])
        raise HTTPException(status_code=500, detail=str(error_reply))


# ====================== FEEDBACK ======================
@app.post("/feedback")
async def feedback(request: FeedbackRequest, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    feedbacks = _load_feedbacks()
    feedbacks.append({
        "type":          request.type,
        "reason":        request.reason,
        "comments":      request.comments,
        "message":       request.message,
        "userQuestion":  request.userQuestion,
        "fishermanId":   x_fisherman_id,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    })
    _save_feedbacks(feedbacks)
    return {"status": "ok"}


@app.get("/feedbacks")
async def get_feedbacks(_: None = Depends(require_admin)):
    return _load_feedbacks()


# ====================== KNOWLEDGE GRAPH ADMIN ======================
@app.get("/admin/graph/search")
async def search_graph_nodes(q: str = "", _: None = Depends(require_admin)):
    results = []
    with neo4j_driver.session() as session:
        keywords = [w for w in q.lower().split() if len(w) > 2] if q.strip() else [""]
        seen = set()
        for keyword in keywords[:5]:
            # Only scan properties that are always scalar (both the curated fact-graph
            # schema and the document-ingestion schema use these). Scanning every
            # property via keys(n) would crash on list-typed properties like the
            # ingestion schema's job_ids/filenames/chunk_ids, since Cypher's toString()
            # doesn't accept lists.
            cypher = (
                "MATCH (n) WHERE any(prop in ['name', 'text', 'filename', 'uid'] "
                "WHERE n[prop] IS NOT NULL AND toLower(toString(n[prop])) CONTAINS $kw) "
                "OPTIONAL MATCH (n)-[r]->(m) "
                "RETURN n, collect({relId: elementId(r), type: type(r), targetId: elementId(m), targetProps: properties(m)}) as rels "
                "LIMIT 20"
            ) if keyword else (
                "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) "
                "RETURN n, collect({relId: elementId(r), type: type(r), targetId: elementId(m), targetProps: properties(m)}) as rels "
                "LIMIT 20"
            )
            rows = session.run(cypher, kw=keyword)
            for record in rows:
                node = record["n"]
                nid  = _get_element_id(node)
                if nid in seen:
                    continue
                seen.add(nid)
                rels = [r for r in record["rels"] if r.get("type") is not None]
                results.append({
                    "nodeId":        nid,
                    "labels":        list(node.labels),
                    "properties":    dict(node),
                    "relationships": [
                        {
                            "relId":       r["relId"],
                            "type":        r["type"],
                            "targetId":    r["targetId"],
                            "targetProps": dict(r["targetProps"]) if r["targetProps"] else {},
                        }
                        for r in rels
                    ],
                })
    return results


@app.post("/admin/graph/node")
async def create_graph_node(request: CreateNodeRequest, _: None = Depends(require_admin)):
    label = _validate_identifier(request.label)
    with neo4j_driver.session() as session:
        result = session.run(
            f"CREATE (n:{label} $props) RETURN elementId(n) as nodeId",
            props=request.properties,
        )
        record = result.single()
        return {"nodeId": record["nodeId"]}


@app.put("/admin/graph/node")
async def update_graph_node(request: UpdateNodeRequest, _: None = Depends(require_admin)):
    with neo4j_driver.session() as session:
        result = session.run(
            "MATCH (n) WHERE elementId(n) = $nid SET n += $props RETURN elementId(n) as nodeId",
            nid=request.node_id,
            props=request.properties,
        )
        if not result.single():
            raise HTTPException(status_code=404, detail="Node not found.")
    return {"status": "updated"}


@app.delete("/admin/graph/node")
async def delete_graph_node(node_id: str, _: None = Depends(require_admin)):
    with neo4j_driver.session() as session:
        session.run(
            "MATCH (n) WHERE elementId(n) = $nid DETACH DELETE n",
            nid=node_id,
        )
    return {"status": "deleted"}


@app.post("/admin/graph/relationship")
async def create_graph_relationship(request: CreateRelationshipRequest, _: None = Depends(require_admin)):
    rel_type = _validate_identifier(request.rel_type)
    with neo4j_driver.session() as session:
        result = session.run(
            f"MATCH (a), (b) WHERE elementId(a) = $from_id AND elementId(b) = $to_id "
            f"CREATE (a)-[r:{rel_type} $props]->(b) RETURN elementId(r) as relId",
            from_id=request.from_id,
            to_id=request.to_id,
            props=request.properties,
        )
        record = result.single()
        if not record:
            raise HTTPException(status_code=404, detail="One or both nodes not found.")
        return {"relId": record["relId"]}


@app.delete("/admin/graph/relationship")
async def delete_graph_relationship(rel_id: str, _: None = Depends(require_admin)):
    with neo4j_driver.session() as session:
        session.run(
            "MATCH ()-[r]-() WHERE elementId(r) = $rid DELETE r",
            rid=rel_id,
        )
    return {"status": "deleted"}

# ====================== USER KNOWLEDGE GRAPH CONTRIBUTION ======================
class ContributeRequest(BaseModel):
    subject: str
    relation: str
    object_: str
    context: str = ""

def _load_contributions() -> list:
    return list(_mongo_db.contributions.find({}, {"_id": 0}))

def _save_contributions(contributions: list) -> None:
    _mongo_db.contributions.delete_many({})
    if contributions:
        _mongo_db.contributions.insert_many([dict(c) for c in contributions])


@app.post("/contribute")
async def contribute_knowledge(request: ContributeRequest, x_fisherman_id: str = Header(...)):
    await require_approved_user(x_fisherman_id)
    if not request.subject.strip() or not request.relation.strip() or not request.object_.strip():
        raise HTTPException(status_code=400, detail="Subject, relation, and object are required.")
    import time
    contributions = _load_contributions()
    contribution = {
        "id": f"contrib_{int(time.time() * 1000)}",
        "fishermanId": x_fisherman_id,
        "subject": request.subject.strip(),
        "relation": request.relation.strip().upper().replace(" ", "_"),
        "object": request.object_.strip(),
        "context": request.context.strip(),
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    contributions.append(contribution)
    _save_contributions(contributions)
    return {"status": "pending", "message": "Thank you! Your contribution has been submitted for admin review."}


@app.get("/admin/contributions")
async def get_contributions(status: str = "pending", _: None = Depends(require_admin)):
    contributions = _load_contributions()
    return [c for c in contributions if c.get("status") == status]


@app.post("/admin/contributions/review")
async def review_contribution(contribution_id: str, action: str, _: None = Depends(require_admin)):
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'.")
    contributions = _load_contributions()
    contribution = next((c for c in contributions if c["id"] == contribution_id), None)
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribution not found.")

    if action == "approve":
        def to_label(s: str) -> str:
            clean = re.sub(r"[^A-Za-z0-9 ]", "", s).title().replace(" ", "_")
            return clean if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", clean) else "Entity"

        subj_label = to_label(contribution["subject"])
        obj_label  = to_label(contribution["object"])
        rel_type   = _validate_identifier(
            re.sub(r"[^A-Za-z0-9_]", "_", contribution["relation"])
        )
        with neo4j_driver.session() as session:
            session.run(
                f"""
                MERGE (a:{subj_label} {{name: $subj_name}})
                MERGE (b:{obj_label}  {{name: $obj_name}})
                MERGE (a)-[r:{rel_type}]->(b)
                ON CREATE SET r.context = $ctx,
                              r.contributed_by = $uid,
                              r.created_at = $ts
                """,
                subj_name=contribution["subject"],
                obj_name=contribution["object"],
                ctx=contribution.get("context", ""),
                uid=contribution["fishermanId"],
                ts=datetime.now(timezone.utc).isoformat(),
            )
        contribution["status"] = "approved"
    else:
        contribution["status"] = "rejected"

    _save_contributions(contributions)
    return {"status": contribution["status"], "contribution_id": contribution_id}

# ====================== CLOUDFLARE TUNNEL ======================
_tunnel_process: subprocess.Popen | None = None
_tunnel_url: str | None = None


def _monitor_tunnel_stderr(proc: subprocess.Popen) -> None:
    global _tunnel_url
    url_pattern = re.compile(r'https://[a-z0-9\-]+\.trycloudflare\.com')
    for line in iter(proc.stderr.readline, b''):
        line_str = line.decode('utf-8', errors='replace').strip()
        if line_str:
            print(f'[cloudflared] {line_str}')
        if _tunnel_url is None:
            m = url_pattern.search(line_str)
            if m:
                _tunnel_url = m.group(0)


@app.get('/tunnel/status')
async def get_tunnel_status():
    running = _tunnel_process is not None and _tunnel_process.poll() is None
    s = _load_settings()
    named = bool(s.get('tunnel_token', '').strip())
    return {'running': running, 'url': _tunnel_url if running else None, 'mode': 'named' if named else 'quick'}


@app.post('/tunnel/start')
async def start_tunnel():
    global _tunnel_process, _tunnel_url
    if _tunnel_process and _tunnel_process.poll() is None:
        return {'status': 'already_running', 'url': _tunnel_url}

    s = _load_settings()
    token    = s.get('tunnel_token', '').strip()
    hostname = s.get('tunnel_hostname', '').strip()
    named    = bool(token)

    _tunnel_url = None
    cmd = (
        ['cloudflared', 'tunnel', 'run', '--token', token]
        if named
        else ['cloudflared', 'tunnel', '--url', 'http://localhost:8000']
    )
    popen_kwargs = dict(args=cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if sys.platform == 'win32':
        popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(**popen_kwargs)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=(
                'cloudflared binary not found. Download it from '
                'https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ '
                'and make sure it is on your PATH.'
            ),
        )
    _tunnel_process = proc
    threading.Thread(target=_monitor_tunnel_stderr, args=(proc,), daemon=True).start()

    if named:
        await asyncio.sleep(4)
        if proc.poll() is not None:
            raise HTTPException(status_code=500, detail='cloudflared exited unexpectedly. Check your tunnel token.')
        url = ('https://' + hostname) if hostname and not hostname.startswith('http') else hostname
        _tunnel_url = url or 'Named tunnel active'
    else:
        for _ in range(30):
            await asyncio.sleep(0.5)
            if _tunnel_url:
                break
        if proc.poll() is not None:
            _tunnel_url = None
            raise HTTPException(status_code=500, detail='cloudflared exited unexpectedly. Check that cloudflared is installed correctly.')

    return {'status': 'running' if _tunnel_url else 'starting', 'url': _tunnel_url, 'mode': 'named' if named else 'quick'}


@app.post('/tunnel/stop')
async def stop_tunnel():
    global _tunnel_process, _tunnel_url
    if _tunnel_process:
        try:
            _tunnel_process.terminate()
        except Exception:
            pass
        _tunnel_process = None
    _tunnel_url = None
    return {'status': 'stopped'}


# ====================== SETTINGS ENDPOINTS ======================
class SettingsRequest(BaseModel):
    neo4j_mode:           str = "local"
    neo4j_uri:            str
    neo4j_user:           str
    neo4j_password:       str
    neo4j_cloud_uri:      str = ""
    neo4j_cloud_user:     str = ""
    neo4j_cloud_password: str = ""
    tunnel_hostname:      str = ""
    tunnel_token:         str = ""
    ollama_url:           str
    model_name:           str
    google_creds_path:    str = ""
    system_prompt:        str = ""


@app.get("/settings")
async def get_settings(_: None = Depends(require_admin)):
    s = _load_settings()
    return s


@app.post("/settings")
async def update_settings(request: SettingsRequest, _: None = Depends(require_admin)):
    data = request.dict()
    _save_settings_file(data)
    try:
        _apply_settings(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settings saved but failed to reconnect: {e}")
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    if neo4j_driver:
        neo4j_driver.close()
    if _tunnel_process and _tunnel_process.poll() is None:
        try:
            _tunnel_process.terminate()
        except Exception:
            pass
