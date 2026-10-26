"""
Streamlit chat UI for Hopscotch Assistant.
Run:  streamlit run app.py
"""
import streamlit as st

from api import app
from app import 

st.set_page_config(page_title="Hopscotch Assistant", page_icon="🛍️")
st.title("🛍️ Hopscotch Assistant")

# Streamlit re-runs this whole file on every click, so anything that must
# survive between runs lives in st.session_state.
ss = st.session_state
ss.setdefault("token", None)
ss.setdefault("llm_messages", [])   # full history incl. tool calls (for the LLM)
ss.setdefault("chat", [])           # just the text bubbles (for display)
ss.setdefault("trace", [])          # tool calls from the latest turn

# ---- Login (the token stays here and never goes into the prompt) ----
with st.sidebar:
    st.header("Account")
    if ss.token is None:
        email = st.text_input("Email")
        if st.button("Log in") and email:
            try:
                ss.token = HopscotchClient().login(email)
                ss.email = email
                st.rerun()
            except Exception as e:
                st.error(str(e))
    else:
        st.success(f"Logged in as {ss.email}")
        if st.button("Log out / reset"):
            for k in ("token", "llm_messages", "chat", "trace"):
                ss[k] = None if k == "token" else []
            st.rerun()

    st.header("Tool trace")
    for t in ss.trace:
        with st.expander(f"🔧 {t['tool']} {t['args']}"):
            st.json(t["result"])

if ss.token is None:
    st.info("Log in from the sidebar to start chatting.")
    st.stop()

# ---- Chat ----
for msg in ss.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g. Add 2 backpacks and a t-shirt to my cart"):
    ss.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    ss.llm_messages.append({"role": "user", "content": prompt})
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            client = HopscotchClient(token=ss.token)
            try:
                answer, ss.trace = run_agent(client, ss.llm_messages)
            except Exception as e:
                answer, ss.trace = f"Something went wrong: {e}", []
        st.markdown(answer)
    ss.chat.append({"role": "assistant", "content": answer})
    st.rerun()  # refresh so the sidebar trace shows this turn's tool calls