import streamlit as st
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Éric", page_icon="🌿")
st.markdown("## 🌿 Éric")
st.caption("Ton tuteur intelligent - 100% gratuit")

with st.sidebar:
    st.markdown("#### 🔑 Clés gratuites")
    #.strip() enlève les espaces qui causent ton erreur
    groq_key_raw = st.text_input("Groq (gratuit)", type="password", value=st.secrets.get("GROQ_KEY",""), placeholder="gsk_...")
    gemini_key_raw = st.text_input("Gemini (gratuit)", type="password", value=st.secrets.get("GEMINI_KEY",""), placeholder="AIza...")
    groq_key = groq_key_raw.strip()
    gemini_key = gemini_key_raw.strip()

    classe = st.selectbox("Classe", ["CP","6e","3e","Terminale","Licence","Master"], index=2)
    matiere = st.selectbox("Matière", ["Mathématiques","Français","Physique","Autre"])
    if st.button("Effacer discussion"):
        st.session_state.messages = []
        st.rerun()
    if groq_key:
        st.success(f"Groq détectée: {groq_key[:7]}...{groq_key[-4:]}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if not groq_key and not gemini_key:
    st.warning("👈 Mets ta clé Groq à gauche")
    st.stop()

SYSTEM = f"Tu es Éric, tuteur. Classe {classe}, Matière {matiere}. Ne donne pas la réponse directe, guide par question."

def call_groq(history):
    client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    msgs = [{"role":"system","content":SYSTEM}] + [{"role":m["role"],"content":m["content"]} for m in history]
    r = client.chat.completions.create(model="llama-3.1-8b-instant", messages=msgs, max_tokens=600)
    return r.choices[0].message.content

prompt = st.chat_input("Écris ici...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Éric réfléchit..."):
                answer = call_groq(st.session_state.messages) if groq_key else None
                if not answer and gemini_key:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM)
                    answer = model.generate_content([m["content"] for m in st.session_state.messages]).text
                st.markdown(answer)
                st.session_state.messages.append({"role":"assistant","content":answer})
        except Exception as e:
            st.error(f"ERREUR EXACTE: {e}")
            st.info("Copie ce message et envoie-le moi")
