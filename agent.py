import streamlit as st
from groq import Groq
from tavily import TavilyClient
import json

st.title("🤖 Agent AI — szuka w internecie")

groq_key = st.text_input("Klucz Groq:", type="password")
tavily_key = st.text_input("Klucz Tavily:", type="password")

if groq_key and tavily_key:
    groq = Groq(api_key=groq_key)
    tavily = TavilyClient(api_key=tavily_key)

    pytanie = st.chat_input("Zadaj pytanie — Agent przeszuka internet...")

    if pytanie:
        with st.spinner("Agent szuka w internecie..."):
            wyniki = tavily.search(pytanie, max_results=3)
            
            kontekst = ""
            for r in wyniki["results"]:
                kontekst += f"Źródło: {r['url']}\n{r['content']}\n\n"

        with st.chat_message("user"):
            st.write(pytanie)

        with st.spinner("AI analizuje wyniki..."):
            odpowiedz = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{
                    "role": "user",
                    "content": f"Na podstawie tych informacji z internetu odpowiedz na pytanie.\n\nInformacje:\n{kontekst}\n\nPytanie: {pytanie}"
                }]
            )

        with st.chat_message("assistant"):
            st.write(odpowiedz.choices[0].message.content)
            
        with st.expander("📰 Źródła"):
            for r in wyniki["results"]:
                st.write(f"- [{r['title']}]({r['url']})")