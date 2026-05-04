import streamlit as st
from groq import Groq
from tavily import TavilyClient
from PIL import Image, ImageEnhance
from rembg import remove
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import json

st.set_page_config(page_title="Sweet Analytics", page_icon="🍰", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.hero { background: white; border-radius: 16px; padding: 32px; margin-bottom: 24px; border: 1px solid #e5e7eb; }
.hero h1 { font-size: 28px; font-weight: 700; color: #111827; margin: 0; }
.hero p { color: #6b7280; margin: 8px 0 0; font-size: 15px; }
.metryka { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; text-align: center; }
.metryka .liczba { font-size: 32px; font-weight: 700; color: #111827; }
.metryka .label { font-size: 13px; color: #6b7280; margin-top: 4px; }
.sekcja { background: white; border-radius: 12px; padding: 24px; margin: 16px 0; border: 1px solid #e5e7eb; }
.sekcja h3 { font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 16px; }
.insight { background: #f9fafb; border-radius: 8px; padding: 14px 16px; margin: 8px 0; border-left: 3px solid #6366f1; }
.insight.success { border-left-color: #10b981; }
.insight.warning { border-left-color: #f59e0b; }
.insight.danger { border-left-color: #ef4444; }
.insight.tip { border-left-color: #3b82f6; }
.krok { background: white; border-radius: 10px; padding: 16px; margin: 10px 0; border: 1px solid #e5e7eb; display: flex; gap: 12px; align-items: flex-start; }
.krok-numer { background: #111827; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0; }
.krok-tresc h4 { font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.krok-tresc p { font-size: 13px; color: #6b7280; margin: 0; }
.plan-dzien { background: #f9fafb; border-radius: 8px; padding: 12px 16px; margin: 6px 0; border: 1px solid #e5e7eb; }
.plan-dzien .data { font-size: 12px; color: #6b7280; font-weight: 500; }
.plan-dzien .temat { font-size: 14px; font-weight: 600; color: #111827; margin: 4px 0; }
.plan-dzien .szczegoly { font-size: 13px; color: #6b7280; }
.tag { padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
.tag-green { background: #d1fae5; color: #065f46; }
.tag-blue { background: #dbeafe; color: #1e40af; }
.tag-orange { background: #ffedd5; color: #9a3412; }
.sticker { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; margin: 2px; background: #f3f4f6; color: #374151; }
.post-viral { background: white; border-radius: 12px; padding: 20px; margin: 12px 0; border: 1px solid #e5e7eb; border-top: 3px solid #6366f1; }
.post-viral .liczba-viral { font-size: 24px; font-weight: 700; color: #6366f1; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🍰 Sweet Analytics")
    st.markdown("---")
    groq_key = st.text_input("Klucz Groq:", type="password")
    tavily_key = st.text_input("Klucz Tavily:", type="password")
    st.markdown("---")
    st.markdown("**Profil cukierni**")
    nazwa = st.text_input("Nazwa:", placeholder="np. Słodki Zakątek")
    miasto = st.text_input("Miasto:", placeholder="np. Poznań")
    specjalizacja = st.multiselect("Specjalizacja:",
        ["Torty weselne", "Torty urodzinowe", "Macarons", "Cupcakes", "Ciasta", "Desery", "Tarty", "Croissanty"],
        default=["Torty urodzinowe"])
    styl_profilu = st.selectbox("Styl profilu:", ["Elegancki i luksusowy", "Ciepły i rodzinny", "Nowoczesny i minimalistyczny", "Kolorowy i radosny"])

if not groq_key or not tavily_key:
    st.markdown("""<div class="hero"><h1>🍰 Sweet Analytics</h1><p>Profesjonalna platforma AI do zarządzania social mediami cukierni</p></div>""", unsafe_allow_html=True)
    st.info("👈 Wpisz klucze API i dane cukierni w panelu po lewej stronie")
    st.stop()

groq = Groq(api_key=groq_key)
tavily = TavilyClient(api_key=tavily_key)

st.markdown(f"""<div class="hero"><h1>🍰 {nazwa if nazwa else 'Sweet Analytics'}</h1><p>Profesjonalna platforma AI do social mediów · {miasto if miasto else ''}</p></div>""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Analiza & Strategia",
    "✍️ Generator treści",
    "📅 Kalendarz",
    "🔍 Trendy & Viral",
    "🎯 Plan działania",
    "🖼️ Edycja zdjęć",
    "📋 Generator ofert PDF"
])

# TAB 1 - ANALIZA
with tab1:
    st.markdown('<div class="sekcja"><h3>📊 Analiza rynku i rekomendacje strategiczne</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        temat_analizy = st.text_input("Co chcesz przeanalizować?", placeholder="np. torty weselne Instagram, cukiernia Poznań")
    with col2:
        typ_analizy = st.selectbox("Typ analizy:", ["Pełna analiza strategiczna", "Co publikować żeby mieć więcej klientów", "Analiza hashtagów", "Najlepsze godziny publikacji", "Analiza Stories vs Reels vs Posty"])

    if st.button("🔍 Analizuj", use_container_width=True, type="primary", key="btn_analiza"):
        with st.spinner("Analizuję Instagram i trendy branżowe..."):
            wyniki = tavily.search(f"cukiernia Instagram {temat_analizy} strategia posty 2025", max_results=6)
            kontekst = "\n\n".join([f"{r['title']}\n{r['content']}" for r in wyniki["results"]])
            odp = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Jesteś ekspertem social media dla cukierni '{nazwa}' w {miasto}. Odpowiadaj jak profesjonalny konsultant marketingowy z konkretnymi danymi."},
                    {"role": "user", "content": f"""Na podstawie danych z internetu:
{kontekst}

Wykonaj: {typ_analizy}

Odpowiedz TYLKO w JSON:
{{"ocena_ogolna": "A/B/C/D", "glowny_wniosek": "jedno zdanie", "mocne_strony": ["punkt 1", "punkt 2", "punkt 3"], "slabe_strony": ["punkt 1", "punkt 2"], "rekomendacje": [{{"priorytet": "WYSOKI/SREDNI/NISKI", "akcja": "co zrobić", "dlaczego": "uzasadnienie", "efekt": "rezultat"}}], "content_mix": {{"reels": "X%", "posty": "X%", "stories": "X%", "karuzele": "X%"}}, "najlepsze_godziny": ["gg:mm dzień"], "top_hashtagi": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"]}}"""}
                ]
            )
            try:
                tekst = odp.choices[0].message.content
                czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                dane = json.loads(czysty)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f'<div class="metryka"><div class="liczba">{dane.get("ocena_ogolna","B")}</div><div class="label">Ocena strategii</div></div>', unsafe_allow_html=True)
                with col2:
                    cm = dane.get('content_mix', {})
                    st.markdown(f'<div class="metryka"><div class="liczba">{cm.get("reels","40%")}</div><div class="label">Reels (zalecane)</div></div>', unsafe_allow_html=True)
                with col3:
                    godz = dane.get('najlepsze_godziny', ['18:00'])
                    st.markdown(f'<div class="metryka"><div class="liczba">{godz[0]}</div><div class="label">Najlepsza godzina</div></div>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="metryka"><div class="liczba">{len(dane.get("rekomendacje",[]))}</div><div class="label">Rekomendacji</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="insight tip">💡 <strong>Wniosek:</strong> {dane.get("glowny_wniosek","")}</div>', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**✅ Mocne strony**")
                    for m in dane.get('mocne_strony', []):
                        st.markdown(f'<div class="insight success">✓ {m}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown("**⚠️ Do poprawy**")
                    for s in dane.get('slabe_strony', []):
                        st.markdown(f'<div class="insight warning">⚠ {s}</div>', unsafe_allow_html=True)
                st.markdown("**🎯 Rekomendacje**")
                for r in dane.get('rekomendacje', []):
                    kolor = "danger" if r.get('priorytet') == 'WYSOKI' else "warning" if r.get('priorytet') == 'SREDNI' else "tip"
                    st.markdown(f'<div class="insight {kolor}"><strong>[{r.get("priorytet","")}] {r.get("akcja","")}</strong><br><span style="color:#6b7280;font-size:13px;">📌 {r.get("dlaczego","")} · 📈 {r.get("efekt","")}</span></div>', unsafe_allow_html=True)
                hashtagi = dane.get('top_hashtagi', [])
                html_tags = " ".join([f'<span class="sticker">#{h.replace("#","")}</span>' for h in hashtagi])
                st.markdown(f"**#️⃣ Top hashtagi:** {html_tags}", unsafe_allow_html=True)
            except:
                st.write(odp.choices[0].message.content)

# TAB 2 - GENERATOR
with tab2:
    st.markdown('<div class="sekcja"><h3>✍️ Generator profesjonalnych treści</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        zdjecie = st.file_uploader("📸 Zdjęcie wyrobu:", type=["jpg","jpeg","png"], key="gen_zdj")
        if zdjecie:
            st.image(Image.open(zdjecie), use_container_width=True)
        produkt = st.text_input("Produkt:", placeholder="np. tort czekoladowy z malinami")
        okazja = st.selectbox("Okazja:", ["Bez okazji", "Urodziny", "Ślub", "Walentynki", "Wielkanoc", "Boże Narodzenie", "Komunia", "Nowy produkt"])
        format_posta = st.selectbox("Format:", ["Post na feed", "Reel (opis)", "Story", "Karuzela"])
        if st.button("✨ Generuj treść", use_container_width=True, type="primary", key="btn_gen") and produkt:
            with st.spinner("Tworzę profesjonalną treść..."):
                odp = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Jesteś ekspertem content marketingu dla cukierni '{nazwa}' w {miasto}. Styl: {styl_profilu}."},
                        {"role": "user", "content": f"""Stwórz treść na Instagram.
Produkt: {produkt}, Okazja: {okazja}, Format: {format_posta}

TYLKO JSON:
{{"glowny_podpis": "podpis 3-4 zdania z emoji", "cta": "wezwanie do działania", "hashtagi_glowne": ["5 hashtagów"], "hashtagi_dodatkowe": ["15 hashtagów"], "najlepsza_godzina": "gg:mm dzień", "muzyka_reel": "propozycja muzyki", "wskazowka_foto": "jak zrobić idealne zdjęcie", "alternatywny_podpis": "drugi wariant"}}"""}
                    ]
                )
                try:
                    tekst = odp.choices[0].message.content
                    czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                    dane = json.loads(czysty)
                    with col2:
                        st.markdown("**📝 Podpis główny:**")
                        st.text_area("", dane.get('glowny_podpis',''), height=120, key="p1")
                        st.markdown(f"**💬 CTA:** {dane.get('cta','')}")
                        st.markdown(f"**⏰ Godzina:** {dane.get('najlepsza_godzina','')}")
                        st.markdown(f"**🎵 Muzyka:** {dane.get('muzyka_reel','')}")
                        st.markdown(f"**📸 Wskazówka foto:** {dane.get('wskazowka_foto','')}")
                        wszystkie = dane.get('hashtagi_glowne',[]) + dane.get('hashtagi_dodatkowe',[])
                        st.text_area("**#️⃣ Hashtagi:**", " ".join(wszystkie), height=80, key="h1")
                        st.markdown("**📝 Alternatywny podpis:**")
                        st.text_area("", dane.get('alternatywny_podpis',''), height=100, key="p2")
                except:
                    with col2:
                        st.write(odp.choices[0].message.content)

# TAB 3 - KALENDARZ
with tab3:
    st.markdown('<div class="sekcja"><h3>📅 Inteligentny kalendarz treści</h3></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        miesiac = st.selectbox("Miesiąc:", ["Styczeń","Luty","Marzec","Kwiecień","Maj","Czerwiec","Lipiec","Sierpień","Wrzesień","Październik","Listopad","Grudzień"])
    with col2:
        czestotliwosc = st.selectbox("Częstotliwość:", ["3 posty/tydzień","5 postów/tydzień","Codziennie"])
    with col3:
        cel = st.selectbox("Cel:", ["Zwiększenie sprzedaży","Budowanie społeczności","Nowe produkty","Sezonowa kampania"])
    if st.button("📅 Generuj kalendarz", use_container_width=True, type="primary", key="btn_kal"):
        with st.spinner("Planuję kalendarz treści..."):
            odp = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Jesteś strategiem content marketingu dla cukierni '{nazwa}'."},
                    {"role": "user", "content": f"""Kalendarz na {miesiac}, {czestotliwosc}, cel: {cel}, specjalizacja: {', '.join(specjalizacja)}.

TYLKO JSON:
{{"strategia_miesiaca": "jedno zdanie", "posty": [{{"tydzien": 1, "data": "3 stycznia (środa)", "format": "Reel/Post/Story", "temat": "temat", "produkt": "co pokazać", "godzina": "18:00", "cel_posta": "sprzedaż/zasięg/zaangażowanie", "wskazowka": "wskazówka wykonania"}}]}}"""}
                ]
            )
            try:
                tekst = odp.choices[0].message.content
                czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                dane = json.loads(czysty)
                st.markdown(f'<div class="insight tip">📌 <strong>Strategia:</strong> {dane.get("strategia_miesiaca","")}</div>', unsafe_allow_html=True)
                tygodnie = {}
                for p in dane.get('posty', []):
                    t = p.get('tydzien', 1)
                    if t not in tygodnie:
                        tygodnie[t] = []
                    tygodnie[t].append(p)
                for tydzien, posty_t in tygodnie.items():
                    st.markdown(f"**Tydzień {tydzien}**")
                    for p in posty_t:
                        kolor = "tag-green" if p.get('cel_posta') == 'sprzedaż' else "tag-blue"
                        st.markdown(f'<div class="plan-dzien"><div style="display:flex;justify-content:space-between;"><div class="data">{p.get("data","")} · {p.get("godzina","")}</div><div><span class="tag tag-orange">{p.get("format","")}</span> <span class="tag {kolor}">{p.get("cel_posta","")}</span></div></div><div class="temat">{p.get("temat","")}</div><div class="szczegoly">🎂 {p.get("produkt","")} · 💡 {p.get("wskazowka","")}</div></div>', unsafe_allow_html=True)
                st.download_button("⬇️ Pobierz kalendarz", json.dumps(dane, ensure_ascii=False, indent=2), file_name=f"kalendarz_{miesiac}.json")
            except:
                st.write(odp.choices[0].message.content)

# TAB 4 - TRENDY I VIRAL
with tab4:
    st.markdown('<div class="sekcja"><h3>🔍 Analiza trendów, konkurencji i viralowych postów</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        fraza = st.text_input("Fraza:", placeholder="np. torty weselne, macarons Polska, cukiernia Poznań")
    with col2:
        typ = st.selectbox("Typ analizy:", [
            "Najpopularniejsze posty + dlaczego działają",
            "Trendy branżowe 2025",
            "Analiza konkurencji",
            "Muzyka i styl do Reels",
            "Viral content — co kopiować"
        ])
    if st.button("🔍 Analizuj", use_container_width=True, type="primary", key="btn_trend") and fraza:
        with st.spinner("Szukam viralowych postów i trendów..."):
            wyniki = tavily.search(f"{fraza} Instagram viral popular posts cukiernia 2025", max_results=8)
            kontekst = "\n\n".join([f"Źródło: {r['url']}\n{r['title']}\n{r['content']}" for r in wyniki["results"]])
            odp = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Jesteś analitykiem social media specjalizującym się w branży cukierniczej. Analizujesz viral content dla '{nazwa}'."},
                    {"role": "user", "content": f"""Dane z internetu:
{kontekst}

Wykonaj: {typ} dla tematu: {fraza}

TYLKO JSON:
{{"podsumowanie": "2-3 zdania", "top_posty": [{{"typ_posta": "np. tort weselny minimalistyczny", "dlaczego_viral": "szczegółowe wyjaśnienie dlaczego ten typ postów zbiera dużo wyświetleń i interakcji", "elementy_sukcesu": ["element 1", "element 2", "element 3"], "jak_skopiowac": "konkretny przepis jak to odtworzyć krok po kroku", "szacowane_zasięgi": "np. 10k-50k wyświetleń"}}], "top_trendy": [{{"trend": "nazwa", "opis": "opis", "jak_wykorzystac": "konkretna akcja"}}], "co_kopiowac": ["rzecz 1", "rzecz 2", "rzecz 3"], "muzyka_reels": ["utwór - artysta"], "styl_wizualny": "opis stylu który teraz działa", "unikac": ["czego unikać 1", "czego unikać 2"], "najlepsze_hashtagi": ["hashtag1", "hashtag2", "hashtag3"]}}"""}
                ]
            )
            try:
                tekst = odp.choices[0].message.content
                czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                dane = json.loads(czysty)
                st.markdown(f'<div class="insight tip">📊 {dane.get("podsumowanie","")}</div>', unsafe_allow_html=True)

                # Najpopularniejsze posty
                if dane.get('top_posty'):
                    st.markdown("### 🏆 Najpopularniejsze typy postów i dlaczego działają")
                    for i, p in enumerate(dane.get('top_posty', [])):
                        st.markdown(f"""<div class="post-viral">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                            <div style="font-size:16px;font-weight:600;color:#111827;">#{i+1} {p.get('typ_posta','')}</div>
                            <div class="liczba-viral">{p.get('szacowane_zasięgi','')}</div>
                        </div>
                        <div class="insight success" style="margin-bottom:8px;">
                            <strong>🎯 Dlaczego viral:</strong> {p.get('dlaczego_viral','')}
                        </div>
                        <strong>✅ Elementy sukcesu:</strong>
                        {"".join([f'<div style="color:#374151;font-size:13px;padding:4px 0;">▸ {e}</div>' for e in p.get('elementy_sukcesu',[])])}
                        <div class="insight tip" style="margin-top:8px;">
                            <strong>📋 Jak to odtworzyć:</strong> {p.get('jak_skopiowac','')}
                        </div>
                        </div>""", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if dane.get('top_trendy'):
                        st.markdown("### 🔥 Top trendy")
                        for t in dane.get('top_trendy', []):
                            st.markdown(f'<div class="insight success"><strong>{t.get("trend","")}</strong><br><span style="color:#6b7280;font-size:13px;">{t.get("opis","")}</span><br><span style="color:#065f46;font-size:13px;">→ {t.get("jak_wykorzystac","")}</span></div>', unsafe_allow_html=True)
                    st.markdown("### ✅ Co skopiować")
                    for c in dane.get('co_kopiowac', []):
                        st.markdown(f'<div class="insight tip">✓ {c}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown("### 🎨 Styl wizualny który działa")
                    st.markdown(f'<div class="insight">{dane.get("styl_wizualny","")}</div>', unsafe_allow_html=True)
                    st.markdown("### 🎵 Muzyka do Reels")
                    for m in dane.get('muzyka_reels', []):
                        st.markdown(f"🎵 {m}")
                    st.markdown("### ❌ Czego unikać")
                    for u in dane.get('unikac', []):
                        st.markdown(f'<div class="insight danger">✗ {u}</div>', unsafe_allow_html=True)
                    hashtagi = dane.get('najlepsze_hashtagi', [])
                    if hashtagi:
                        html_tags = " ".join([f'<span class="sticker">#{h.replace("#","")}</span>' for h in hashtagi])
                        st.markdown(f"**#️⃣ Hashtagi:** {html_tags}", unsafe_allow_html=True)
            except:
                st.write(odp.choices[0].message.content)

# TAB 5 - PLAN
with tab5:
    st.markdown('<div class="sekcja"><h3>🎯 Plan działania krok po kroku</h3></div>', unsafe_allow_html=True)
    aktualny_stan = st.text_area("Opisz aktualną sytuację:", placeholder="np. Mam 200 obserwujących, wrzucam posty 2x w tygodniu...", height=100)
    cel_glowny = st.text_input("Główny cel:", placeholder="np. Chcę mieć 1000 obserwujących i więcej zamówień")
    if st.button("🎯 Generuj plan", use_container_width=True, type="primary", key="btn_plan") and aktualny_stan:
        with st.spinner("Przygotowuję plan działania..."):
            odp = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Jesteś konsultantem marketingowym dla '{nazwa}' w {miasto}."},
                    {"role": "user", "content": f"""Stan: {aktualny_stan}, Cel: {cel_glowny}

TYLKO JSON:
{{"diagnoza": "ocena", "dziś": [{{"numer": 1, "akcja": "co", "szczegoly": "jak dokładnie", "czas": "ile minut"}}], "ten_tydzień": [{{"numer": 1, "akcja": "co", "szczegoly": "jak", "efekt": "efekt"}}], "ten_miesiąc": [{{"numer": 1, "akcja": "co", "szczegoly": "jak", "efekt": "efekt"}}], "kluczowe_metryki": ["metryka"], "motywacja": "zdanie"}}"""}
                ]
            )
            try:
                tekst = odp.choices[0].message.content
                czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                dane = json.loads(czysty)
                st.markdown(f'<div class="insight warning">🔍 <strong>Diagnoza:</strong> {dane.get("diagnoza","")}</div>', unsafe_allow_html=True)
                for sekcja, tytul in [("dziś","⚡ Zrób to DZIŚ"), ("ten_tydzień","📅 Ten tydzień"), ("ten_miesiąc","🗓️ Ten miesiąc")]:
                    st.markdown(f"### {tytul}")
                    for k in dane.get(sekcja, []):
                        czas = f"· ⏱ {k.get('czas','')}" if k.get('czas') else f"· 📈 {k.get('efekt','')}"
                        st.markdown(f'<div class="krok"><div class="krok-numer">{k.get("numer","")}</div><div class="krok-tresc"><h4>{k.get("akcja","")}</h4><p>{k.get("szczegoly","")} {czas}</p></div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="insight success">💪 {dane.get("motywacja","")}</div>', unsafe_allow_html=True)
            except:
                st.write(odp.choices[0].message.content)

# TAB 6 - EDYCJA ZDJĘĆ
with tab6:
    st.markdown('<div class="sekcja"><h3>🖼️ Profesjonalna edycja zdjęć</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        zdjecie_edycja = st.file_uploader("📸 Wrzuć zdjęcie tortu:", type=["jpg","jpeg","png"], key="edycja_zdj")
        if zdjecie_edycja:
            img_oryg = Image.open(zdjecie_edycja)
            st.image(img_oryg, caption="Oryginał", use_container_width=True)
            tryb = st.radio("Co chcesz zrobić?", ["Popraw kolory i jasność", "Usuń tło i dodaj nowe", "Oba"])
            if tryb in ["Popraw kolory i jasność", "Oba"]:
                c1, c2 = st.columns(2)
                with c1:
                    jasnosc = st.slider("☀️ Jasność", 0.5, 2.0, 1.2, key="j")
                    kontrast = st.slider("🌗 Kontrast", 0.5, 2.0, 1.1, key="k")
                with c2:
                    nasycenie = st.slider("🎨 Kolory", 0.5, 2.0, 1.3, key="n")
                    ostrosc = st.slider("🔍 Ostrość", 0.5, 2.0, 1.2, key="o")
            if tryb in ["Usuń tło i dodaj nowe", "Oba"]:
                st.markdown("**Wybierz nowe tło:**")
                typ_tla = st.selectbox("Typ tła:", ["Jednolity kolor", "Gradient pastelowy", "Białe studio"])
                if typ_tla == "Jednolity kolor":
                    kolor_tla = st.color_picker("Kolor tła:", "#FFF5F5")
                elif typ_tla == "Gradient pastelowy":
                    kolor_tla = "#FFF0F5"
                else:
                    kolor_tla = "#FFFFFF"

            if st.button("✨ Edytuj zdjęcie", use_container_width=True, type="primary", key="btn_edycja"):
                with st.spinner("AI edytuje zdjęcie..."):
                    img_wynik = img_oryg.copy()
                    if tryb in ["Popraw kolory i jasność", "Oba"]:
                        img_wynik = ImageEnhance.Brightness(img_wynik).enhance(jasnosc)
                        img_wynik = ImageEnhance.Contrast(img_wynik).enhance(kontrast)
                        img_wynik = ImageEnhance.Color(img_wynik).enhance(nasycenie)
                        img_wynik = ImageEnhance.Sharpness(img_wynik).enhance(ostrosc)
                    if tryb in ["Usuń tło i dodaj nowe", "Oba"]:
                        with st.spinner("Usuwam tło AI (może potrwać 1-2 minuty)..."):
                            img_bytes = io.BytesIO()
                            img_wynik.save(img_bytes, format="PNG")
                            wynik_bytes = remove(img_bytes.getvalue())
                            img_bez_tla = Image.open(io.BytesIO(wynik_bytes)).convert("RGBA")
                            r_val = int(kolor_tla[1:3], 16)
                            g_val = int(kolor_tla[3:5], 16)
                            b_val = int(kolor_tla[5:7], 16)
                            tlo = Image.new("RGBA", img_bez_tla.size, (r_val, g_val, b_val, 255))
                            tlo.paste(img_bez_tla, mask=img_bez_tla.split()[3])
                            img_wynik = tlo.convert("RGB")
                    with col2:
                        st.image(img_wynik, caption="Po edycji", use_container_width=True)
                        buf = io.BytesIO()
                        img_wynik.save(buf, format="JPEG", quality=95)
                        st.download_button("⬇️ Pobierz zdjęcie", buf.getvalue(), file_name="edytowane.jpg", mime="image/jpeg")
                        odp_foto = groq.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": "Podaj 3 konkretne wskazówki jak profesjonalnie sfotografować tort/ciasto do Instagrama. Odpowiedz po polsku, krótko i praktycznie."}]
                        )
                        st.markdown("**💡 Wskazówki fotograficzne:**")
                        st.markdown(f'<div class="insight tip">{odp_foto.choices[0].message.content}</div>', unsafe_allow_html=True)

# TAB 7 - GENERATOR OFERT PDF
with tab7:
    st.markdown('<div class="sekcja"><h3>📋 Generator profesjonalnych ofert z PDF</h3></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        okazja_oferty = st.selectbox("Okazja:", ["Święta Bożego Narodzenia 🎄","Wielkanoc 🐣","Walentynki ❤️","Dzień Matki 💐","Komunia Święta ✝️","Wesele 💍","Urodziny 🎂","Nowy Rok 🎆","Dzień Dziecka 🎈","Halloween 🎃","Oferta ogólna"])
        if "produkty" not in st.session_state:
            st.session_state.produkty = [{"nazwa": "", "cena": ""}]
        st.markdown("**Dodaj produkty i ceny:**")
        for i, prod in enumerate(st.session_state.produkty):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.session_state.produkty[i]["nazwa"] = st.text_input(f"Produkt {i+1}:", value=prod["nazwa"], placeholder="np. Tort czekoladowy", key=f"prod_{i}")
            with c2:
                st.session_state.produkty[i]["cena"] = st.text_input("Cena:", value=prod["cena"], placeholder="150 zł", key=f"cena_{i}")
            with c3:
                if i > 0 and st.button("❌", key=f"del_{i}"):
                    st.session_state.produkty.pop(i)
                    st.rerun()
        if st.button("➕ Dodaj produkt", use_container_width=True):
            st.session_state.produkty.append({"nazwa": "", "cena": ""})
            st.rerun()
        dodatkowe_info = st.text_area("Dodatkowe informacje:", placeholder="np. dostawa gratis, zamówienia min. 3 dni wcześniej, tel. 123-456-789")
        logo = st.file_uploader("📸 Logo cukierni (opcjonalnie):", type=["jpg","jpeg","png"], key="logo_oferta")

        if st.button("✨ Generuj ofertę + PDF", use_container_width=True, type="primary", key="btn_oferta"):
            produkty_lista = "\n".join([f"- {p['nazwa']}: {p['cena']}" for p in st.session_state.produkty if p['nazwa']])
            with st.spinner("Tworzę profesjonalną ofertę..."):
                odp = groq.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Jesteś ekspertem marketingu dla cukierni '{nazwa}' w {miasto}. Styl: {styl_profilu}."},
                        {"role": "user", "content": f"""Stwórz profesjonalną ofertę na: {okazja_oferty}
Cukiernia: {nazwa}, {miasto}
Produkty:
{produkty_lista}
Dodatkowe info: {dodatkowe_info}

TYLKO JSON:
{{"tytul_oferty": "chwytliwy tytuł", "podtytul": "podtytuł", "wstep": "ciepłe wprowadzenie 2 zdania", "produkty_opisane": [{{"nazwa": "nazwa", "cena": "cena", "opis": "krótki opis 1 zdanie", "emoji": "emoji"}}], "bonus": "dodatkowa oferta/gratis", "cta": "wezwanie do działania", "hashtagi": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"], "wersja_stories": "krótka wersja na Stories max 3 zdania", "wersja_sms": "wersja SMS dla klientów"}}"""}
                    ]
                )
                try:
                    tekst = odp.choices[0].message.content
                    czysty = tekst[tekst.find('{'):tekst.rfind('}')+1]
                    dane = json.loads(czysty)
                    with col2:
                        st.markdown(f"### {dane.get('tytul_oferty','')}")
                        st.markdown(f"*{dane.get('podtytul','')}*")
                        st.markdown(dane.get('wstep',''))
                        st.markdown("**Produkty:**")
                        for p in dane.get('produkty_opisane', []):
                            st.markdown(f"**{p.get('emoji','')} {p.get('nazwa','')}** — {p.get('cena','')}")
                            st.caption(p.get('opis',''))
                        if dane.get('bonus'):
                            st.markdown(f'<div class="insight success">🎁 {dane.get("bonus","")}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="insight tip">📲 {dane.get("cta","")}</div>', unsafe_allow_html=True)
                        st.markdown("**Stories:**")
                        st.text_area("", dane.get('wersja_stories',''), height=80, key="stories_v")
                        st.markdown("**SMS:**")
                        st.text_area("", dane.get('wersja_sms',''), height=80, key="sms_v")

                    # Generuj PDF
                    buf_pdf = io.BytesIO()
                    doc = SimpleDocTemplate(buf_pdf, pagesize=A4,
                        rightMargin=2*cm, leftMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm)
                    styles = getSampleStyleSheet()
                    story = []

                    # Styl tytułu
                    styl_tytul = ParagraphStyle('tytul', parent=styles['Title'],
                        fontSize=28, textColor=colors.HexColor('#111827'),
                        spaceAfter=8, fontName='Helvetica-Bold', alignment=1)
                    styl_podtytul = ParagraphStyle('podtytul', parent=styles['Normal'],
                        fontSize=14, textColor=colors.HexColor('#6b7280'),
                        spaceAfter=20, alignment=1)
                    styl_wstep = ParagraphStyle('wstep', parent=styles['Normal'],
                        fontSize=12, textColor=colors.HexColor('#374151'),
                        spaceAfter=20, leading=18, alignment=1)
                    styl_produkt_nazwa = ParagraphStyle('prod_nazwa', parent=styles['Normal'],
                        fontSize=13, textColor=colors.HexColor('#111827'),
                        fontName='Helvetica-Bold')
                    styl_produkt_opis = ParagraphStyle('prod_opis', parent=styles['Normal'],
                        fontSize=11, textColor=colors.HexColor('#6b7280'), leading=15)
                    styl_cena = ParagraphStyle('cena', parent=styles['Normal'],
                        fontSize=14, textColor=colors.HexColor('#6366f1'),
                        fontName='Helvetica-Bold', alignment=2)
                    styl_cta = ParagraphStyle('cta', parent=styles['Normal'],
                        fontSize=13, textColor=colors.HexColor('#ffffff'),
                        alignment=1, fontName='Helvetica-Bold')
                    styl_footer = ParagraphStyle('footer', parent=styles['Normal'],
                        fontSize=10, textColor=colors.HexColor('#9ca3af'), alignment=1)

                    # Logo jeśli jest
                    if logo:
                        from reportlab.platypus import Image as RLImage
                        logo_img = Image.open(logo)
                        logo_buf = io.BytesIO()
                        logo_img.save(logo_buf, format="PNG")
                        logo_buf.seek(0)
                        rl_img = RLImage(logo_buf, width=4*cm, height=4*cm)
                        rl_img.hAlign = 'CENTER'
                        story.append(rl_img)
                        story.append(Spacer(1, 0.5*cm))

                    # Tytuł
                    story.append(Paragraph(dane.get('tytul_oferty',''), styl_tytul))
                    story.append(Paragraph(dane.get('podtytul',''), styl_podtytul))
                    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
                    story.append(Spacer(1, 0.5*cm))
                    story.append(Paragraph(dane.get('wstep',''), styl_wstep))
                    story.append(Spacer(1, 0.3*cm))

                    # Produkty
                    story.append(Paragraph("🎂 Nasza oferta:", ParagraphStyle('h2', parent=styles['Normal'],
                        fontSize=16, fontName='Helvetica-Bold', textColor=colors.HexColor('#111827'), spaceAfter=12)))

                    for p in dane.get('produkty_opisane', []):
                        dane_tabeli = [[
                            Paragraph(f"{p.get('emoji','')} {p.get('nazwa','')}", styl_produkt_nazwa),
                            Paragraph(p.get('opis',''), styl_produkt_opis),
                            Paragraph(p.get('cena',''), styl_cena)
                        ]]
                        tabela = Table(dane_tabeli, colWidths=[5*cm, 8*cm, 3*cm])
                        tabela.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
                            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f9fafb')]),
                            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
                            ('LEFTPADDING', (0,0), (-1,-1), 12),
                            ('RIGHTPADDING', (0,0), (-1,-1), 12),
                            ('TOPPADDING', (0,0), (-1,-1), 10),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                            ('ROUNDEDCORNERS', [4]),
                        ]))
                        story.append(tabela)
                        story.append(Spacer(1, 0.2*cm))

                    story.append(Spacer(1, 0.5*cm))

                    # Bonus
                    if dane.get('bonus'):
                        bonus_tabela = Table([[Paragraph(f"🎁 {dane.get('bonus','')}", ParagraphStyle('bonus',
                            parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#065f46'),
                            fontName='Helvetica-Bold'))]],
                            colWidths=[16*cm])
                        bonus_tabela.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#d1fae5')),
                            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#10b981')),
                            ('LEFTPADDING', (0,0), (-1,-1), 15),
                            ('TOPPADDING', (0,0), (-1,-1), 12),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                        ]))
                        story.append(bonus_tabela)
                        story.append(Spacer(1, 0.5*cm))

                    # CTA
                    cta_tabela = Table([[Paragraph(dane.get('cta',''), styl_cta)]], colWidths=[16*cm])
                    cta_tabela.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#6366f1')),
                        ('LEFTPADDING', (0,0), (-1,-1), 15),
                        ('TOPPADDING', (0,0), (-1,-1), 15),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                        ('ROUNDEDCORNERS', [8]),
                    ]))
                    story.append(cta_tabela)
                    story.append(Spacer(1, 0.5*cm))

                    # Dodatkowe info
                    if dodatkowe_info:
                        story.append(Paragraph(dodatkowe_info, ParagraphStyle('info', parent=styles['Normal'],
                            fontSize=10, textColor=colors.HexColor('#6b7280'), alignment=1)))

                    story.append(Spacer(1, 0.5*cm))
                    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e5e7eb')))
                    story.append(Spacer(1, 0.3*cm))
                    hashtagi_tekst = " ".join([f"#{h.replace('#','')}" for h in dane.get('hashtagi',[])])
                    story.append(Paragraph(hashtagi_tekst, styl_footer))
                    story.append(Paragraph(f"{nazwa} · {miasto}", styl_footer))

                    doc.build(story)
                    buf_pdf.seek(0)
                    st.download_button("⬇️ Pobierz ofertę PDF", buf_pdf.getvalue(),
                        file_name=f"oferta_{okazja_oferty[:10]}.pdf", mime="application/pdf",
                        use_container_width=True)
                    st.success("✅ PDF gotowy do pobrania!")

                except Exception as e:
                    st.error(f"Błąd: {e}")
                    with col2:
                        st.write(odp.choices[0].message.content)