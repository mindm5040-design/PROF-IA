import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Éric", page_icon="🌿")
st.markdown("## 🌿 Éric")
st.caption("Ton tuteur intelligent - sans clé")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    classe = st.selectbox("Classe", ["CP","6e","3e","Terminale","Licence","Master"], index=2)
    matiere = st.selectbox("Matière", ["Mathématiques","Français","Physique","SVT","Autre"])
    if st.button("Effacer"):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

SYSTEM = f"Tu es Éric, tuteur scolaire patient. Classe {classe}, Matière {matiere}. Tu ne donnes jamais la réponse directe, tu guides par une question."

client = OpenAI(base_url="https://text.pollinations.ai/openai", api_key="not-needed")

prompt = st.chat_input("Écris ta question...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Éric réfléchit..."):
            try:
                msgs = [{"role":"system","content":SYSTEM}] + st.session_state.messages
                r = client.chat.completions.create(model="openai", messages=msgs, max_tokens=600)
                ans = r.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Erreur: {e}")
        
