import streamlit as st
from openai import OpenAI

st.title("🤖 Mój Chatbot AI")

client = OpenAI(
    api_key=st.text_input("Wpisz klucz Groq API:", type="password"),
    base_url="https://api.groq.com/openai/v1"
)

if "historia" not in st.session_state:
    st.session_state.historia = []

for wiadomosc in st.session_state.historia:
    with st.chat_message(wiadomosc["role"]):
        st.write(wiadomosc["content"])

pytanie = st.chat_input("Napisz coś...")

if pytanie:
    st.session_state.historia.append({"role": "user", "content": pytanie})
    with st.chat_message("user"):
        st.write(pytanie)

    odpowiedz = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=st.session_state.historia
    )

    tekst = odpowiedz.choices[0].message.content
    st.session_state.historia.append({"role": "assistant", "content": tekst})
    with st.chat_message("assistant"):
        st.write(tekst)