import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="Éric", page_icon="🌿")
st.markdown("## 🌿 Éric")
st.caption("Sans clé, gratuit")

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

SYSTEM = f"Tu es Éric, tuteur scolaire. Classe {classe}, Matière {matiere}. Ne donne pas la réponse directe, guide par une question. Réponds court."

prompt = st.chat_input("Écris ta question...")
if prompt:
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Éric réfléchit..."):
            try:
                # On construit le prompt complet
                full_prompt = f"{SYSTEM}\n\nHistorique: {st.session_state.messages[-3:]}\n\nQuestion: {prompt}\n\nRéponse d'Éric:"
                url = f"https://text.pollinations.ai/{urllib.parse.quote(full_prompt)}?model=openai&system={urllib.parse.quote(SYSTEM)}"
                r = requests.get(url, timeout=30)
                ans = r.text
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Erreur: {e}")
