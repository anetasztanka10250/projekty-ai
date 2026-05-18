import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageFilter
import io
import cv2
import numpy as np
import os
import base64
import re

def _wczytaj_token_hf():
    try:
        tekst = open("klucz.txt", encoding="utf-8").read()
        m = re.search(r'(hf_\S+)', tekst)
        return m.group(1) if m else None
    except FileNotFoundError:
        return None

HF_TOKEN = _wczytaj_token_hf()
HF_INPAINT_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting"

st.set_page_config(page_title="🎨 AI Kompozycja Tortów", page_icon="🎨", layout="wide")

st.markdown("""
<style>
.hero { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #e5e7eb; }
.info { background: #dbeafe; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 3px solid #3b82f6; font-size: 13px; }
.tlo-selected { border: 3px solid #6366f1 !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
<h1>🎨 AI Kompozycja — Tort na Profesjonalnym Tle</h1>
<p>Wybierz gotowe tło → wrzuć tort mamy → pobierz gotowe zdjęcie Instagram 1080x1080px</p>
</div>""", unsafe_allow_html=True)

# Sprawdzone tła — bezpośrednie linki do zdjęć
TLLA = {
    "🪵 Jasne drewno": [
        {"url": "https://images.pexels.com/photos/1148399/pexels-photo-1148399.jpeg", "opis": "Jasny drewniany stół"},
        {"url": "https://images.pexels.com/photos/1571458/pexels-photo-1571458.jpeg", "opis": "Drewniana deska kuchenna"},
        {"url": "https://images.pexels.com/photos/3992656/pexels-photo-3992656.jpeg", "opis": "Ciepłe drewno z białą ścianą"},
        {"url": "https://images.pexels.com/photos/6207364/pexels-photo-6207364.jpeg", "opis": "Elegancki drewniany blat"},
    ],
    "🤍 Białe i beżowe": [
        {"url": "https://images.pexels.com/photos/1939485/pexels-photo-1939485.jpeg", "opis": "Białe minimalistyczne tło"},
        {"url": "https://images.pexels.com/photos/3764013/pexels-photo-3764013.jpeg", "opis": "Beżowe eleganckie tło"},
        {"url": "https://images.pexels.com/photos/5824901/pexels-photo-5824901.jpeg", "opis": "Jasne studio fotograficzne"},
        {"url": "https://images.pexels.com/photos/4992816/pexels-photo-4992816.jpeg", "opis": "Białe tło cukiernicze"},
    ],
    "🌸 Pastelowe": [
        {"url": "https://images.pexels.com/photos/931177/pexels-photo-931177.jpeg", "opis": "Pastelowe różowe tło"},
        {"url": "https://images.pexels.com/photos/1279813/pexels-photo-1279813.jpeg", "opis": "Kwiaty na jasnym tle"},
        {"url": "https://images.pexels.com/photos/3819983/pexels-photo-3819983.jpeg", "opis": "Delikatne pastelowe tło"},
        {"url": "https://images.pexels.com/photos/4099232/pexels-photo-4099232.jpeg", "opis": "Różowe eleganckie tło"},
    ],
    "🍰 Cukiernicze": [
        {"url": "https://images.pexels.com/photos/4553118/pexels-photo-4553118.jpeg", "opis": "Drewniany stół cukierniczy"},
        {"url": "https://images.pexels.com/photos/6133325/pexels-photo-6133325.jpeg", "opis": "Profesjonalne tło deserowe"},
        {"url": "https://images.pexels.com/photos/2144200/pexels-photo-2144200.jpeg", "opis": "Eleganckie tło z deserem"},
        {"url": "https://images.pexels.com/photos/5765/food-sweet-flowers-candy.jpg", "opis": "Kwiatowe tło cukiernicze"},
    ]
}

with st.sidebar:
    st.markdown("### ⚙️ Klucz API")
    removebg_key = st.text_input("Klucz Remove.bg:", type="password")
    st.markdown("---")
    st.markdown("### 📋 Jak używać:")
    st.markdown("""
    1. Wybierz tło z galerii
    2. Wrzuć zdjęcie tortu
    3. Ustaw rozmiar i pozycję
    4. Pobierz gotowe 1080x1080px
    """)

if not removebg_key:
    st.info("👈 Wpisz klucz Remove.bg w panelu po lewej")
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

def pobierz_zdjecie_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url + "?auto=compress&cs=tinysrgb&w=1080", headers=headers)
    return Image.open(io.BytesIO(resp.content)).convert("RGB")

def przytnij_do_kwadratu(img, rozmiar=1080):
    w, h = img.size
    min_wym = min(w, h)
    lewo = (w - min_wym) // 2
    gora = (h - min_wym) // 2
    return img.crop((lewo, gora, lewo + min_wym, gora + min_wym)).resize((rozmiar, rozmiar), Image.LANCZOS)

def dodaj_cien(tort_rgba, intensywnosc=0.4, rozmycie=20, offset=15):
    w, h = tort_rgba.size
    maska = tort_rgba.split()[3]
    cien_maska = maska.point(lambda x: int(x * intensywnosc))
    cien_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cien_layer.putalpha(cien_maska)
    cien_layer = cien_layer.filter(ImageFilter.GaussianBlur(rozmycie))
    wynik = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wynik.paste(cien_layer, (offset, offset))
    wynik.paste(tort_rgba, (0, 0), mask=tort_rgba.split()[3])
    return wynik

def inpaint_hf(obraz_pil, maska_np):
    w_orig, h_orig = obraz_pil.size
    skala = min(512 / w_orig, 512 / h_orig, 1.0)
    nowy_w = max(8, (round(w_orig * skala) // 8) * 8)
    nowy_h = max(8, (round(h_orig * skala) // 8) * 8)
    img_512 = obraz_pil.resize((nowy_w, nowy_h), Image.LANCZOS)
    maska_512 = Image.fromarray(maska_np).resize((nowy_w, nowy_h), Image.NEAREST)

    def pil_b64(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    resp = requests.post(
        HF_INPAINT_URL,
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json={
            "inputs": "background, seamless texture, clean surface, no objects",
            "parameters": {
                "image": pil_b64(img_512),
                "mask_image": pil_b64(maska_512),
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
            }
        },
        timeout=120
    )
    if resp.status_code != 200:
        raise RuntimeError(f"HF API {resp.status_code}: {resp.text[:300]}")
    wynik = Image.open(io.BytesIO(resp.content)).convert("RGB")
    return np.array(wynik.resize((w_orig, h_orig), Image.LANCZOS))

def sklej_kompozycje(tlo_img, tort_rgba, skala, pozycja_x, pozycja_y, cien_int, cien_roz):
    rozmiar = 1080
    tlo_kwadrat = przytnij_do_kwadratu(tlo_img, rozmiar).convert("RGBA")
    wynik = tlo_kwadrat.copy()
    tort_w, tort_h = tort_rgba.size
    nowy_w = int(rozmiar * skala)
    nowy_h = int(tort_h * (nowy_w / tort_w))
    tort_skalowany = tort_rgba.resize((nowy_w, nowy_h), Image.LANCZOS)
    if cien_int > 0:
        tort_skalowany = dodaj_cien(tort_skalowany, cien_int, cien_roz)
    x = int((rozmiar - nowy_w) * pozycja_x)
    y = int((rozmiar - nowy_h) * pozycja_y)
    wynik.paste(tort_skalowany, (x, y), mask=tort_skalowany.split()[3])
    return wynik.convert("RGB")

# KROK 0 — OCZYSZCZANIE WŁASNEGO TŁA
st.markdown("## 🧹 Krok 0 — Oczyść własne tło *(opcjonalne)*")
st.markdown('<div class="info">📷 Masz zdjęcie tła z niechcianym obiektem? Zaznacz go suwakami i usuń przez <strong>Stable Diffusion Inpainting</strong> (HuggingFace) — czyste tło zapisze się jako <strong>tla/wlasne.jpg</strong>.</div>', unsafe_allow_html=True)

if "tlo_wyczyszczone" not in st.session_state:
    st.session_state.tlo_wyczyszczone = None

tlo_do_czyszczenia = st.file_uploader(
    "Wrzuć zdjęcie tła do oczyszczenia:",
    type=["jpg", "jpeg", "png"],
    key="tlo_czyszczenie"
)

if tlo_do_czyszczenia:
    tlo_obraz = Image.open(tlo_do_czyszczenia).convert("RGB")
    tlo_np = np.array(tlo_obraz)
    h_img, w_img = tlo_np.shape[:2]

    st.markdown("**Zaznacz obszar do usunięcia:**")
    col_suw1, col_suw2 = st.columns(2)
    with col_suw1:
        x_inp = st.slider("↔️ Pozycja X (px)", 0, w_img - 1, w_img // 4, key="inp_x")
        szer_max = max(1, w_img - x_inp)
        szer_inp = st.slider("📏 Szerokość (px)", 1, szer_max, min(max(1, w_img // 4), szer_max), key="inp_w")
    with col_suw2:
        y_inp = st.slider("↕️ Pozycja Y (px)", 0, h_img - 1, h_img // 4, key="inp_y")
        wys_max = max(1, h_img - y_inp)
        wys_inp = st.slider("📐 Wysokość (px)", 1, wys_max, min(max(1, h_img // 4), wys_max), key="inp_h")

    podglad_np = tlo_np.copy()
    cv2.rectangle(
        podglad_np,
        (x_inp, y_inp),
        (min(x_inp + szer_inp, w_img - 1), min(y_inp + wys_inp, h_img - 1)),
        (255, 0, 0), 3
    )
    st.image(podglad_np, caption="Podgląd — czerwona ramka = obszar do usunięcia", use_container_width=True)

    if st.button("🤖 Usuń obiekt przez SD Inpainting i zapisz czyste tło", use_container_width=True, type="primary", key="btn_inpaint"):
        if not HF_TOKEN:
            st.error("Nie znaleziono tokenu HuggingFace w klucz.txt!")
        else:
            with st.spinner("Wysyłam do Stable Diffusion Inpainting (HuggingFace)... może potrwać ~30 s"):
                try:
                    maska = np.zeros((h_img, w_img), dtype=np.uint8)
                    maska[y_inp:min(y_inp + wys_inp, h_img), x_inp:min(x_inp + szer_inp, w_img)] = 255
                    wynik_rgb = inpaint_hf(tlo_obraz, maska)
                    os.makedirs("tla", exist_ok=True)
                    Image.fromarray(wynik_rgb).save("tla/wlasne.jpg", quality=95)
                    st.session_state.tlo_wyczyszczone = wynik_rgb
                except RuntimeError as e:
                    st.error(str(e))

    if st.session_state.tlo_wyczyszczone is not None:
        col_przed, col_po = st.columns(2)
        with col_przed:
            st.image(tlo_obraz, caption="Oryginał", use_container_width=True)
        with col_po:
            st.image(st.session_state.tlo_wyczyszczone, caption="✅ Po usunięciu obiektu", use_container_width=True)
        st.success("✅ Czyste tło zapisane jako tla/wlasne.jpg")

st.markdown("---")

# KROK 1 — WYBÓR TŁA
st.markdown("## 🖼️ Krok 1 — Wybierz tło")

if "wybrany_url_tla" not in st.session_state:
    st.session_state.wybrany_url_tla = None
if "wybrany_opis_tla" not in st.session_state:
    st.session_state.wybrany_opis_tla = None

kategoria = st.selectbox("Kategoria teł:", list(TLLA.keys()))

st.markdown("**Kliknij żeby wybrać tło:**")
cols = st.columns(4)
for i, tlo in enumerate(TLLA[kategoria]):
    with cols[i % 4]:
        st.image(tlo["url"] + "?auto=compress&cs=tinysrgb&w=400", use_container_width=True)
        st.caption(tlo["opis"])
        if st.button(f"Wybierz", key=f"tlo_{i}", use_container_width=True):
            st.session_state.wybrany_url_tla = tlo["url"]
            st.session_state.wybrany_opis_tla = tlo["opis"]

if st.session_state.wybrany_url_tla:
    st.markdown(f'<div class="info">✅ Wybrano tło: <strong>{st.session_state.wybrany_opis_tla}</strong></div>', unsafe_allow_html=True)

st.markdown("---")

# KROK 2 — TORT
st.markdown("## 🎂 Krok 2 — Wrzuć zdjęcie tortu mamy")
tort_file = st.file_uploader("Wrzuć zdjęcie tortu:", type=["jpg","jpeg","png"])

if tort_file and st.session_state.wybrany_url_tla:
    tort_img = Image.open(tort_file).convert("RGB")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(st.session_state.wybrany_url_tla + "?auto=compress&cs=tinysrgb&w=400", caption="Wybrane tło", use_container_width=True)
    with col2:
        st.image(tort_img, caption="Tort mamy", use_container_width=True)
    
    st.markdown("## ⚙️ Krok 3 — Ustawienia")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**🎨 Kolory tortu:**")
        jasnosc = st.slider("☀️ Jasność", 0.5, 2.0, 1.1)
        kontrast = st.slider("🌗 Kontrast", 0.5, 2.0, 1.1)
        nasycenie = st.slider("🎨 Kolory", 0.5, 2.0, 1.2)
        ostrosc = st.slider("🔍 Ostrość", 0.5, 2.0, 1.2)
    with col_b:
        st.markdown("**📐 Kompozycja:**")
        skala = st.slider("📏 Rozmiar tortu", 0.3, 1.0, 0.65)
        pozycja_x = st.slider("↔️ Pozycja pozioma", 0.0, 1.0, 0.5)
        pozycja_y = st.slider("↕️ Pozycja pionowa", 0.0, 1.0, 0.8)
        cien_int = st.slider("🌑 Intensywność cienia", 0.0, 0.8, 0.35)
        cien_roz = st.slider("💨 Rozmycie cienia", 5, 50, 20)

    if st.button("✨ Generuj profesjonalne zdjęcie!", use_container_width=True, type="primary"):
        with st.spinner("Poprawiam kolory tortu..."):
            tort_pop = ImageEnhance.Brightness(tort_img).enhance(jasnosc)
            tort_pop = ImageEnhance.Contrast(tort_pop).enhance(kontrast)
            tort_pop = ImageEnhance.Color(tort_pop).enhance(nasycenie)
            tort_pop = ImageEnhance.Sharpness(tort_pop).enhance(ostrosc)

        with st.spinner("Remove.bg precyzyjnie wycina tort..."):
            tort_bez_tla = usun_tlo_removebg(tort_pop)

        if tort_bez_tla:
            with st.spinner("Pobieram wybrane tło..."):
                tlo_img = pobierz_zdjecie_url(st.session_state.wybrany_url_tla)

            with st.spinner("Składam kompozycję 1080x1080px..."):
                wynik = sklej_kompozycje(tlo_img, tort_bez_tla, skala, pozycja_x, pozycja_y, cien_int, cien_roz)

            with col3:
                st.image(wynik, caption="✨ Gotowe Instagram!", use_container_width=True)
                buf = io.BytesIO()
                wynik.save(buf, format="JPEG", quality=95)
                st.download_button(
                    "⬇️ Pobierz (1080x1080px)",
                    buf.getvalue(),
                    file_name="tort_instagram.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
                st.success("🎉 Gotowe na Instagram!")
                st.markdown('<div class="info">💡 Zmień suwaki i wygeneruj ponownie żeby poprawić kompozycję!</div>', unsafe_allow_html=True)

elif tort_file and not st.session_state.wybrany_url_tla:
    st.warning("⬆️ Najpierw wybierz tło w Kroku 1!")
  