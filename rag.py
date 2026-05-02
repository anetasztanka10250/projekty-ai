import streamlit as st
from groq import Groq
import PyPDF2

st.title("📄 AI czyta Twoje dokumenty")

client = Groq(api_key=st.text_input("Wpisz klucz Groq API:", type="password"))

uploaded_file = st.file_uploader("Wrzuć plik PDF", type="pdf")

if uploaded_file:
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    tekst = ""
    for strona in pdf_reader.pages:
        tekst += strona.extract_text()

    st.success(f"Wczytano {len(pdf_reader.pages)} stron!")

    if "historia" not in st.session_state:
        st.session_state.historia = []

    for msg in st.session_state.historia:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    pytanie = st.chat_input("Zadaj pytanie o dokument...")

    if pytanie:
        prompt = f"Dokument:\n{tekst[:8000]}\n\nPytanie: {pytanie}"
        st.session_state.historia.append({"role": "user", "content": pytanie})

        odpowiedz = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        tekst_odpowiedzi = odpowiedz.choices[0].message.content
        st.session_state.historia.append({"role": "assistant", "content": tekst_odpowiedzi})

        with st.chat_message("user"):
            st.write(pytanie)
        with st.chat_message("assistant"):
            st.write(tekst_odpowiedzi)