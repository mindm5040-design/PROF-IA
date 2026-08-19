import streamlit as st
import base64
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Éric — Intelligence pédagogique unifiée", page_icon="◆", layout="centered")

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
    transition: background-color.15s ease;
}
.stButton>button:hover { background-color: #2F5D50; color: #F6F4EF; }
.stTextInput>div>div>input,.stTextArea textarea,.stSelectbox>div>div {
    background-color: #FFFFFF!important; color: #26241F!important; border: 1px solid #DEDACB!important;
    border-radius: 6px!important;
}
[data-testid="stChatInput"] textarea { background-color: #FFFFFF!important; color: #26241F!important; }
.badge {
    display:inline-block; border:1px solid #DEDACB; border-radius:14px; padding:4px 12px;
    font-size:0.75rem; color:#23392F; margin-right:6px; background-color:#FFFFFF; font-weight:600;
}
.stCaption { color: #6B6656!important; }
</style>
""", unsafe_allow_html=True)

# ========== 2. SYSTEME DE CLES (SANS SECRETS) ==========
with st.sidebar:
    st.markdown("#### 🔑 Tes clés API")
    st.caption("Les clés restent sur ton navigateur, non sauvegardées.")

    def get_secret_safe(name):
        try:
            return st.secrets.get(name, "")
        except Exception:
            return ""

    CLAUDE_KEY = st.text_input("Claude Key", value=get_secret_safe("CLAUDE_KEY"), type="password", placeholder="sk-ant-...")
    OPENAI_KEY = st.text_input("OpenAI Key", value=get_secret_safe("OPENAI_KEY"), type="password", placeholder="sk-proj-...")
    GEMINI_KEY = st.text_input("Gemini Key", value=get_secret_safe("GEMINI_KEY"), type="password", placeholder="AIza...")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-1.5-flash"

# ========== 3. CONSTITUTION DE ÉRIC ==========
def build_system_prompt(classe, matiere):
    return f"""Tu es Éric. Le meilleur tuteur scolaire au monde. Tu t'appelles Éric.

RÈGLES STRICTES :
1. MISSION : Faire progresser. Ne donne JAMAIS la réponse directe. Guide par 1 question.
2. ZONE : Scolaire/Universitaire uniquement. Hors-sujet = "Je suis Éric, je traite que les cours."
3. ADAPTATION : Détecte la classe {classe}. CP=simple+emojis. Master=rigueur+démo.
4. PSYCHO : Patient, encourageant. Si "je suis nul" → "On bloque sur 1 étape. On la fait ensemble."
5. ANTI-TRICHE : Si "DS", "Contrôle", "Examen" → "Je ne peux pas aider pendant un examen. On révise après?"
6. VÉRITÉ : Si tu ne sais pas → "Je ne sais pas". Zéro invention.
7. ÉTHIQUE : Zéro pub, zéro biais, données sécurisées Afrique/Europe.
8. PÉDAGOGIE : Montre toujours les étapes. Utilise des exemples locaux.
9. IDENTITÉ : Tu t'appelles Éric. Si on te demande qui tu es, tu réponds "Je suis Éric". Tu ne mentionnes jamais ProfIA.
10. SÉRIEUX : Ton professionnel et posé en toute circonstance. Aucune blague, aucun trait d'humour, aucune plaisanterie — l'usage d'emojis reste réservé au cas CP prévu par la règle 3.

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

# ========== 4. APPELS AUX 3 IA ==========
def call_claude(system, history, key):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key, max_retries=0, timeout=20.0)
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

def call_openai(system, history, key):
    try:
        import openai
        client = openai.OpenAI(api_key=key, max_retries=0, timeout=20.0)
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

def call_gemini(system, history, key):
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)
        contents = []
        for m in history:
            parts = [m["content"] or "Regarde la photo jointe."]
            if m.get("image_b64"):
                parts.append({"mime_type": m["image_mime"], "data": base64.b64decode(m["image_b64"])})
            contents.append({"role": "model" if m["role"]=="assistant" else "user", "parts": parts})
        resp = model.generate_content(contents, request_options={"timeout": 20})
        return resp.text.strip(), None
    except Exception as e:
        return None, str(e)

def fuse_drafts(system, last_text, drafts, keys_dict):
    fusion_system = system + "\n\nTu reçois plusieurs brouillons. Fusionne-les en UNE seule réponse Éric optimale. Ne mentionne jamais les brouillons."
    drafts_text = "\n\n---\n\n".join(f"Brouillon {i+1} :\n{d}" for i, d in enumerate(drafts))
    fusion_history = [{"role":"user", "content": f'Question : "{last_text}"\n\n{drafts_text}', "image_b64": None, "image_mime": None}]
    if keys_dict.get("claude"):
        text, _ = call_claude(fusion_system, fusion_history, keys_dict["claude"])
        if text: return text
    if keys_dict.get("openai"):
        text, _ = call_openai(fusion_system, fusion_history, keys_dict["openai"])
        if text: return text
    if keys_dict.get("gemini"):
        text, _ = call_gemini(fusion_system, fusion_history, keys_dict["gemini"])
        if text: return text
    return drafts[0]

def get_profia_answer(classe, matiere, history, keys_dict):
    system = build_system_prompt(classe, matiere)
    active = []
    if keys_dict.get("claude"): active.append(("claude", keys_dict["claude"], call_claude))
    if keys_dict.get("openai"): active.append(("openai", keys_dict["openai"], call_openai))
    if keys_dict.get("gemini"): active.append(("gemini", keys_dict["gemini"], call_gemini))
    if not active:
        return None, "Aucune clé API entrée. Mets au moins 1 clé dans la barre à gauche."
    drafts = []
    errors = []
    with ThreadPoolExecutor(max_workers=len(active)) as executor:
        futures = {executor.submit(fn, system, history, key): name for name, key, fn in active}
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
        return None, " | ".join(errors)
    last_text = history[-1]["content"] if history else ""
    if len(drafts) == 1:
        return drafts[0], None
    try:
        return fuse_drafts(system, last_text, drafts, keys_dict), None
    except Exception:
        return drafts[0], None

# ========== 5. INTERFACE ==========
st.markdown("## 🌿 Éric")
st.caption("Ton tuteur intelligent, pour toutes les classes")

with st.sidebar:
    st.divider()
    st.markdown("#### Contexte")
    classe = st.selectbox("Classe", NIVEAUX, index=5)
    matiere = st.selectbox("Matière", MATIERES, index=0)
    fichier = st.file_uploader("Ajouter un fichier (photo ou PDF)", type=["png","jpg","jpeg","pdf"])
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()
    n_active = sum(1 for k in [CLAUDE_KEY, OPENAI_KEY, GEMINI_KEY] if k)
    st.markdown(f"<span class='badge'>{n_active} modèle(s) actif(s)</span>", unsafe_allow_html=True)
    if n_active == 0:
        st.warning("Entre au moins 1 clé pour démarrer")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"]=="user" else "assistant"):
        st.markdown(msg.get("display") or msg["content"])
        if msg.get("image_b64"):
            st.image(base64.b64decode(msg["image_b64"]))

prompt = st.chat_input("Écris ta question ici...")

if prompt or fichier:
    if not (CLAUDE_KEY or OPENAI_KEY or GEMINI_KEY):
        st.error("Entre d'abord ta clé API dans le menu à gauche.")
        st.stop()

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
        with st.spinner("Éric réfléchit..."):
            keys_dict = {"claude": CLAUDE_KEY, "openai": OPENAI_KEY, "gemini": GEMINI_KEY}
            answer, error = get_profia_answer(classe, matiere, st.session_state.messages, keys_dict)
        if answer:
            st.markdown(answer)
            st.session_state.messages.append({"role":"assistant","content":answer,"image_b64":None,"image_mime":None})
        else:
            st.error(f"Éric n'a pas pu répondre. Détail : {error}")
