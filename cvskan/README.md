# CVSkan.pl

Polski analizator CV i wyszukiwarka ofert pracy napędzana AI.

## Funkcje

- **Analiza CV** — ocena ATS z wynikiem procentowym, lista brakujących słów kluczowych i sugestii
- **Wyszukiwarka ofert** — 20+ portali równolegle (Pracuj.pl, JustJoinIT, NoFluffJobs, OLX, LinkedIn...)
- **Ukryte oferty** — bezpośrednio ze stron karier firm, niedostępne na głównych portalach
- **Zagraniczne remote** — oferty zdalne przyjazne dla obywateli UE (bez US work authorization)
- **Tracker aplikacji** — historia wysłanych CV z notatkami i statusami
- **Generator CV** — CV dopasowane pod konkretną ofertę pracy
- **Ulubione** — zapisywanie ofert z trwałym ID (stabilny fingerprint: firma+tytuł+lokalizacja)
- **Auto-filtr junior** — automatyczne odrzucanie ofert senior/mid gdy zaznaczono niski poziom doświadczenia

## Technologie

- **Frontend:** Next.js 16, React 19, Tailwind CSS v4, TypeScript
- **AI:** Google Gemini API (gemini-2.0-flash) z Google Search grounding
- **Baza danych:** Supabase (PostgreSQL) — opcjonalnie
- **Deploy:** Vercel

## Uruchomienie lokalne

```bash
cd cvskan
npm install
```

Utwórz plik `.env.local`:
```
GEMINI_API_KEY_1=twoj_klucz
GEMINI_API_KEY_2=twoj_klucz_backup
GEMINI_API_KEY_3=twoj_klucz_backup2
```

```bash
npm run dev
```

Aplikacja dostępna pod `http://localhost:3000`.

## Zmienne środowiskowe

| Zmienna | Opis |
|---------|------|
| `GEMINI_API_KEY_1` | Główny klucz Gemini API |
| `GEMINI_API_KEY_2` | Backup (fallback przy rate limit) |
| `GEMINI_API_KEY_3` | Backup (fallback przy rate limit) |

## Struktura projektu

```
cvskan/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analyze-cv/   # Analiza CV przez Gemini
│   │   │   ├── generate-cv/  # Generowanie CV
│   │   │   └── search-jobs/  # Wyszukiwanie ofert
│   │   └── page.tsx
│   ├── components/           # React components
│   └── lib/
│       ├── types.ts          # Typy + computeOfferId()
│       ├── gemini.ts         # Klient Gemini z fallback
│       └── competition.ts    # Obliczanie poziomu konkurencji
```

---

*Zbudowane z pomocą [Claude Code](https://claude.ai/code)*
