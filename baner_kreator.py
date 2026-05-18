import io
import os

import numpy as np
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REMOVEBG_API_KEY = "AjFQmET8gkH3zDo79tdN4P5K"
BANNER_W, BANNER_H = 3000, 1400


# ─── Helpers ──────────────────────────────────────────────────────────────────

def remove_bg(image_bytes: bytes) -> Image.Image | None:
    resp = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": ("img.png", image_bytes, "image/png")},
        data={"size": "auto"},
        headers={"X-Api-Key": REMOVEBG_API_KEY},
        timeout=30,
    )
    if resp.status_code == 200:
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    st.error(f"Remove.bg błąd {resp.status_code}: {resp.text[:300]}")
    return None


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def darken(rgb: tuple, factor: float = 0.38) -> tuple:
    return tuple(int(c * factor) for c in rgb)


def gradient_bg(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    t = np.linspace(0, 1, h)[:, None]
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for i, (v1, v2) in enumerate(zip(c1, c2)):
        col = (v1 + (v2 - v1) * t).astype(np.uint8)
        arr[:, :, i] = np.broadcast_to(col, (h, w))
    return Image.fromarray(arr, "RGB").convert("RGBA")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        f"C:/Windows/Fonts/{'arialbd.ttf' if bold else 'arial.ttf'}",
        f"C:/Windows/Fonts/{'calibrib.ttf' if bold else 'calibri.ttf'}",
        f"C:/Windows/Fonts/{'segoeui.ttf'}",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf".format("-Bold" if bold else ""),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def shadowed_text(
    draw: ImageDraw.ImageDraw,
    pos: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    offset: int = 5,
):
    draw.text((pos[0] + offset, pos[1] + offset), text, font=font, fill=(0, 0, 0, 110))
    draw.text(pos, text, font=font, fill=fill)


# ─── Banner builder ───────────────────────────────────────────────────────────

def make_banner(
    name: str,
    subtitle: str,
    city: str,
    phone: str,
    bg_hex: str,
    cakes: list,
) -> Image.Image:
    bg = hex_to_rgb(bg_hex)
    canvas = gradient_bg(BANNER_W, BANNER_H, darken(bg, 0.30), bg)
    draw = ImageDraw.Draw(canvas)

    GOLD = (212, 175, 55, 255)
    WHITE = (255, 255, 255, 255)
    CREAM = (255, 245, 215, 255)

    # Top & bottom gold stripes
    draw.rectangle([0, 0, BANNER_W, 16], fill=GOLD)
    draw.rectangle([0, BANNER_H - 16, BANNER_W, BANNER_H], fill=GOLD)

    # Subtle dark overlay on the left text panel
    panel = Image.new("RGBA", (1060, BANNER_H - 32), (0, 0, 0, 75))
    canvas.alpha_composite(panel, (0, 16))

    # Vertical gold accent bar
    draw.rectangle([1040, 16, 1052, BANNER_H - 16], fill=GOLD)

    # Fonts
    fn_title = load_font(180, bold=True)
    fn_sub = load_font(88)
    fn_info = load_font(72)

    MARGIN = 90
    y = 150

    # ── Bakery name ──
    shadowed_text(draw, (MARGIN, y), name, fn_title, WHITE, offset=6)
    bbox = draw.textbbox((MARGIN, y), name, font=fn_title)
    y = bbox[3] + 28

    # Gold divider under name
    draw.rectangle([MARGIN, y, MARGIN + 740, y + 8], fill=GOLD)
    y += 50

    # ── Subtitle ──
    shadowed_text(draw, (MARGIN, y), subtitle, fn_sub, CREAM, offset=4)
    bbox = draw.textbbox((MARGIN, y), subtitle, font=fn_sub)
    y = bbox[3] + 80

    # ── City ──
    shadowed_text(draw, (MARGIN, y), f"  {city}", fn_info, WHITE, offset=3)
    y += 110

    # ── Phone ──
    shadowed_text(draw, (MARGIN, y), f"  {phone}", fn_info, WHITE, offset=3)

    # ── Cake images ──
    right_x = 1080
    available_w = BANNER_W - right_x - 40
    slot_w = available_w // 3
    max_cake_h = BANNER_H - 60

    for i, cake in enumerate(cakes[:3]):
        if cake is None:
            continue
        c = cake.copy()
        c.thumbnail((slot_w - 30, max_cake_h), Image.LANCZOS)

        paste_x = right_x + i * slot_w + (slot_w - c.width) // 2
        paste_y = BANNER_H - c.height - 16

        # Elliptical drop shadow
        shadow = Image.new("RGBA", (BANNER_W, BANNER_H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse(
            [paste_x + 40, paste_y + c.height - 10,
             paste_x + c.width - 40, paste_y + c.height + 50],
            fill=(0, 0, 0, 100),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        canvas.alpha_composite(shadow)
        canvas.alpha_composite(c, (paste_x, paste_y))

    return canvas.convert("RGB")


# ─── Streamlit UI ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Kreator Banerów Cukierniczych", layout="wide", page_icon="🎂")
st.title("🎂 Kreator Banerów Cukierniczych")

# Session state – cache Remove.bg results to avoid redundant API calls
if "proc_imgs" not in st.session_state:
    st.session_state.proc_imgs = [None, None, None]
if "img_hashes" not in st.session_state:
    st.session_state.img_hashes = [None, None, None]

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("✏️ Dane cukierni")
    name = st.text_input("Nazwa cukierni", "Cukiernia Słodki Raj")
    subtitle = st.text_input("Podtytuł", "Torty artystyczne na zamówienie")
    city = st.text_input("Miasto", "Warszawa")
    phone = st.text_input("Telefon", "+48 123 456 789")

    st.divider()
    st.subheader("🎨 Kolor tła")
    COLORS = {
        "Różowy":       "#C2185B",
        "Bordowy":      "#880E4F",
        "Złoty brąz":   "#BF6900",
        "Granatowy":    "#1A237E",
        "Szmaragdowy":  "#1B5E20",
        "Fioletowy":    "#4A148C",
        "Czekoladowy":  "#3E2723",
        "Turkusowy":    "#006064",
    }
    choice = st.selectbox("Schemat kolorów", list(COLORS.keys()))
    bg_hex = COLORS[choice]
    if st.checkbox("Własny kolor"):
        bg_hex = st.color_picker("Wybierz kolor", bg_hex)
    st.markdown(
        f'<div style="background:{bg_hex};height:38px;border-radius:7px;'
        f'border:2px solid rgba(255,255,255,0.3);margin-top:6px"></div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("📸 Zdjęcia tortów")
    st.caption("Tło zostanie usunięte automatycznie przez Remove.bg")
    uploads = [
        st.file_uploader(f"Tort {i + 1}", type=["jpg", "jpeg", "png", "webp"], key=f"u{i}")
        for i in range(3)
    ]

# ── Process uploads (Remove.bg only when file changes) ────────────────────────
for i, f in enumerate(uploads):
    if f is not None:
        data = f.read()
        h = hash(data)
        if st.session_state.img_hashes[i] != h:
            with st.spinner(f"Usuwanie tła — tort {i + 1}…"):
                result = remove_bg(data)
            st.session_state.proc_imgs[i] = result
            st.session_state.img_hashes[i] = h
    else:
        st.session_state.proc_imgs[i] = None
        st.session_state.img_hashes[i] = None

# ── Build & display banner ─────────────────────────────────────────────────────
banner = make_banner(name, subtitle, city, phone, bg_hex, st.session_state.proc_imgs)

st.subheader("👁️ Podgląd baneru")
preview = banner.copy()
preview.thumbnail((1400, 700), Image.LANCZOS)
st.image(preview, width="stretch")

# ── Download ───────────────────────────────────────────────────────────────────
buf = io.BytesIO()
banner.save(buf, "PNG")
buf.seek(0)

st.download_button(
    label="⬇️ Pobierz baner PNG (3000 × 1400 px)",
    data=buf,
    file_name="baner_cukiernia.png",
    mime="image/png",
)
