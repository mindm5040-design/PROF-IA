import streamlit as st
import base64
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="ProfIA — Intelligence pédagogique unifiée", page_icon="◆", layout="centered")

# ========== 1. DESIGN BLANC DOUX ==========
st.markdown("""
<style>
.stApp { background-color: #F6F4EF; color: #26241F; }
section[data-testid="stSidebar"] { background-color: #EFEBE1; border-right: 1px solid #DEDACB; }
h1, h2, h3 { font-family: Georgia, serif; color: #23392F; letter-spacing: 0.01em; }
.stChatMessage {
    background-color: #FFFFFF; border: 1px solid #E4DFD0; border-radius: 10px;
    box-shadow: 0 1px 3px rgba(35,57,47,0.06); padding: 4px 6px;
}
.stButton>button {
    background-color: #23392F; color: #F6F4EF; border: none; font-weight: 600; border-radius: 6px;
    transition: background-color .15s ease;
}
.stButton>button:hover { background-color: #2F5D50; color: #F6F4EF; }
.stTextInput>div>div>input, .stTextArea textarea, .stSelectbox>div>div {
    background-color: #FFFFFF !important; color: #26241F !important; border: 1px solid #DEDACB !important;
    border-radius: 6px !important;
}
[data-testid="stChatInput"] textarea { background-color: #FFFFFF !important; color: #26241F !important; }
.badge {
    display:inline-block; border:1px solid #DEDACB; border-radius:14px; padding:4px 12px;
    font-size:0.75rem; color:#23392F; margin-right:6px; background-color:#FFFFFF; font-weight:600;
}
.stCaption { color: #6B6656 !important; }
</style>
""", unsafe_allow_html=True)

# ========== 2. CLES API (Secrets) ==========
def get_secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return ""

CLAUDE_KEY = get_secret("CLAUDE_KEY")
OPENAI_KEY = get_secret("OPENAI_KEY")
GEMINI_KEY = get_secret("GEMINI_KEY")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
OPENAI_MODEL = "gpt-5.6-sol"
GEMINI_MODEL = "gemini-3.5-flash"

# ========== 3. CONSTITUTION ==========
def build_system_prompt(classe, matiere):
    return f"""Tu es ProfIA v1.0. Le meilleur tuteur scolaire au monde.

RÈGLES STRICTES :
1. MISSION : Faire progresser. Ne donne JAMAIS la réponse directe. Guide par 1 question.
2. ZONE : Scolaire/Universitaire uniquement. Hors-sujet = "Je suis ProfIA, je traite que les cours."
3. ADAPTATION : Détecte la classe {classe}. CP=simple+emojis. Master=rigueur+démo.
4. PSYCHO : Patient, encourageant. Si "je suis nul" → "On bloque sur 1 étape. On la fait ensemble."
5. ANTI-TRICHE : Si "DS", "Contrôle", "Examen" → "Je ne peux pas aider pendant un examen. On révise après ?"
6. VÉRITÉ : Si tu ne sais pas → "Je ne sais pas". Zéro invention.
7. ÉTHIQUE : Zéro pub, zéro biais, données sécurisées Afrique/Europe.
8. PÉDAGOGIE : Montre toujours les étapes. Utilise des exemples locaux.
9. SÉRIEUX : Ton professionnel et posé en toute circonstance. Aucune blague, aucun trait d'humour, aucune plaisanterie — l'usage d'emojis reste réservé au cas CP prévu par la règle 3.

Matière actuelle : {matiere}"""

def extract_pdf_text(file_bytes, max_chars=6000):
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
            if len(text) > max_chars:
                break
        return text[:max_chars].strip()
    except Exception as e:
        return f"[Impossible de lire ce PDF : {e}]"

NIVEAUX = ["CP","CE1","CE2","CM1","CM2","6e","5e","4e","3e","2nde","1ère","Terminale","Licence","Master"]
MATIERES = ["Mathématiques","Physique","SVT","Français","Anglais","Histoire-Géo","Philosophie","Informatique","ECM","Autre"]

# ========== 4. APPELS AUX 3 IA (chacun isolé, ne peut jamais faire planter le site) ==========
def call_claude(system, history, image_b64=None, image_mime=None):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_KEY, max_retries=0, timeout=15.0)
        messages = []
        for m in history:
            content = []
            if m.get("image_b64"):
                content.append({"type":"image","source":{"type":"base64","media_type":m["image_mime"],"data":m["image_b64"]}})
            content.append({"type":"text","text": m["content"] or "Regarde la photo jointe."})
            messages.append({"role": m["role"], "content": content})
        resp = client.messages.create(model=CLAUDE_MODEL, max_tokens=700, system=system, messages=messages)
        return "".join(b.text for b in resp.content if hasattr(b, "text")).strip(), None
    except Exception as e:
        return None, str(e)

def call_openai(system, history):
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_KEY, max_retries=0, timeout=15.0)
        messages = [{"role":"system","content":system}]
        for m in history:
            if m.get("image_b64"):
                messages.append({"role": m["role"], "content":[
                    {"type":"text","text": m["content"] or "Regarde la photo jointe."},
                    {"type":"image_url","image_url":{"url": f"data:{m['image_mime']};base64,{m['image_b64']}"}}
                ]})
            else:
                messages.append({"role": m["role"], "content": m["content"]})
        resp = client.chat.completions.create(model=OPENAI_MODEL, messages=messages, max_tokens=700)
        return resp.choices[0].message.content.strip(), None
    except Exception as e:
        return None, str(e)

def call_gemini(system, history):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)
        contents = []
        for m in history:
            parts = [m["content"] or "Regarde la photo jointe."]
            if m.get("image_b64"):
                parts.append({"mime_type": m["image_mime"], "data": base64.b64decode(m["image_b64"])})
            contents.append({"role": "model" if m["role"]=="assistant" else "user", "parts": parts})
        resp = model.generate_content(contents, request_options={"timeout": 15})
        return resp.text.strip(), None
    except Exception as e:
        return None, str(e)

PROVIDERS = [
    ("claude", CLAUDE_KEY, call_claude),
    ("openai", OPENAI_KEY, call_openai),
    ("gemini", GEMINI_KEY, call_gemini),
]

def fuse_drafts(system, last_text, drafts):
    """Fusionne plusieurs brouillons en une seule réponse, via le premier modèle disponible."""
    fusion_system = system + """

Tu reçois ci-dessous plusieurs brouillons de réponse à la même question d'élève, rédigés indépendamment. Fusionne-les en UNE seule réponse ProfIA optimale : garde le meilleur raisonnement de chaque brouillon, corrige les erreurs éventuelles, élimine les répétitions, et respecte strictement les règles ci-dessus. Ne mentionne jamais qu'il existe plusieurs brouillons ou plusieurs assistants : réponds directement en tant que ProfIA."""
    drafts_text = "\n\n---\n\n".join(f"Brouillon {i+1} :\n{d}" for i, d in enumerate(drafts))
    fusion_history = [{"role":"user", "content": f'Question de l\'élève : "{last_text}"\n\n{drafts_text}', "image_b64": None, "image_mime": None}]
    for name, key, fn in PROVIDERS:
        if not key:
            continue
        if name == "claude":
            text, err = fn(fusion_system, fusion_history)
        else:
            text, err = fn(fusion_system, fusion_history)
        if text:
            return text
    return drafts[0]  # filet de sécurité ultime : jamais de plantage

def get_profia_answer(classe, matiere, history):
    system = build_system_prompt(classe, matiere)
    active = [(n, k, fn) for n, k, fn in PROVIDERS if k]
    if not active:
        return None, "Aucune clé API n'est configurée sur ce serveur (voir .streamlit/secrets.toml)."

    drafts = []
    errors = []
    # Appels en parallèle : le temps d'attente devient celui du modèle le plus lent,
    # pas la somme de tous les modèles.
    with ThreadPoolExecutor(max_workers=len(active)) as executor:
        futures = {executor.submit(fn, system, history): name for name, key, fn in active}
        for future in futures:
            name = futures[future]
            try:
                text, err = future.result()
            except Exception as e:
                text, err = None, str(e)
            if text:
                drafts.append(text)
            else:
                errors.append(f"{name}: {err}")

    if not drafts:
        return None, " | ".join(errors) if errors else "Aucun modèle n'a répondu."

    last_text = history[-1]["content"] if history else ""
    if len(drafts) == 1:
        return drafts[0], None
    try:
        return fuse_drafts(system, last_text, drafts), None
    except Exception:
        return drafts[0], None  # si la fusion échoue, on renvoie quand même une réponse valable

# ========== 5. INTERFACE ==========
st.markdown("## 🌿 ProfIA")
st.caption("Intelligence pédagogique unifiée")

with st.sidebar:
    st.markdown("#### Contexte")
    classe = st.selectbox("Classe", NIVEAUX, index=5)
    matiere = st.selectbox("Matière", MATIERES, index=0)
    fichier = st.file_uploader("Ajouter un fichier (photo ou PDF)", type=["png","jpg","jpeg","pdf"])
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()
    n_active = sum(1 for _, k, _ in PROVIDERS if k)
    st.markdown(f"<span class='badge'>{n_active} modèle(s) actif(s)</span>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"]=="user" else "assistant"):
        st.markdown(msg.get("display") or msg["content"])
        if msg.get("image_b64"):
            st.image(base64.b64decode(msg["image_b64"]))

prompt = st.chat_input("Écris ta question ici...")

if prompt or fichier:
    image_b64, image_mime = None, None
    pdf_text = None
    if fichier:
        raw = fichier.read()
        if fichier.type == "application/pdf":
            pdf_text = extract_pdf_text(raw)
        else:
            image_b64 = base64.b64encode(raw).decode("utf-8")
            image_mime = fichier.type or "image/jpeg"

    user_text = prompt or ("Voici un document, aide-moi." if pdf_text else "Voici une photo de mon exercice, aide-moi.")
    if pdf_text:
        user_text = f"{user_text}\n\n[Contenu du document joint]\n{pdf_text}"
    display_text = prompt or ("📄 Document joint" if pdf_text else "📷 Photo jointe")
    st.session_state.messages.append({"role":"user","content":user_text,"display":display_text,"image_b64":image_b64,"image_mime":image_mime})

    with st.chat_message("user"):
        st.markdown(display_text)
        if image_b64:
            st.image(base64.b64decode(image_b64))

    with st.chat_message("assistant"):
        with st.spinner("ProfIA réfléchit..."):
            answer, error = get_profia_answer(classe, matiere, st.session_state.messages)
        if answer:
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer,"image_b64":None,"image_mime":None})
        else:
            st.error(f"ProfIA n'a pas pu répondre pour le moment. Détail technique : {error}")
