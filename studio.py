import streamlit as st
import requests
from PIL import Image, ImageEnhance, ImageFilter
import io
import numpy as np
import re
import urllib.parse
from huggingface_hub import InferenceClient

# ── Constants ─────────────────────────────────────────────────────────────────
LAMA_URL      = "http://localhost:8080"
OUTPUT_SIZE   = 1080
PEXELS_SEARCH = "https://api.pexels.com/v1/search"
REMOVEBG_URL  = "https://api.remove.bg/v1.0/removebg"

# label → Pexels query (label shown on button, query sent to API)
PRESETS = {
    "🪵 Jasne drewno":   "wooden table food photography background",
    "🤍 Biały marmur":   "white marble surface food photography background",
    "🩶 Ciemny beton":   "dark concrete surface food photography background",
    "🌸 Pastelowe":      "pastel pink background food photography flat lay",
    "🍽️ Food studio":   "food photography studio background clean",
    "🧵 Len / tkanina":  "linen fabric texture food photography background",
    "🟫 Ceramika":       "ceramic tile surface food photography background",
    "🪨 Łupek / kamień": "slate stone surface food photography background",
}

HF_SDXL_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

_BG_STYLES = {
    "🪵 Drewno": {
        "prompt": "clean rustic wooden kitchen table surface, top-down view, food photography background, warm natural oak wood grain texture, soft natural studio lighting, ultra-realistic, 4k, no objects",
        "neg":    "people, food, cutlery, objects, text, watermark, harsh shadows, dark tones",
    },
    "🤍 Marmur": {
        "prompt": "clean white marble surface, top-down view, food photography background, elegant subtle grey veins, luxury minimal aesthetic, soft diffused studio lighting, ultra-realistic, 4k, empty surface",
        "neg":    "people, food, objects, text, watermark, harsh shadows, colored stains, cracks",
    },
    "🌸 Pastel": {
        "prompt": "smooth soft pastel pink blush surface, top-down view, food photography background, clean minimalist aesthetic, dreamy soft gradient, professional studio lighting, 4k, empty",
        "neg":    "people, food, objects, text, watermark, dark colors, harsh shadows, strong saturation",
    },
    "🍰 Cukiernicze": {
        "prompt": "clean elegant white confectionery bakery linen surface, top-down view, food photography background, soft warm fabric texture, minimal pastry shop aesthetic, soft diffused light, 4k, empty surface",
        "neg":    "people, food, pastries, objects, text, watermark, harsh shadows, dark tones",
    },
}


# ── Keys ──────────────────────────────────────────────────────────────────────
def _load_keys():
    out = {"pexels": "", "removebg": "", "hf": ""}
    try:
        text = open("klucz.txt", encoding="utf-8").read()
        m = re.search(r'([A-Za-z0-9]{10,})\s*[-–]\s*pexels', text, re.IGNORECASE)
        if m: out["pexels"] = m.group(1)
        m = re.search(r'([A-Za-z0-9]{10,})\s*[-–]\s*remove', text, re.IGNORECASE)
        if m: out["removebg"] = m.group(1)
        m = re.search(r'(hf_[A-Za-z0-9]+)', text)
        if m: out["hf"] = m.group(1)
    except FileNotFoundError:
        pass
    return out

KEYS = _load_keys()

# ── Page ──────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Food Studio AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { display: none; }
.main .block-container { padding-top: 1.5rem; }
.studio-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,.07);
}
.step-row { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.step-num {
    width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    color: #fff; font-size: 18px; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
}
.step-num.done   { background: linear-gradient(135deg,#10b981,#059669); }
.step-num.locked { background: #94a3b8; }
.step-title { font-size: 1.15rem; font-weight: 700; color: #1e293b; line-height: 1.2; }
.step-sub   { font-size: .82rem; color: #64748b; margin-top: 2px; }
.info-box {
    background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px;
    padding: 10px 14px; color: #1d4ed8; font-size: 13px; margin: 10px 0;
}
.warn-box {
    background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px;
    padding: 10px 14px; color: #92400e; font-size: 13px; margin: 10px 0;
}
.sel-pill {
    background: #6366f1; color: #fff; border-radius: 20px;
    padding: 3px 10px; font-size: 11px; font-weight: 600; display: inline-block;
}
</style>""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
_defaults = {
    "bg_photo":    None,   # selected Pexels photo dict
    "bg_bytes":    None,   # current background bytes (Pexels or AI-generated)
    "bg_edited":   False,
    "food_cutout": None,   # PIL RGBA after Remove.bg
    "q":           "food photography background",
    "page":        1,
    "ai_style":    list(_BG_STYLES.keys())[0],
    "hf_gen_bytes": None,  # latest generated image bytes (preview)
    "hf_gen_url":   None,  # full Pollinations URL used for last generation
    "selected_bg":  None,  # AI background chosen directly for Krok 3
    "sl_scale":     0.60,
    "sl_pos_x":     0.50,
    "sl_pos_y":     0.75,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Status kluczy API")
    p_ok  = bool(KEYS["pexels"])
    rb_ok = bool(KEYS["removebg"])
    hf_ok = bool(KEYS["hf"])
    st.markdown(f"{'✅' if p_ok  else '❌'} **Pexels**")
    st.markdown(f"{'✅' if rb_ok else '❌'} **Remove.bg**")
    st.markdown(f"{'✅' if hf_ok else '❌'} **HuggingFace** (SDXL)")
    if not p_ok:
        KEYS["pexels"]   = st.text_input("Klucz Pexels:", type="password", key="sb_pex")
    if not rb_ok:
        KEYS["removebg"] = st.text_input("Klucz Remove.bg:", type="password", key="sb_rbg")
    if not hf_ok:
        KEYS["hf"]       = st.text_input("Klucz HuggingFace (hf_...):", type="password", key="sb_hf")

    st.markdown("---")
    st.markdown("### ⚡ lama-cleaner")
    st.code("lama-cleaner --model lama\n  --device cpu --port 8080", language="bash")

    lama_ok = False
    try:
        lama_ok = requests.get(LAMA_URL, timeout=1.5).status_code < 500
    except Exception:
        pass
    st.markdown(f"{'🟢 Działa' if lama_ok else '🔴 Nie działa'} na {LAMA_URL}")

    st.markdown("---")
    if st.button("🔄 Zacznij od nowa", use_container_width=True):
        for k in ["bg_photo","bg_bytes","food_cutout","selected_bg"]:
            st.session_state[k] = None
        st.session_state.bg_edited = False
        st.rerun()

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def pexels_search(query: str, page: int, api_key: str, per_page: int = 12):
    if not api_key:
        return [], 0
    try:
        r = requests.get(
            PEXELS_SEARCH,
            headers={"Authorization": api_key},
            params={"query": query, "per_page": per_page, "page": page, "orientation": "landscape"},
            timeout=12,
        )
        if r.status_code == 200:
            d = r.json()
            return d.get("photos", []), d.get("total_results", 0)
    except Exception:
        pass
    return [], 0


@st.cache_data(show_spinner=False)
def fetch_bytes(url: str) -> bytes | None:
    try:
        r = requests.get(url, headers={"User-Agent": "FoodStudio/1.0"}, timeout=20)
        return r.content
    except Exception:
        return None


def img_to_bytes(img: Image.Image, fmt="JPEG", quality=95) -> bytes:
    buf = io.BytesIO()
    img.save(buf, fmt, quality=quality)
    return buf.getvalue()


def bytes_to_img(b: bytes, mode="RGB") -> Image.Image:
    return Image.open(io.BytesIO(b)).convert(mode)


def lama_inpaint(image: Image.Image, mask_np: np.ndarray) -> Image.Image | None:
    ib = io.BytesIO(); image.save(ib, "PNG"); ib.seek(0)
    mb = io.BytesIO()
    Image.fromarray(mask_np.astype(np.uint8)).save(mb, "PNG"); mb.seek(0)
    try:
        r = requests.post(
            f"{LAMA_URL}/inpaint",
            files={
                "image": ("img.png", ib, "image/png"),
                "mask":  ("msk.png", mb, "image/png"),
            },
            data={
                "ldmSteps": 25,
                "hdStrategy": "CROP",
                "hdStrategyCropMargin": 128,
                "hdStrategyCropTrigerSize": 1280,
                "hdStrategyResizeLimit": 2048,
            },
            timeout=120,
        )
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        st.error(f"lama-cleaner {r.status_code}: {r.text[:200]}")
    except requests.ConnectionError:
        st.error("Brak połączenia z lama-cleaner. Uruchom komendę z panelu bocznego.")
    return None


def do_removebg(image: Image.Image) -> Image.Image | None:
    buf = io.BytesIO(); image.save(buf, "PNG"); buf.seek(0)
    try:
        r = requests.post(
            REMOVEBG_URL,
            files={"image_file": ("img.png", buf.getvalue(), "image/png")},
            data={"size": "auto"},
            headers={"X-Api-Key": KEYS["removebg"]},
            timeout=30,
        )
        if r.status_code == 200:
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
        err = r.json().get("errors", [{}])[0].get("title", r.text[:120])
        st.error(f"Remove.bg {r.status_code}: {err}")
    except Exception as e:
        st.error(f"Remove.bg błąd: {e}")
    return None


def generate_bg_hf(prompt: str, neg_prompt: str, hf_key: str) -> Image.Image | None:
    # HF classic API no longer serves SDXL/SD on free tier (404).
    # Pollinations.ai is free, no key required, returns high-quality images.
    full_prompt = prompt + ", " + "no " + neg_prompt.replace(", ", ", no ")
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(full_prompt)
        + "?width=1080&height=1080&nologo=true&model=flux&seed="
        + str(hash(prompt) % 99999)
    )
    st.session_state["hf_gen_url"] = url
    st.write(f"🔗 URL do Pollinations: {url}")
    try:
        r = requests.get(url, timeout=120)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        st.error(f"Pollinations błąd {r.status_code}: {r.text[:120]}")
    except requests.Timeout:
        st.error("⏱️ Timeout — serwer generowania nie odpowiedział. Spróbuj ponownie.")
    except Exception as e:
        st.error(f"Błąd generowania: {e}")
    return None


def compose_image(
    bg: Image.Image, fg: Image.Image,
    scale: float, px: float, py: float,
    sh_alpha: float, sh_blur: int,
) -> Image.Image:
    S = OUTPUT_SIZE
    w, h = bg.size; s = min(w, h)
    canvas = (
        bg.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
        .resize((S, S), Image.LANCZOS)
        .convert("RGBA")
    )
    fw, fh = fg.size
    nw = int(S * scale)
    nh = int(fh * nw / fw)
    food = fg.resize((nw, nh), Image.LANCZOS)

    if sh_alpha > 0:
        alpha_ch = food.split()[3]
        sh_mask  = alpha_ch.point(lambda x: int(x * sh_alpha))
        sh_base  = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
        sh_base.putalpha(sh_mask)
        sh_base  = sh_base.filter(ImageFilter.GaussianBlur(sh_blur))
        shadow_canvas = Image.new("RGBA", (nw + 24, nh + 24), (0, 0, 0, 0))
        shadow_canvas.paste(sh_base, (12, 18))
        shadow_canvas.paste(food, (0, 0), mask=food.split()[3])
        food = shadow_canvas
        nw += 24; nh += 24

    x = max(0, int((S - nw) * px))
    y = max(0, int((S - nh) * py))
    canvas.paste(food, (x, y), mask=food.split()[3])
    return canvas.convert("RGB")


def detect_table_line(bg_img: Image.Image) -> float:
    """Returns y-fraction (0=top, 1=bottom) of the detected table/wall edge."""
    small = np.array(bg_img.convert("L").resize((80, 80), Image.LANCZOS), dtype=float)
    vert_grad = np.abs(np.diff(small, axis=0))   # (79, 80)
    row_avg = vert_grad.mean(axis=1)              # mean gradient per row (79,)
    w = 3
    row_smooth = np.convolve(row_avg, np.ones(w) / w, mode="same")
    h = len(row_smooth)
    s, e = int(h * 0.30), int(h * 0.80)
    sub = row_smooth[s:e]
    if sub.max() > row_avg.mean() * 2.0:          # significant edge found
        peak = s + int(np.argmax(sub))
        return peak / h
    return 0.68                                    # flat surface fallback


# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align:center;padding:20px 0 6px">
  <h1 style="font-size:2.2rem;font-weight:800;color:#1e293b;margin:0">🍽️ Food Studio AI</h1>
  <p style="color:#64748b;font-size:1rem;margin-top:6px">
    AI tło &nbsp;/&nbsp; Pexels &nbsp;→&nbsp; lama-cleaner &nbsp;→&nbsp; Remove.bg &nbsp;→&nbsp; 1080×1080 px
  </p>
</div>
""", unsafe_allow_html=True)

step1_done = (st.session_state.bg_photo is not None
              or st.session_state.bg_bytes is not None)
step3_done = st.session_state.food_cutout is not None
selected_bg_ok = st.session_state.get("selected_bg") is not None

# ═════════════════════════════════════════════════════════════════════════════
# KROK 0 — GENERATOR TŁA AI
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="studio-card">', unsafe_allow_html=True)

_ai_done = st.session_state.hf_gen_bytes is not None
b0 = "done" if _ai_done else ""
st.markdown(f"""<div class="step-row">
  <div class="step-num {b0}">{'✓' if _ai_done else '0'}</div>
  <div>
    <div class="step-title">Generator tła AI
      <span style="font-weight:400;color:#94a3b8">(opcjonalnie)</span>
    </div>
    <div class="step-sub">Wygeneruj czyste tło przez Stable Diffusion XL — lub przejdź od razu do Kroku 1</div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Style selector ────────────────────────────────────────────────────────────
st.markdown("**Wybierz styl:**")
style_cols = st.columns(len(_BG_STYLES))
for idx, (style_key, _) in enumerate(_BG_STYLES.items()):
    with style_cols[idx]:
        is_active = st.session_state.ai_style == style_key
        label = f"**{style_key}**" if is_active else style_key
        if st.button(label, key=f"style_{idx}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.ai_style = style_key
            st.rerun()

# ── Editable prompt ───────────────────────────────────────────────────────────
style_data   = _BG_STYLES[st.session_state.ai_style]
custom_prompt = st.text_area(
    "Prompt (edytowalny):",
    value=style_data["prompt"],
    height=80,
    key=f"ai_prompt_{st.session_state.ai_style}",
)

# ── Generate button ───────────────────────────────────────────────────────────
if st.button(
    "✨ Generuj tło AI",
    type="primary",
    use_container_width=True,
    key="btn_gen_ai",
):
    with st.spinner("🎨 Generuję tło AI (Flux)… ~15–30 s"):
        gen_img = generate_bg_hf(custom_prompt, style_data["neg"], KEYS["hf"])
    if gen_img:
        st.session_state.hf_gen_bytes = img_to_bytes(gen_img)
        st.rerun()

# ── Preview + use button ──────────────────────────────────────────────────────
if st.session_state.hf_gen_bytes:
    prev_col, btn_col = st.columns([3, 1])
    with prev_col:
        st.image(
            bytes_to_img(st.session_state.hf_gen_bytes),
            caption=f"Wygenerowane tło — styl: {st.session_state.ai_style}",
            use_container_width=True,
        )
        if st.button("✅ Użyj tego tła jako tło główne", key="use_ai_bg"):
            st.session_state["selected_bg"] = st.session_state["hf_gen_bytes"]
            st.session_state["selected_bg_ok"] = True
            st.success("✅ Tło AI wybrane! Przewiń do Kroku 3.")
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(custom_prompt)}"
        st.markdown(f'**🔗 Link do tła:** [Kliknij tutaj]({url})')
        full_url = st.session_state.get("hf_gen_url", "")
        if full_url:
            st.markdown("**📋 Pełny URL (skopiuj i wklej do przeglądarki):**")
            st.code(full_url, language=None)
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "✅ Użyj jako tło\n→ Krok 2",
            type="primary",
            use_container_width=True,
            key="btn_use_ai_bg",
        ):
            st.session_state.bg_bytes  = st.session_state.hf_gen_bytes
            st.session_state.bg_photo  = None   # nie pochodzi z Pexels
            st.session_state.bg_edited = False
            st.success("✅ Tło AI ustawione!")
            st.rerun()
        if st.button(
            "✅ Użyj tego tła jako tło główne",
            use_container_width=True,
            key="btn_set_selected_bg",
        ):
            st.session_state["selected_bg"] = st.session_state.hf_gen_bytes
            st.success("Tło AI wybrane! Przejdź do Kroku 3.")
            st.rerun()
        if st.button(
            "🔄 Generuj\nponownie",
            use_container_width=True,
            key="btn_regen",
        ):
            with st.spinner("🎨 Generuję…"):
                gen_img = generate_bg_hf(custom_prompt, style_data["neg"], KEYS["hf"])
            if gen_img:
                st.session_state.hf_gen_bytes = img_to_bytes(gen_img)
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# KROK 1 — PEXELS GALLERY
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="studio-card">', unsafe_allow_html=True)

b1 = "done" if step1_done else ""
st.markdown(f"""<div class="step-row">
  <div class="step-num {b1}">{'✓' if step1_done else '1'}</div>
  <div>
    <div class="step-title">Wybierz tło z Pexels
      <span style="font-weight:400;color:#94a3b8">(opcjonalnie — jeśli używasz AI z Kroku 0)</span>
    </div>
    <div class="step-sub">Wyszukaj zdjęcie tła i kliknij Wybierz</div>
  </div>
</div>""", unsafe_allow_html=True)

# Preset chips (2 rows × 4) — label shown, query sent to Pexels
_preset_items = list(PRESETS.items())   # [(label, query), ...]
for row in range(0, len(_preset_items), 4):
    chip_cols = st.columns(4)
    for i, (label, query) in enumerate(_preset_items[row:row + 4]):
        with chip_cols[i]:
            if st.button(label, key=f"chip_{row+i}", use_container_width=True):
                st.session_state.q    = query   # ← targeted Pexels query
                st.session_state.page = 1
                st.rerun()

# Search bar
sc, sb = st.columns([5, 1])
with sc:
    new_q = st.text_input(
        "Szukaj:", value=st.session_state.q,
        placeholder="np. marble, wooden board, dark concrete...",
        label_visibility="collapsed",
    )
with sb:
    if st.button("🔍 Szukaj", type="primary", use_container_width=True):
        st.session_state.q    = new_q
        st.session_state.page = 1
        st.rerun()

# Fetch results
photos, total = pexels_search(
    st.session_state.q, st.session_state.page, KEYS["pexels"]
)

if not KEYS["pexels"]:
    st.markdown('<div class="warn-box">⚠️ Brak klucza Pexels — wpisz go w panelu bocznym lub w pliku klucz.txt</div>', unsafe_allow_html=True)
elif not photos:
    st.markdown('<div class="info-box">🔍 Brak wyników. Spróbuj innego zapytania.</div>', unsafe_allow_html=True)
else:
    gallery_cols = st.columns(4)
    for i, photo in enumerate(photos[:12]):
        with gallery_cols[i % 4]:
            is_sel = (
                st.session_state.bg_photo is not None
                and st.session_state.bg_photo["id"] == photo["id"]
            )
            st.image(photo["src"]["medium"], use_container_width=True)
            if is_sel:
                st.markdown('<div class="sel-pill">✅ Wybrano</div>', unsafe_allow_html=True)
                st.write("")
            else:
                if st.button("Wybierz", key=f"ph_{photo['id']}", use_container_width=True):
                    with st.spinner("Pobieranie tła…"):
                        b = fetch_bytes(photo["src"]["large2x"])
                        if b:
                            st.session_state.bg_photo  = photo
                            st.session_state.bg_bytes  = b
                            st.session_state.bg_edited = False
                            st.session_state.food_cutout = None
                            st.rerun()

    # Pagination
    total_pages = min((total + 11) // 12, 50)
    pa, pb, pc = st.columns([1, 3, 1])
    with pa:
        if st.session_state.page > 1:
            if st.button("← Wstecz", key="pg_prev"):
                st.session_state.page -= 1; st.rerun()
    with pb:
        st.caption(f"Strona {st.session_state.page} / {total_pages}  ·  {total:,} wyników")
    with pc:
        if st.session_state.page < total_pages:
            if st.button("Dalej →", key="pg_next"):
                st.session_state.page += 1; st.rerun()

if step1_done:
    ph = st.session_state.bg_photo
    edited_tag = " · <strong>edytowane</strong>" if st.session_state.bg_edited else ""
    st.markdown(
        f'<div class="info-box">✅ Wybrano: <strong>{ph.get("alt","")[:60]}</strong>'
        f' · {ph.get("photographer","")}{edited_tag}</div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# KROK 2 — LAMA-CLEANER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="studio-card">', unsafe_allow_html=True)

b2 = "done" if st.session_state.bg_edited else ("" if step1_done else "locked")
st.markdown(f"""<div class="step-row">
  <div class="step-num {b2}">{'✓' if st.session_state.bg_edited else '2'}</div>
  <div>
    <div class="step-title">Edytuj tło — lama-cleaner <span style="font-weight:400;color:#94a3b8">(opcjonalnie)</span></div>
    <div class="step-sub">Usuń niechciane elementy lub wgraj własne tło</div>
  </div>
</div>""", unsafe_allow_html=True)

if not step1_done:
    st.markdown('<div class="info-box">⬆️ Najpierw wybierz tło w Kroku 1.</div>', unsafe_allow_html=True)
else:
    bg_img = bytes_to_img(st.session_state.bg_bytes)
    col_l, col_r = st.columns([1, 2])

    with col_l:
        caption = "✅ Edytowane tło" if st.session_state.bg_edited else "Oryginalne tło"
        st.image(bg_img, caption=caption, use_container_width=True)
        st.markdown("**Wgraj wynik z lama-cleaner:**")
        edited_file = st.file_uploader("", type=["jpg","jpeg","png"], key="bg_up")
        if edited_file:
            st.session_state.bg_bytes  = edited_file.read()
            st.session_state.bg_edited = True
            st.rerun()

    with col_r:
        lama_status = "🟢 działa" if lama_ok else "🔴 nie działa"
        st.markdown(f"**lama-cleaner** — {lama_status} &nbsp;(`{LAMA_URL}`)")

        if not lama_ok:
            st.markdown(
                '<div class="warn-box">Uruchom lama-cleaner komendą z panelu bocznego.</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="info-box">'
            '1. Pobierz tło przyciskiem poniżej &nbsp;·&nbsp; '
            '2. Otwórz lama-cleaner w nowej karcie &nbsp;·&nbsp; '
            '3. Wgraj plik, zamaluj obszar → <strong>Inpaint</strong> &nbsp;·&nbsp; '
            '4. Pobierz wynik z lama-cleaner &nbsp;·&nbsp; '
            '5. Wgraj wynik w panelu po lewej'
            '</div>',
            unsafe_allow_html=True,
        )

        dl_col, lm_col = st.columns(2)
        with dl_col:
            st.download_button(
                "⬇️ Pobierz tło do edycji",
                data=st.session_state.bg_bytes,
                file_name="tlo_do_edycji.jpg",
                mime="image/jpeg",
                use_container_width=True,
                type="primary",
            )
        with lm_col:
            st.link_button(
                "🌐 Otwórz lama-cleaner",
                LAMA_URL,
                use_container_width=True,
            )

st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# KROK 3 — KOMPOZYCJA I EKSPORT
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="studio-card">', unsafe_allow_html=True)

b3 = "done" if step3_done else ("" if (step1_done or selected_bg_ok) else "locked")
st.markdown(f"""<div class="step-row">
  <div class="step-num {b3}">{'✓' if step3_done else '3'}</div>
  <div>
    <div class="step-title">Wgraj jedzenie → Wytnij tło → Pobierz 1080×1080</div>
    <div class="step-sub">Remove.bg precyzyjnie wycina produkt, nakładamy na wybrane tło</div>
  </div>
</div>""", unsafe_allow_html=True)

if not step1_done and not selected_bg_ok:
    st.markdown('<div class="info-box">⬆️ Najpierw wybierz tło w Kroku 1 lub wygeneruj tło AI w Kroku 0.</div>', unsafe_allow_html=True)
else:
    if selected_bg_ok:
        st.markdown('<div class="info-box">🎨 Tło: <strong>wygenerowane AI (Krok 0)</strong></div>', unsafe_allow_html=True)
    food_file = st.file_uploader(
        "📷 Zdjęcie jedzenia (tort, ciasto, danie…):",
        type=["jpg","jpeg","png"],
        key="food_up",
    )

    if food_file:
        food_orig = Image.open(food_file).convert("RGB")
        col_a, col_b = st.columns(2)

        with col_a:
            st.image(food_orig, caption="Oryginał", use_container_width=True)
            if not KEYS["removebg"]:
                st.markdown(
                    '<div class="warn-box">⚠️ Brak klucza Remove.bg — wpisz go w panelu bocznym.</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button("✂️ Wytnij tło — Remove.bg", type="primary",
                             use_container_width=True, key="btn_rbg"):
                    with st.spinner("Wycinanie przez Remove.bg…"):
                        cutout = do_removebg(food_orig)
                        if cutout:
                            st.session_state.food_cutout = cutout
                            st.rerun()

        with col_b:
            if st.session_state.food_cutout is not None:
                st.image(
                    st.session_state.food_cutout,
                    caption="Po wycięciu tła",
                    use_container_width=True,
                )
            else:
                st.markdown('<div class="info-box">👈 Kliknij Wytnij tło aby usunąć tło ze zdjęcia.</div>', unsafe_allow_html=True)

        if st.session_state.food_cutout is not None:
            st.markdown("---")
            st.markdown("### 🎛️ Kompozycja")

            # Build background early — needed for auto-detect
            bg_src = st.session_state["selected_bg"] if selected_bg_ok else st.session_state.bg_bytes
            if isinstance(bg_src, bytes):
                bg_final = Image.open(io.BytesIO(bg_src)).convert("RGB")
            else:
                bg_final = bg_src
            food_rgba = st.session_state.food_cutout

            # Auto-positioning row
            auto_btn_col, auto_info_col = st.columns([1, 2])
            with auto_btn_col:
                if st.button("🎯 Auto-ustaw pozycję", type="primary",
                             use_container_width=True, key="btn_auto_pos"):
                    t = detect_table_line(bg_final)
                    auto_sc = 0.40
                    fw, fh = food_rgba.size
                    nh = int(OUTPUT_SIZE * auto_sc * fh / fw)
                    S = OUTPUT_SIZE
                    py = max(0.0, min(1.0, (t * S - nh) / (S - nh)))
                    st.session_state["sl_scale"] = auto_sc
                    st.session_state["sl_pos_x"] = 0.50
                    st.session_state["sl_pos_y"] = round(py, 2)
                    st.session_state["_auto_table_y"] = t
                    st.rerun()
            with auto_info_col:
                if "_auto_table_y" in st.session_state:
                    t_pct = int(st.session_state["_auto_table_y"] * 100)
                    st.markdown(
                        f'<div class="info-box">🔍 Wykryto linię stołu: <strong>{t_pct}%</strong> od góry obrazu</div>',
                        unsafe_allow_html=True,
                    )

            c1, c2, c3 = st.columns(3)
            with c1:
                scale = st.slider("📏 Rozmiar jedzenia", 0.20, 1.00, step=0.01, key="sl_scale")
                pos_x = st.slider("↔️ Pozycja X",        0.00, 1.00, step=0.01, key="sl_pos_x")
                pos_y = st.slider("↕️ Pozycja Y",        0.00, 1.00, step=0.01, key="sl_pos_y")
            with c2:
                sh_a  = st.slider("🌑 Cień (intensywność)", 0.00, 0.80, 0.35, 0.05)
                sh_b  = st.slider("💨 Cień (rozmycie)",       0,   50,   18,  1)
            with c3:
                bright = st.slider("☀️ Jasność",   0.50, 1.80, 1.10, 0.05)
                contr  = st.slider("🌗 Kontrast",  0.50, 1.80, 1.05, 0.05)
                sat    = st.slider("🎨 Nasycenie", 0.50, 2.00, 1.15, 0.05)

            food_rgb = food_rgba.convert("RGB")
            food_rgb = ImageEnhance.Brightness(food_rgb).enhance(bright)
            food_rgb = ImageEnhance.Contrast(food_rgb).enhance(contr)
            food_rgb = ImageEnhance.Color(food_rgb).enhance(sat)
            food_adj = food_rgb.convert("RGBA")
            food_adj.putalpha(food_rgba.split()[3])  # restore original alpha

            result = compose_image(bg_final, food_adj, scale, pos_x, pos_y, sh_a, sh_b)

            res_col, dl_col = st.columns([3, 1])
            with res_col:
                st.image(result, caption="Podgląd kompozycji 1080×1080 px", use_container_width=True)

            with dl_col:
                st.markdown("### ⬇️ Pobierz")

                jpg_b = img_to_bytes(result, "JPEG", 95)
                st.download_button(
                    "📸 JPEG · 1080px\n(Instagram)",
                    jpg_b,
                    "food_studio_1080.jpg",
                    "image/jpeg",
                    use_container_width=True,
                    type="primary",
                )

                png_buf = io.BytesIO()
                result.save(png_buf, "PNG")
                st.download_button(
                    "🖼️ PNG\n(bez kompresji)",
                    png_buf.getvalue(),
                    "food_studio_1080.png",
                    "image/png",
                    use_container_width=True,
                )

                st.markdown("---")
                st.caption(f"Rozmiar: **1080×1080 px**")
                st.caption(f"Jedzenie: **{int(scale*100)}%** szerokości")
                st.success("🎉 Gotowe!")

st.markdown('</div>', unsafe_allow_html=True)
