import streamlit as st
from groq import Groq
from gtts import gTTS
from audio_recorder_streamlit import audio_recorder
import base64
import json
import io
from PIL import Image

st.set_page_config(page_title="🇩🇪 Deutsch Lernen", page_icon="🇩🇪", layout="wide")

st.markdown("""
<style>
.slowo-pl { background: #1e3a5f; border-radius: 12px; padding: 15px; text-align: center; }
.slowo-de { background: #1a3a2a; border-radius: 12px; padding: 15px; text-align: center; }
.wymowa { background: #2d1b4e; border-radius: 12px; padding: 12px; margin: 8px 0; }
.gramatyka { background: #3a2000; border-radius: 12px; padding: 12px; margin: 8px 0; border-left: 4px solid #ff9800; }
.slowo-karta { background: #1e2a3a; border-radius: 12px; padding: 15px; margin: 8px 0; border-left: 4px solid #4CAF50; }
.przyklad { background: #1a2a1a; border-radius: 12px; padding: 15px; margin: 8px 0; border-left: 4px solid #2196F3; }
.czat-pytanie { background: #1e3a5f; border-radius: 12px; padding: 12px; margin: 5px 0; }
.czat-odpowiedz { background: #1a3a2a; border-radius: 12px; padding: 12px; margin: 5px 0; }
.big-text { font-size: 28px; font-weight: bold; color: white; }
.label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🇩🇪 Deutsch Lernen — Twój Asystent Niemieckiego")
st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ Ustawienia")
    groq_key = st.text_input("Klucz Groq API:", type="password")
    st.markdown("---")
    st.markdown("### 📊 Statystyki")
    if "historia" in st.session_state:
        st.metric("Przetłumaczone słówka", len(st.session_state.historia))

if not groq_key:
    st.info("👈 Wpisz klucz Groq API w panelu po lewej stronie aby zacząć")
    st.stop()

client = Groq(api_key=groq_key)

if "historia" not in st.session_state:
    st.session_state.historia = []
if "tekst" not in st.session_state:
    st.session_state.tekst = ""
if "wynik" not in st.session_state:
    st.session_state.wynik = None
if "czat_gramatyka" not in st.session_state:
    st.session_state.czat_gramatyka = []

def tlumacz(tekst):
    odpowiedz = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Przetłumacz na niemiecki: "{tekst}"
Odpowiedz TYLKO w tym formacie JSON:
{{"niemieckie": "tłumaczenie", "wymowa": "fonetyczna wymowa po polsku", "przyklad": "dodatkowe zdanie po niemiecku", "przyklad_pl": "tłumaczenie przykładu", "slowa": [{{"polskie": "słowo", "niemieckie": "słowo", "wymowa": "[wymowa]", "czesc_mowy": "np. rzeczownik/czasownik/przymiotnik", "rodzaj": "np. der/die/das lub brak", "gramatyka": "krótkie wyjaśnienie po polsku"}}], "gramatyka_zdania": "szczegółowe wyjaśnienie budowy zdania po polsku"}}"""
        }]
    )
    return json.loads(odpowiedz.choices[0].message.content)

def czytaj_po_niemiecku(tekst):
    tts = gTTS(text=tekst, lang='de')
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    audio_b64 = base64.b64encode(buf.read()).decode()
    return f'<audio autoplay controls><source src="data:audio/mp3;base64,{audio_b64}"></audio>'

def zapytaj_o_gramatyke(pytanie, kontekst):
    odpowiedz = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"Jesteś nauczycielem języka niemieckiego. Odpowiadasz po polsku. Kontekst: przetłumaczono zdanie '{kontekst['polskie']}' na '{kontekst['niemieckie']}'. Gramatyka: {kontekst.get('gramatyka_zdania', '')}. Odpowiadaj krótko i jasno."
            },
            {
                "role": "user",
                "content": pytanie
            }
        ]
    )
    return odpowiedz.choices[0].message.content

tab1, tab2, tab3 = st.tabs(["✍️ Tłumacz", "📸 Zdjęcie", "📚 Historia słówek"])

with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 🎤 Nagraj lub wpisz")
        audio = audio_recorder(text="Kliknij i mów po polsku", pause_threshold=2.0)

        if audio:
            with st.spinner("🎧 Rozpoznaję mowę..."):
                rozpoznane = client.audio.transcriptions.create(
                    file=("audio.wav", audio, "audio/wav"),
                    model="whisper-large-v3",
                    language="pl"
                )
                st.session_state.tekst = rozpoznane.text
                st.session_state.czat_gramatyka = []
                st.success(f"✅ Rozpoznałam: **{st.session_state.tekst}**")

        tekst_input = st.text_area("✏️ Wpisz po polsku:", value=st.session_state.tekst, height=100, placeholder="np. Gdzie jest dworzec kolejowy?")
        if tekst_input != st.session_state.tekst:
            st.session_state.tekst = tekst_input

        if st.button("🔄 Tłumacz na niemiecki", use_container_width=True, type="primary"):
            if st.session_state.tekst:
                with st.spinner("🧠 Tłumaczę i analizuję gramatykę..."):
                    wynik = tlumacz(st.session_state.tekst)
                    st.session_state.wynik = wynik
                    st.session_state.czat_gramatyka = []
                    st.session_state.historia.append({"polskie": st.session_state.tekst, **wynik})

    with col_right:
        if st.session_state.wynik:
            wynik = st.session_state.wynik
            st.markdown("### 🎯 Tłumaczenie")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="slowo-pl"><div class="label">🇵🇱 Polski</div><div class="big-text">{st.session_state.tekst}</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="slowo-de"><div class="label">🇩🇪 Deutsch</div><div class="big-text">{wynik['niemieckie']}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="wymowa">📢 <strong>Wymowa:</strong> {wynik['wymowa']}</div>""", unsafe_allow_html=True)
            st.markdown(czytaj_po_niemiecku(wynik["niemieckie"]), unsafe_allow_html=True)

    if st.session_state.wynik:
        wynik = st.session_state.wynik
        st.markdown("---")
        col_gram, col_slowa = st.columns([1, 1])

        with col_gram:
            st.markdown("### 📖 Analiza gramatyczna zdania")
            st.markdown(f"""<div class="gramatyka">{wynik.get('gramatyka_zdania', '')}</div>""", unsafe_allow_html=True)

            st.markdown("### 💬 Przykład użycia")
            st.markdown(f"""<div class="przyklad"><div style="font-size:18px; color:#64b5f6;">🇩🇪 {wynik['przyklad']}</div><div style="color:#aaa; margin-top:8px;">🇵🇱 {wynik['przyklad_pl']}</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### 🤔 Zapytaj o gramatykę")
            st.caption("Masz pytanie do tego zdania? Zapytaj tutaj!")

            for msg in st.session_state.czat_gramatyka:
                if msg["role"] == "user":
                    st.markdown(f"""<div class="czat-pytanie">🙋 <strong>Ty:</strong> {msg["content"]}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="czat-odpowiedz">🎓 <strong>Nauczyciel:</strong> {msg["content"]}</div>""", unsafe_allow_html=True)

            pytanie_gram = st.text_input("Twoje pytanie:", placeholder="np. Dlaczego używamy möchte a nie will?", key="pytanie_gram_input")
            if st.button("📨 Zapytaj", use_container_width=True) and pytanie_gram:
                with st.spinner("Nauczyciel odpowiada..."):
                    kontekst = {
                        "polskie": st.session_state.tekst,
                        "niemieckie": wynik["niemieckie"],
                        "gramatyka_zdania": wynik.get("gramatyka_zdania", "")
                    }
                    odpowiedz = zapytaj_o_gramatyke(pytanie_gram, kontekst)
                    st.session_state.czat_gramatyka.append({"role": "user", "content": pytanie_gram})
                    st.session_state.czat_gramatyka.append({"role": "assistant", "content": odpowiedz})
                    st.rerun()

        with col_slowa:
            st.markdown("### 🔤 Słowa jedno po drugim")
            for i, slowo in enumerate(wynik.get("slowa", [])):
                st.markdown(f"""<div class="slowo-karta">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:16px;">🇵🇱 <strong>{slowo['polskie']}</strong> → 🇩🇪 <strong>{slowo['niemieckie']}</strong></span>
                    <span style="background:#2d4a2d; padding:3px 8px; border-radius:8px; font-size:12px;">{slowo.get('czesc_mowy','')}</span>
                </div>
                <div style="color:#a8c7a8; margin-top:5px;">📢 {slowo['wymowa']}</div>
                {"<div style='color:#ffb74d; margin-top:3px;'>🔖 Rodzaj: " + slowo['rodzaj'] + "</div>" if slowo.get('rodzaj') else ""}
                <div style="color:#888; margin-top:5px; font-size:13px;">📝 {slowo['gramatyka']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button("🔊", key=f"play_{i}"):
                    st.markdown(czytaj_po_niemiecku(slowo["niemieckie"]), unsafe_allow_html=True)

with tab2:
    st.markdown("### 📸 Wrzuć zdjęcie — AI opisze i przetłumaczy")
    zdjecie = st.file_uploader("Wybierz zdjęcie", type=["jpg", "jpeg", "png"])
    if zdjecie:
        col_img, col_opis = st.columns([1, 1])
        with col_img:
            img = Image.open(zdjecie)
            st.image(img, caption="Twoje zdjęcie", use_column_width=True)
        with col_opis:
            if st.button("🔍 Analizuj i przetłumacz", use_container_width=True, type="primary"):
                with st.spinner("🧠 Analizuję zdjęcie..."):
                    odpowiedz = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": "Opisz krótko co widzisz na zdjęciu po polsku, a potem podaj 5 głównych słów po niemiecku z wymową i rodzajnikiem. Format:\n🇵🇱 Opis: ...\n\n🇩🇪 Słówka:\n- polskie = der/die/das niemieckie [wymowa]"}]
                    )
                    st.markdown(odpowiedz.choices[0].message.content)

with tab3:
    st.markdown("### 📚 Historia Twoich słówek")
    if not st.session_state.historia:
        st.info("🌱 Jeszcze nie przetłumaczyłaś żadnego słówka!")
    else:
        st.metric("Łącznie słówek", len(st.session_state.historia))
        st.markdown("---")
        for i, s in enumerate(reversed(st.session_state.historia)):
            with st.expander(f"🇵🇱 {s['polskie']} → 🇩🇪 {s['niemieckie']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"📢 **Wymowa:** {s['wymowa']}")
                    st.write(f"💬 {s['przyklad']}")
                with col2:
                    if st.button("🔊 Posłuchaj", key=f"hist_{i}"):
                        st.markdown(czytaj_po_niemiecku(s["niemieckie"]), unsafe_allow_html=True)
        if st.button("🗑️ Wyczyść historię", type="secondary"):
            st.session_state.historia = []
            st.session_state.wynik = None
            st.session_state.czat_gramatyka = []
            st.rerun()