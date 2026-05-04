import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageFilter
import io

st.set_page_config(page_title="🎨 AI Tło Cukiernicze", page_icon="🎨", layout="wide")

st.markdown("""
<style>
.hero { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #e5e7eb; }
.info { background: #dbeafe; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 3px solid #3b82f6; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
<h1>🎨 AI Generator Tła Cukierniczego</h1>
<p>Profesjonalne zdjęcia tortów gotowe na Instagram — precyzyjne wycinanie + realistyczne tło</p>
</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Klucze API")
    pexels_key = st.text_input("Klucz Pexels:", type="password")
    removebg_key = st.text_input("Klucz Remove.bg:", type="password")
    st.markdown("---")
    st.markdown("### 📐 Format Instagram")
    st.markdown("Zdjęcia 1080x1080px gotowe do publikacji")

if not pexels_key or not removebg_key:
    st.info("👈 Wpisz oba klucze API w panelu po lewej")
    st.stop()

def usun_tlo_removebg(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    resp = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": buf.getvalue()},
        data={"size": "auto"},
        headers={"X-Api-Key": removebg_key}
    )
    if resp.status_code == 200:
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    else:
        st.error(f"Błąd Remove.bg: {resp.status_code}")
        return None

def pobierz_tla_z_pexels(query, ile=9):
    headers = {"Authorization": pexels_key}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={ile}&orientation=square"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("photos", [])
    return []

def pobierz_zdjecie(url):
    resp = requests.get(url)
    return Image.open(io.BytesIO(resp.content)).convert("RGB")

def przytnij_do_kwadratu(img, rozmiar=1080):
    w, h = img.size
    min_wym = min(w, h)
    lewo = (w - min_wym) // 2
    gora = (h - min_wym) // 2
    return img.crop((lewo, gora, lewo + min_wym, gora + min_wym)).resize((rozmiar, rozmiar), Image.LANCZOS)

def dodaj_cien(tort_rgba, intensywnosc=0.35, rozmycie=25):
    w, h = tort_rgba.size
    maska = tort_rgba.split()[3]
    cien_maska = maska.point(lambda x: int(x * intensywnosc))
    cien_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cien_layer.putalpha(cien_maska)
    cien_layer = cien_layer.filter(ImageFilter.GaussianBlur(rozmycie))
    wynik = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wynik.paste(cien_layer, (0, int(h * 0.03)))
    wynik.paste(tort_rgba, (0, 0), mask=tort_rgba.split()[3])
    return wynik

def polacz_z_tlem(tort_rgba, tlo_img, skala=0.8):
    rozmiar = 1080
    tlo_kwadrat = przytnij_do_kwadratu(tlo_img, rozmiar).convert("RGBA")
    wynik = Image.new("RGBA", (rozmiar, rozmiar))
    wynik.paste(tlo_kwadrat, (0, 0))
    tort_w, tort_h = tort_rgba.size
    nowy_w = int(rozmiar * skala)
    nowy_h = int(tort_h * (nowy_w / tort_w))
    tort_skalowany = tort_rgba.resize((nowy_w, nowy_h), Image.LANCZOS)
    x = (rozmiar - nowy_w) // 2
    y = rozmiar - nowy_h - int(rozmiar * 0.05)
    wynik.paste(tort_skalowany, (x, y), mask=tort_skalowany.split()[3])
    return wynik.convert("RGB")

tab1, tab2 = st.tabs(["🖼️ Edytuj zdjęcie", "📚 Biblioteka teł"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📸 Twoje zdjęcie")
        zdjecie = st.file_uploader("Wrzuć zdjęcie tortu:", type=["jpg","jpeg","png"])

        if zdjecie:
            img = Image.open(zdjecie)
            st.image(img, caption="Oryginał", use_container_width=True)

            st.markdown("### 🎨 Popraw kolory")
            c1, c2 = st.columns(2)
            with c1:
                jasnosc = st.slider("☀️ Jasność", 0.5, 2.0, 1.1)
                kontrast = st.slider("🌗 Kontrast", 0.5, 2.0, 1.1)
            with c2:
                nasycenie = st.slider("🎨 Kolory", 0.5, 2.0, 1.2)
                ostrosc = st.slider("🔍 Ostrość", 0.5, 2.0, 1.2)

            st.markdown("### 🌑 Cień")
            c1, c2 = st.columns(2)
            with c1:
                cien_int = st.slider("Intensywność", 0.0, 0.8, 0.3)
            with c2:
                cien_roz = st.slider("Rozmycie", 5, 50, 20)

            st.markdown("### 📐 Rozmiar tortu")
            skala = st.slider("Skala tortu na zdjęciu", 0.4, 1.0, 0.75)

            st.markdown("### 🖼️ Wybierz tło")
            styl_tla = st.selectbox("Kategoria:", [
                "empty wooden table white wall",
                "empty marble table clean background",
                "empty pastel pink wall clean",
                "clean white studio background empty",
                "empty rustic wood wall background",
                "empty dark elegant background",
                "empty beige wall table clean",
                "empty light background minimal"
            ])

            if st.button("🔍 Pokaż opcje tła", use_container_width=True):
                with st.spinner("Pobieram tła..."):
                    st.session_state.tla = pobierz_tla_z_pexels(styl_tla, 9)
                    st.session_state.wybrany_index = None

            if "tla" in st.session_state and st.session_state.tla:
                st.markdown("**Wybierz tło (tylko puste!):**")
                cols = st.columns(3)
                for i, foto in enumerate(st.session_state.tla):
                    with cols[i % 3]:
                        st.image(foto["src"]["medium"], use_container_width=True)
                        if st.button(f"#{i+1}", key=f"wybierz_{i}", use_container_width=True):
                            st.session_state.wybrany_index = i
                            st.session_state.wybrany_url = foto["src"]["large2x"]

            if "wybrany_index" in st.session_state and st.session_state.wybrany_index is not None:
                st.markdown(f'<div class="info">✅ Wybrano tło #{st.session_state.wybrany_index + 1}</div>', unsafe_allow_html=True)

                if st.button("✨ Generuj profesjonalne zdjęcie!", use_container_width=True, type="primary"):
                    with st.spinner("Poprawiam kolory..."):
                        img_pop = ImageEnhance.Brightness(img).enhance(jasnosc)
                        img_pop = ImageEnhance.Contrast(img_pop).enhance(kontrast)
                        img_pop = ImageEnhance.Color(img_pop).enhance(nasycenie)
                        img_pop = ImageEnhance.Sharpness(img_pop).enhance(ostrosc)

                    with st.spinner("Remove.bg usuwa tło precyzyjnie..."):
                        tort_bez_tla = usun_tlo_removebg(img_pop)

                    if tort_bez_tla:
                        with st.spinner("Dodaję cień..."):
                            tort_z_cieniem = dodaj_cien(tort_bez_tla, cien_int, cien_roz)

                        with st.spinner("Pobieram tło..."):
                            tlo_img = pobierz_zdjecie(st.session_state.wybrany_url)

                        with st.spinner("Składam finalne zdjęcie 1080x1080px..."):
                            wynik = polacz_z_tlem(tort_z_cieniem, tlo_img, skala)

                        with col2:
                            st.markdown("### ✨ Gotowe! Instagram 1080x1080")
                            st.image(wynik, caption="Profesjonalne zdjęcie", use_container_width=True)
                            buf = io.BytesIO()
                            wynik.save(buf, format="JPEG", quality=95)
                            st.download_button("⬇️ Pobierz (1080x1080px)", buf.getvalue(),
                                file_name="tort_instagram.jpg", mime="image/jpeg", use_container_width=True)
                            st.success("🎉 Gotowe na Instagram!")

with tab2:
    st.markdown("### 📚 Przeglądaj bibliotekę teł")
    kategoria = st.selectbox("Kategoria:", [
        "empty wooden table background",
        "empty marble surface clean",
        "empty pastel background minimal",
        "empty white studio background",
        "empty elegant dark background"
    ], key="kat_biblioteka")
    if st.button("🔍 Pokaż", use_container_width=True):
        with st.spinner("Pobieram..."):
            zdjecia = pobierz_tla_z_pexels(kategoria, 12)
            cols = st.columns(4)
            for i, foto in enumerate(zdjecia):
                with cols[i % 4]:
                    st.image(foto["src"]["medium"], use_container_width=True)
                    st.caption(f"📸 {foto.get('photographer','')}")