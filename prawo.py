import streamlit as st
from groq import Groq
from tavily import TavilyClient

st.set_page_config(page_title="⚖️ Asystent Prawa Dziecka", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
.definicja { background: #1e2a3a; border-radius: 12px; padding: 20px; margin: 10px 0; border-left: 4px solid #2196F3; }
.zrodlo { background: #1a3a2a; border-radius: 12px; padding: 12px; margin: 5px 0; border-left: 4px solid #4CAF50; }
.pytanie { background: #1e3a5f; border-radius: 12px; padding: 12px; margin: 5px 0; }
.odpowiedz { background: #1a3a2a; border-radius: 12px; padding: 12px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("# ⚖️ Asystent Prawa Dziecka")
st.markdown("Definicje, źródła i odpowiedzi na pytania z zakresu prawa dziecka")
st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ Klucze API")
    groq_key = st.text_input("Klucz Groq:", type="password")
    tavily_key = st.text_input("Klucz Tavily:", type="password")
    st.markdown("---")
    st.markdown("### 📚 Jak używać?")
    st.markdown("""
    1. Wpisz pojęcie lub pytanie
    2. AI znajdzie definicję i źródła
    3. Możesz zadawać pytania uzupełniające
    """)

if not groq_key or not tavily_key:
    st.info("👈 Wpisz klucze API w panelu po lewej stronie")
    st.stop()

groq = Groq(api_key=groq_key)
tavily = TavilyClient(api_key=tavily_key)

if "historia" not in st.session_state:
    st.session_state.historia = []
if "wynik" not in st.session_state:
    st.session_state.wynik = None

def szukaj_i_definiuj(pytanie):
    with st.spinner("🔍 Szukam w źródłach prawnych..."):
        wyniki = tavily.search(
            f"prawo dziecka {pytanie} definicja Polska Konwencja Praw Dziecka",
            max_results=5
        )
    
    kontekst = ""
    zrodla = []
    for r in wyniki["results"]:
        kontekst += f"Źródło: {r['url']}\nTytuł: {r['title']}\n{r['content']}\n\n"
        zrodla.append({"tytul": r["title"], "url": r["url"]})
    
    with st.spinner("🧠 Analizuję i przygotowuję definicję..."):
        odpowiedz = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """Jesteś ekspertem prawa dziecka. Na podstawie podanych źródeł:
1. Podaj dokładną definicję prawną
2. Wskaż podstawy prawne (artykuły, ustawy, konwencje)
3. Wyjaśnij praktyczne znaczenie
4. Jeśli możliwe — podaj przykład zastosowania
Odpowiadaj po polsku, precyzyjnie i akademicko."""
                },
                {
                    "role": "user",
                    "content": f"Źródła:\n{kontekst}\n\nPytanie: {pytanie}"
                }
            ]
        )
    
    return odpowiedz.choices[0].message.content, zrodla

tab1, tab2 = st.tabs(["🔍 Szukaj definicji", "💬 Historia wyszukiwań"])

with tab1:
    pytanie = st.text_input(
        "Wpisz pojęcie lub pytanie:",
        placeholder="np. władza rodzicielska, alimenty, prawo do nauki, opieka naprzemienna..."
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        szukaj = st.button("🔍 Szukaj", use_container_width=True, type="primary")
    
    if szukaj and pytanie:
        definicja, zrodla = szukaj_i_definiuj(pytanie)
        st.session_state.wynik = {
            "pytanie": pytanie,
            "definicja": definicja,
            "zrodla": zrodla
        }
        st.session_state.historia.append(st.session_state.wynik)
        st.session_state.historia_czat = []
    
    if st.session_state.wynik:
        wynik = st.session_state.wynik
        
        st.markdown(f"### 📖 Definicja: *{wynik['pytanie']}*")
        st.markdown(f"""<div class="definicja">{wynik['definicja']}</div>""", unsafe_allow_html=True)
        
        st.markdown("### 🔗 Źródła")
        for z in wynik["zrodla"]:
            st.markdown(f"""<div class="zrodlo">
            📄 <a href="{z['url']}" target="_blank" style="color:#64b5f6;">{z['tytul']}</a><br>
            <small style="color:#888;">{z['url']}</small>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🤔 Masz pytanie uzupełniające?")
        
        if "historia_czat" not in st.session_state:
            st.session_state.historia_czat = []
        
        for msg in st.session_state.historia_czat:
            if msg["role"] == "user":
                st.markdown(f"""<div class="pytanie">🙋 <strong>Ty:</strong> {msg["content"]}</div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="odpowiedz">⚖️ <strong>Asystent:</strong> {msg["content"]}</div>""", unsafe_allow_html=True)
        
        pytanie_uzup = st.text_input("Twoje pytanie:", placeholder="np. Czy alimenty można podwyższyć? Jak długo trwa władza rodzicielska?")
        
        if st.button("📨 Zapytaj", use_container_width=True) and pytanie_uzup:
            with st.spinner("Szukam odpowiedzi..."):
                wiadomosci = [
                    {
                        "role": "system",
                        "content": f"Jesteś ekspertem prawa dziecka. Poprzednie pytanie dotyczyło: {wynik['pytanie']}. Definicja: {wynik['definicja'][:500]}. Odpowiadaj po polsku, precyzyjnie."
                    }
                ]
                for msg in st.session_state.historia_czat:
                    wiadomosci.append(msg)
                wiadomosci.append({"role": "user", "content": pytanie_uzup})
                
                odp = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=wiadomosci
                )
                
                st.session_state.historia_czat.append({"role": "user", "content": pytanie_uzup})
                st.session_state.historia_czat.append({"role": "assistant", "content": odp.choices[0].message.content})
                st.rerun()

with tab2:
    st.markdown("### 📚 Historia wyszukiwań")
    
    if not st.session_state.historia:
        st.info("Jeszcze nic nie wyszukałaś!")
    else:
        for i, h in enumerate(reversed(st.session_state.historia)):
            with st.expander(f"⚖️ {h['pytanie']}"):
                st.markdown(h["definicja"])
                st.markdown("**Źródła:**")
                for z in h["zrodla"]:
                    st.markdown(f"- [{z['tytul']}]({z['url']})")
        
        if st.button("🗑️ Wyczyść historię"):
            st.session_state.historia = []
            st.session_state.wynik = None
            st.rerun()