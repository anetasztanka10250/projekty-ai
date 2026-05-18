# Projekty AI — Aneta Sztanka

Kolekcja aplikacji zbudowanych z pomocą AI (Claude Code, Gemini API, HuggingFace).

## Projekty

| Projekt | Opis | Technologie |
|---------|------|-------------|
| [CVSkan](./cvskan) | Polski analizator CV i wyszukiwarka ofert pracy | Next.js, Gemini AI |
| [Audyt Szafy](./szafa) | Zarządzanie garderobą z analizą AI | Flask, PostgreSQL, Together AI |
| [Studio AI](#studio-ai) | Streamlit studio: tła, inpainting, generowanie obrazów | Streamlit, HuggingFace, Pexels |
| [Kreator Banerów](#kreator-banerów) | Generator profesjonalnych banerów produktowych | Streamlit, Remove.bg |
| [Wytnij Torty](#wytnij-torty) | Batch usuwanie tła ze zdjęć | Remove.bg API |
| [Inpainting](#inpainting) | Edycja zdjęć przez AI — zamiana tła | Streamlit, HuggingFace SD |
| [Chatbot](#pozostałe-skrypty) | Chatbot w przeglądarce i terminalu | Python, Groq, LLaMA |
| [Agent AI](#pozostałe-skrypty) | Agent z wyszukiwaniem internetowym | Python, Groq, Tavily |

---

## Studio AI

`studio.py` — Streamlit app do tworzenia kompozycji produktowych.

**Funkcje:**
- Wyszukiwanie i pobieranie teł z Pexels
- Generowanie teł AI przez Stable Diffusion XL (HuggingFace)
- Usuwanie tła z produktów (Remove.bg)
- Inpainting z LaMa (lokalny serwer)

```bash
pip install streamlit pillow requests numpy huggingface_hub
streamlit run studio.py
```

Wpisz klucze API w interfejsie (Pexels, Remove.bg, HuggingFace).

---

## Kreator Banerów

`baner_kreator.py` — generator banerów 3000×1400 px.

**Funkcje:**
- Tło gradientowe lub własne zdjęcie
- Automatyczne usuwanie tła z produktu (Remove.bg)
- Dodawanie logo, tekstu, ceny
- Eksport PNG gotowy do druku/internetu

```bash
pip install streamlit pillow requests numpy
streamlit run baner_kreator.py
```

---

## Wytnij Torty

`wytnij_torty.py` — skrypt wsadowy do usuwania tła ze zdjęć tortów.

Umieść pliki `tort1.png`, `tort2.png`, `tort3.png` w folderze roboczym, następnie:

```bash
pip install requests pillow
python wytnij_torty.py
```

---

## Inpainting

`inpainting.py` — Streamlit app do edycji zdjęć przez AI.

**Funkcje:**
- Zamiana tła na gotowe presety (drewno, marmur, pastel...)
- Inpainting przez Stable Diffusion (HuggingFace API)
- Wynik 1080×1080 px gotowy na Instagram

```bash
pip install streamlit pillow requests numpy opencv-python
streamlit run inpainting.py
```

---

## Pozostałe skrypty

| Plik | Opis |
|------|------|
| `chatbot.py` | Chatbot terminalowy (Groq + LLaMA 3.3) |
| `app.py` | Chatbot webowy w Streamlit |
| `agent.py` | Agent AI z wyszukiwaniem internetowym (Groq + Tavily) |
| `rag.py` | Analizator PDF z pytaniami (RAG) |
| `kalkulator.py` | Prosty kalkulator Python |
| `niemiecki.py` | Nauka języka niemieckiego z AI |
| `prawo.py` | Asystent prawa dziecka |
| `cukiernia.py` | Asystent cukierniczy AI |
| `tlo_ai.py` | Generator teł AI |
| `magic_edit.py` | Edycja zdjęć poleceniami AI |

---

## Wymagania

```bash
pip install -r requirements.txt
```

Klucze API przechowuj lokalnie w `klucz.txt` (plik jest w `.gitignore`) lub jako zmienne środowiskowe.

---

*Zbudowane z pomocą [Claude Code](https://claude.ai/code) — Junior AI Developer*
