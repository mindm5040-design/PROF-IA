import streamlit as st
from openai import OpenAI
import google.generativeai as genai

st.set_page_config(page_title="Éric", page_icon="🌿", layout="centered")
st.markdown("## 🌿 Éric")
st.caption("Ton tuteur intelligent - 100% gratuit")

with st.sidebar:
    st.markdown("#### 🔑 Clés gratuites")
    groq_key = st.text_input("Groq (gratuit)", type="password", value=st.secrets.get("GROQ_KEY",""), placeholder="gsk_...")
    gemini_key = st.text_input("Gemini (gratuit)", type="password", value=st.secrets.get("GEMINI_KEY",""), placeholder="AIza...")

    classe = st.selectbox("Classe", ["CP","6e","3e","Terminale","Licence","Master"], index=2)
    matiere = st.selectbox("Matière", ["Mathématiques","Français","Physique","SVT","Autre"])
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if not groq_key and not gemini_key:
    st.warning("👈 Mets au moins une clé Groq ou Gemini à gauche. Les deux sont gratuites.")
    st.info("Groq: console.groq.com/keys\nGemini: aistudio.google.com/app/apikey")
    st.stop()

SYSTEM = f"Tu es Éric, le meilleur tuteur scolaire. Classe: {classe}, Matière: {matiere}. Ne donne JAMAIS la réponse directe, guide par 1 question. Patient, encourageant. Tu t'appelles Éric."

def call_groq(prompt_history):
    try:
        client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        msgs = [{"role":"system","content":SYSTEM}] + [{"role":m["role"],"content":m["content"]} for m in prompt_history]
        resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=msgs, max_tokens=600)
        return resp.choices[0].message.content
    except Exception as e:
        return None

def call_gemini(prompt_history):
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM)
        resp = model.generate_content([m["content"] for m in prompt_history])
        return resp.text
    except Exception as e:
        return None

prompt = st.chat_input("Écris ta question ici...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Éric réfléchit..."):
            answer = None
            if groq_key:
                answer = call_groq(st.session_state.messages)
            if not answer and gemini_key:
                answer = call_gemini(st.session_state.messages)

            if answer:
                st.markdown(answer)
                st.session_state.messages.append({"role":"assistant","content":answer})
            else:
                st.error("Les clés sont invalides. Vérifie console.groq.com")
