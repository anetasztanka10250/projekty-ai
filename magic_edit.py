import streamlit as st
import requests
from PIL import Image, ImageDraw
import io
import numpy as np

st.set_page_config(page_title="🎨 Magic Edit", page_icon="🎨", layout="wide")

st.markdown("""
<style>
.hero { background: white; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #e5e7eb; }
.info { background: #dbeafe; border-radius: 8px; padding: 12px; margin: 8px 0; border-left: 3px solid #3b82f6; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
<h1>🎨 Magic Edit — Usuń obiekt ze zdjęcia</h1>
<p>Opisz co usunąć → AI usuwa i wypełnia naturalnym tłem → wstaw tort mamy</p>
</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Klucze API")
    hf_token = st.text_input("Token Hugging Face:", type="password")
    removebg_key = st.text_input("Klucz Remove.bg:", type="password")
    st.markdown("---")
    st.markdown("""### 📋 Jak używać:
1. Wrzuć zdjęcie tła (np. z Pexels)
2. Zaznacz obszar do usunięcia suwakami
3. AI usuwa obiekt i wypełnia tłem
4. Wrzuć tort mamy
5. Pobierz gotowe zdjęcie
    """)

if not hf_token or not removebg_key:
    st.info("👈 Wpisz klucze API w panelu po lewej")
    st.stop()

def usun_obiekt_inpainting(img, maska, opis_co_usunac):
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-inpainting"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    img_resized = img.resize((512, 512))
    maska_resized = maska.resize((512, 512))
    
    buf_img = io.BytesIO()
    img_resized.save(buf_img, format="PNG")
    
    buf_maska = io.BytesIO()
    maska_resized.save(buf_maska, format="PNG")
    
    prompt = f"empty wooden table, natural light, no objects, clean background, professional food photography"
    negative = f"{opis_co_usunac}, cake, plate, book, people, food"
    
    resp = requests.post(API_URL, headers=headers, json={
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative,
            "num_inference_steps": 30,
        }
    })
    
    if resp.status_code == 200:
        return Image.open(io.BytesIO(resp.content))
    elif resp.status_code == 503:
        st.warning("Model się ładuje — poczekaj 30 sekund i spróbuj ponownie")
        return None
    else:
        st.error(f"Błąd: {resp.status_code} — {resp.text[:200]}")
        return None

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

def przytnij_do_kwadratu(img, rozmiar=1080):
    w, h = img.size
    min_wym = min(w, h)
    lewo = (w - min_wym) // 2
    gora = (h - min_wym) // 2
    return img.crop((lewo, gora, lewo + min_wym, gora + min_wym)).resize((rozmiar, rozmiar), Image.LANCZOS)

def dodaj_cien(tort_rgba, intensywnosc=0.4, rozmycie=20):
    from PIL import ImageFilter
    w, h = tort_rgba.size
    maska = tort_rgba.split()[3]
    cien_maska = maska.point(lambda x: int(x * intensywnosc))
    cien_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cien_layer.putalpha(cien_maska)
    cien_layer = cien_layer.filter(ImageFilter.GaussianBlur(rozmycie))
    wynik = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wynik.paste(cien_layer, (15, 15))
    wynik.paste(tort_rgba, (0, 0), mask=tort_rgba.split()[3])
    return wynik

tab1, tab2 = st.tabs(["✂️ Usuń obiekt z tła", "🎂 Złóż kompozycję"])

with tab1:
    st.markdown("### Krok 1 — Wrzuć zdjęcie tła")
    tlo_file = st.file_uploader("Wrzuć zdjęcie:", type=["jpg","jpeg","png"], key="tlo_magic")
    
    if tlo_file:
        tlo_img = Image.open(tlo_file).convert("RGB")
        w, h = tlo_img.size
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(tlo_img, caption="Oryginał", use_container_width=True)
        
        st.markdown("### Krok 2 — Zaznacz co usunąć")
        st.markdown('<div class="info">💡 Ustaw suwaki żeby zaznaczyć obszar który chcesz usunąć (talerz, ciasto, książka itp.)</div>', unsafe_allow_html=True)
        
        co_usunac = st.text_input("Co chcesz usunąć?", placeholder="np. talerz z ciastem i książka")
        
        c1, c2 = st.columns(2)
        with c1:
            x1_proc = st.slider("📍 Lewy brzeg (%)", 0, 100, 20)
            y1_proc = st.slider("📍 Górny brzeg (%)", 0, 100, 30)
        with c2:
            x2_proc = st.slider("📍 Prawy brzeg (%)", 0, 100, 80)
            y2_proc = st.slider("📍 Dolny brzeg (%)", 0, 100, 90)
        
        x1 = int(w * x1_proc / 100)
        y1 = int(h * y1_proc / 100)
        x2 = int(w * x2_proc / 100)
        y2 = int(h * y2_proc / 100)
        
        podglad = tlo_img.copy()
        draw = ImageDraw.Draw(podglad)
        draw.rectangle([x1, y1, x2, y2], outline="red", width=5)
        
        with col1:
            st.image(podglad, caption="Zaznaczony obszar (czerwona ramka)", use_container_width=True)
        
        if st.button("✨ Usuń obiekt AI!", use_container_width=True, type="primary") and co_usunac:
            maska = Image.new("L", (w, h), 0)
            draw_maska = ImageDraw.Draw(maska)
            draw_maska.rectangle([x1, y1, x2, y2], fill=255)
            
            with st.spinner("AI usuwa obiekt (może potrwać 30-60 sekund)..."):
                wynik = usun_obiekt_inpainting(tlo_img, maska, co_usunac)
            
            if wynik:
                wynik_pelny = tlo_img.copy()
                wynik_resized = wynik.resize((x2-x1, y2-y1))
                wynik_pelny.paste(wynik_resized, (x1, y1))
                
                with col2:
                    st.image(wynik_pelny, caption="Po usunięciu obiektu", use_container_width=True)
                    buf = io.BytesIO()
                    wynik_pelny.save(buf, format="JPEG", quality=95)
                    st.session_state.czyste_tlo = wynik_pelny
                    st.download_button("⬇️ Pobierz czyste tło", buf.getvalue(), file_name="czyste_tlo.jpg")
                    st.success("✅ Gotowe! Przejdź do zakładki 'Złóż kompozycję'")

with tab2:
    st.markdown("### Złóż tort na tle")
    
    if "czyste_tlo" not in st.session_state:
        st.info("⬆️ Najpierw usuń obiekt w zakładce 'Usuń obiekt z tła'")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.image(st.session_state.czyste_tlo, caption="Czyste tło", use_container_width=True)
        
        tort_file2 = st.file_uploader("🎂 Wrzuć zdjęcie tortu mamy:", type=["jpg","jpeg","png"], key="tort2")
        
        if tort_file2:
            tort_img = Image.open(tort_file2).convert("RGB")
            with col2:
                st.image(tort_img, caption="Tort mamy", use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1:
                skala = st.slider("📏 Rozmiar tortu", 0.3, 1.0, 0.6)
                pozycja_x = st.slider("↔️ Pozycja pozioma", 0.0, 1.0, 0.5)
            with c2:
                pozycja_y = st.slider("↕️ Pozycja pionowa", 0.0, 1.0, 0.75)
                cien_int = st.slider("🌑 Cień", 0.0, 0.8, 0.3)
            
            if st.button("✨ Złóż kompozycję!", use_container_width=True, type="primary"):
                with st.spinner("Wyciam tort..."):
                    tort_bez_tla = usun_tlo_removebg(tort_img)
                
                if tort_bez_tla:
                    tlo_kwadrat = przytnij_do_kwadratu(st.session_state.czyste_tlo, 1080).convert("RGBA")
                    tort_z_cieniem = dodaj_cien(tort_bez_tla, cien_int)
                    
                    tort_w, tort_h = tort_z_cieniem.size
                    nowy_w = int(1080 * skala)
                    nowy_h = int(tort_h * (nowy_w / tort_w))
                    tort_skalowany = tort_z_cieniem.resize((nowy_w, nowy_h), Image.LANCZOS)
                    
                    x = int((1080 - nowy_w) * pozycja_x)
                    y = int((1080 - nowy_h) * pozycja_y)
                    
                    tlo_kwadrat.paste(tort_skalowany, (x, y), mask=tort_skalowany.split()[3])
                    wynik_final = tlo_kwadrat.convert("RGB")
                    
                    with col3:
                        st.image(wynik_final, caption="✨ Gotowe!", use_container_width=True)
                        buf = io.BytesIO()
                        wynik_final.save(buf, format="JPEG", quality=95)
                        st.download_button("⬇️ Pobierz (1080x1080px)", buf.getvalue(), 
                            file_name="tort_instagram.jpg", mime="image/jpeg", use_container_width=True)
                        st.success("🎉 Gotowe na Instagram!")