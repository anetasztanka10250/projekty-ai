# Audyt Szafy

Aplikacja webowa do zarządzania garderobą z analizą AI. Prześlij zdjęcie ubrania, a AI opisze je i skategoryzuje.

## Funkcje

- Dodawanie ubrań ze zdjęciem i automatyczną analizą AI (Together AI / Llama Vision)
- Kategoryzacja: typ, stan, kolor, pora roku
- Przeglądanie i filtrowanie garderoby
- Eksport listy do CSV
- Audyt szafy — AI analizuje całą garderobę i sugeruje stylizacje
- Baza danych PostgreSQL (Supabase)

## Technologie

- **Backend:** Python, Flask
- **Baza danych:** PostgreSQL (Supabase)
- **AI:** Together AI (Llama 3.2 Vision)
- **Frontend:** HTML, CSS, Jinja2

## Uruchomienie

```bash
cd szafa
pip install -r requirements.txt
```

Utwórz plik `.env`:
```
TOGETHER_API_KEY=twoj_klucz_together_ai
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

```bash
python app.py
```

Aplikacja dostępna pod `http://localhost:5000`.

## Wymagania

```
flask
requests
psycopg2-binary
python-dotenv
```

---

*Zbudowane z pomocą [Claude Code](https://claude.ai/code)*
