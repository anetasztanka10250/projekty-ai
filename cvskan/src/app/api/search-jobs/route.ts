import { NextRequest, NextResponse } from "next/server";
import type { JobOffer, JobSearchFilters, SearchMode } from "@/lib/types";
import { computeOfferId } from "@/lib/types";
import { checkRateLimit } from "@/lib/rate-limiter";
import { calcCompetition, hoursAgo } from "@/lib/competition";
import { fetchRemotive, fetchJobicy } from "@/lib/direct-apis";
import { callGeminiWithFallback } from "@/lib/gemini";
import { verifyLinks } from "@/lib/link-checker";

export const runtime = "nodejs";
export const maxDuration = 120;

// ── Portale groups ──────────────────────────────────────────────────────────
const PORTAL_GROUPS = [
  {
    name: "JustJoinIT + Polskie IT",
    portals: ["justjoin.it", "nofluffjobs.com", "rocketjobs.pl", "bulldogjob.pl", "theprotocol.it", "solid.jobs"],
  },
  {
    name: "Polskie ogólne",
    portals: ["pracuj.pl", "olx.pl/praca", "praca.pl", "kariera.pl", "goldenline.pl", "gratka.pl/praca", "monsterpolska.pl"],
  },
  {
    name: "Międzynarodowe",
    portals: ["linkedin.com/jobs", "indeed.com/pl", "glassdoor.com", "jooble.org/pl"],
  },
];

// ── Hidden offer portals ─────────────────────────────────────────────────────
const HIDDEN_QUERIES = (pos: string, loc?: string) => [
  `"${pos}" ${loc ? `"${loc}"` : ""} "aplikuj" OR "dołącz do nas" OR "join us" -site:pracuj.pl -site:linkedin.com -site:justjoin.it -site:nofluffjobs.com -site:olx.pl`,
  `"${pos}" "kariera" OR "careers" ${loc ? `"${loc}"` : ""} site:*.pl -site:pracuj.pl -site:linkedin.com`,
  `"${pos}" "oferta pracy" OR "job offer" "apply" ${loc ? loc : "Polska"} -site:pracuj.pl -site:justjoin.it -site:nofluffjobs.com`,
  `"${pos}" "praca" "formularz" OR "wyślij CV" OR "send cv" ${loc ? `"${loc}"` : ""} -site:pracuj.pl`,
  `"${pos}" hiring ${loc ? `"${loc}"` : "Poland"} "apply now" OR "aplikuj teraz" -site:linkedin.com -site:indeed.com`,
];

// ── Remote/international portals ─────────────────────────────────────────────
// Wyłącznie darmowe portale — dailyremote.com jest płatny
const REMOTE_PORTALS = [
  // Remote (darmowe)
  "remote.co", "weworkremotely.com", "remoteok.com", "himalayas.app", "arc.dev",
  "euremotejobs.com", "justremote.co", "remote.io", "jobspresso.co", "wellfound.com",
  // Ogólne międzynarodowe (darmowe)
  "indeed.com", "glassdoor.com", "eurojobs.com", "jobs.eu", "eurojobs.com",
  // Relokacja i EU
  "relocate.me", "otta.com",
];
const REMOTE_QUERIES = (pos: string) => [
  `"${pos}" "remote" "EU welcome" OR "Europe welcome" OR "hire in Poland" OR "open to EU"`,
  `"${pos}" "remote" "contractors welcome" OR "B2B contract" "Europe" OR "Poland"`,
  `"${pos}" "work from anywhere" -"US only" -"US citizens only" -"work authorization"`,
  `"${pos}" site:*.com/careers OR site:*.io/careers OR site:*.co/careers "remote" "EU" OR "worldwide"`,
  `"${pos}" "open to EU" OR "EU residents" OR "Polish candidates" "remote" "apply"`,
];

// ── Helpers ──────────────────────────────────────────────────────────────────
function buildFilters(filters: JobSearchFilters): string {
  return [
    filters.location ? `- Lokalizacja: ${filters.location}` : null,
    filters.workMode?.length ? `- Tryb pracy: ${filters.workMode.join(", ")}` : null,
    filters.salaryMin ? `- Min. wynagrodzenie: ${filters.salaryMin} zł` : null,
    filters.contractType?.length ? `- Typ umowy: ${filters.contractType.join(", ")}` : null,
    filters.timeAdded && filters.timeAdded !== "any"
      ? `- Czas dodania: ostatnie ${filters.timeAdded}`
      : null,
  ]
    .filter(Boolean)
    .join("\n") || "- Brak dodatkowych filtrów";
}

function buildExperience(filters: JobSearchFilters): string {
  const levels = (filters.experienceLevels ?? []).filter(Boolean);
  if (!levels.length) return "";

  const LABELS: Record<string, string> = {
    "0":   "bez doświadczenia (staż, 0 lat)",
    "0-1": "junior, do 1 roku",
    "1-2": "1–2 lata",
    "2-3": "2–3 lata",
    "3-5": "3–5 lat",
    "5+":  "5+ lat (senior)",
  };

  const desc = levels.map((l) => LABELS[l] ?? l).join(" LUB ");
  const hasSenior = levels.includes("5+") || levels.includes("3-5");

  return `\nFILTR DOŚWIADCZENIA (OR) — oferta musi pasować do JEDNEGO z: ${desc}.${
    !hasSenior ? ' ODRZUĆ oferty z tytułem Senior/Lead/Principal lub wymagające 5+ lat.' : ""
  }`;
}

function buildSearchQuery(filters: JobSearchFilters): string {
  const pos = filters.position?.trim();
  const kws = (filters.keywords ?? []).map((k) => k?.trim()).filter(Boolean);

  if (pos && kws.length > 0) return `"${pos}" ${kws.map((k) => `"${k}"`).join(" ")}`;
  if (pos) return `"${pos}"`;
  if (kws.length > 0) return kws.map((k) => `"${k}"`).join(" ");
  return filters.location ? `oferty pracy "${filters.location}"` : "oferty pracy";
}

function buildKeywordsInstruction(filters: JobSearchFilters): string {
  const kws = (filters.keywords ?? []).map((k) => k?.trim()).filter(Boolean);
  if (!kws.length) return "";
  return `\nOBOWIĄZKOWE słowa kluczowe (AND — wszystkie muszą wystąpić w ofercie): ${kws.map((k) => `"${k}"`).join(", ")}. Odrzuć oferty gdzie brakuje choćby jednego.`;
}

const LINK_INSTRUCTION = `
WAŻNE — LINKI: Podawaj TYLKO prawdziwe, istniejące linki bezpośrednio do ogłoszenia.
Jeśli nie jesteś pewny czy link istnieje lub prowadzi do konkretnej oferty — nie podawaj go wcale (zostaw "url": "").
Nie wymyślaj URL-i. Nie podawaj linków do strony głównej portalu ani kategorii.`;

function buildPortalPrompt(filters: JobSearchFilters, groupName: string, portals: string[]): string {
  return `Jesteś ekspertem rynku pracy. Szukaj aktualnych ofert dla: ${buildSearchQuery(filters)}.

Filtry:
${buildFilters(filters)}
${buildExperience(filters)}${buildKeywordsInstruction(filters)}
Przeszukaj KAŻDY z tych portali osobnym zapytaniem Google Search (${groupName}):
${portals.map((p) => `- ${p}`).join("\n")}

Szukaj ofert z ostatnich ${filters.timeAdded === "1h" ? "godziny" : filters.timeAdded === "12h" ? "12 godzin" : filters.timeAdded === "24h" ? "24 godzin" : filters.timeAdded === "3d" ? "3 dni" : filters.timeAdded === "7d" ? "tygodnia" : "14 dni"}.
Zwracaj TYLKO oferty dodane w ciągu ostatnich 30 dni. Ignoruj starsze ogłoszenia.
Cel: 25-30 konkretnych ofert z każdego portalu.
${LINK_INSTRUCTION}
Zwróć WYŁĄCZNIE JSON:
{"oferty":[{"title":"...","company":"...","location":"...","work_mode":"zdalna|hybrydowa|stacjonarna","salary":"...lub null","contract_type":"B2B|UoP|Zlecenie|null","published_at":"...","url":"...","sources":["${portals[0]}"],"description":"...","is_hidden":false,"is_remote_foreign":false,"eu_friendly":false}]}`;
}

function buildHiddenPrompt(filters: JobSearchFilters, query: string): string {
  return `Szukaj ofert pracy dla: ${buildSearchQuery(filters)} BEZPOŚREDNIO na stronach karier firm, omijając główne portale pracy.

Zapytanie Google Search: ${query}

Filtry: ${buildFilters(filters)}${buildExperience(filters)}${buildKeywordsInstruction(filters)}
Zwracaj TYLKO oferty dodane w ciągu ostatnich 30 dni. Ignoruj starsze ogłoszenia.

Znajdź 10-15 ofert niedostępnych na głównych portalach. Dla każdej oferty:
- Sprawdź że to bezpośrednia strona kariery firmy, nie portal agregujący
${LINK_INSTRUCTION}
Zwróć WYŁĄCZNIE JSON:
{"oferty":[{"title":"...","company":"...","location":"...","work_mode":"...","salary":null,"contract_type":null,"published_at":"...","url":"...","sources":["strona kariery firmy"],"description":"...","is_hidden":true,"is_remote_foreign":false,"eu_friendly":false}]}`;
}

function buildRemotePrompt(filters: JobSearchFilters): string {
  const sq = buildSearchQuery(filters);
  return `Szukaj zagranicznych ofert pracy zdalnej dla: ${sq}. Szukaj TYLKO ofert dostępnych dla obywateli EU/Polski bez wizy.

Przeszukaj portale:
${REMOTE_PORTALS.map((p) => `- ${p}`).join("\n")}

Użyj też zapytań:
${REMOTE_QUERIES(sq).map((q) => `- ${q}`).join("\n")}
${buildKeywordsInstruction(filters)}
Zwracaj TYLKO oferty dodane w ciągu ostatnich 30 dni. Ignoruj starsze ogłoszenia.
OBOWIĄZKOWE kryteria:
- Oferta musi być otwarta dla kandydatów z EU/Polski
- NIE musi posiadać US work authorization
- Preferuj: "worldwide", "EU welcome", "contractors OK", "B2B"
- ODRZUĆ: "US only", "must be based in US", "work authorization required", "US citizens"
${LINK_INSTRUCTION}
Zwróć WYŁĄCZNIE JSON:
{"oferty":[{"title":"...","company":"...","location":"Remote","work_mode":"zdalna","salary":"...lub null","contract_type":"B2B|null","published_at":"...","url":"...","sources":["remote.co"],"description":"...","is_hidden":false,"is_remote_foreign":true,"eu_friendly":true}]}`;
}

// ── Post-fetch filter ─────────────────────────────────────────────────────────
const EXCLUDED_REGIONS = [
  "latam", "latin america", "us only", "americas", "north america only",
  "usa only", "united states only", "us-only", "us residents only",
  "us citizens only", "must be in us",
];

const SYNONYMS: Record<string, string[]> = {
  junior:   ["junior", "młodszy", "entry level", "entry-level", "początkujący", "jr"],
  senior:   ["senior", "starszy", "sr", "principal"],
  manager:  ["manager", "kierownik", "menedżer", "menager", "head"],
  lead:     ["lead", "lider", "kierownik", "head", "manager"],
  developer:["developer", "deweloper", "programista", "dev"],
  engineer: ["engineer", "inżynier", "dev", "developer"],
  analyst:  ["analyst", "analityk", "analist"],
  designer: ["designer", "projektant", "ux", "ui"],
  tester:   ["tester", "qa", "quality assurance", "kontroler jakości"],
};

function expandWord(word: string): string[] {
  return SYNONYMS[word] ?? [word];
}

function isPolandSearch(location?: string): boolean {
  const loc = (location || "").toLowerCase();
  return loc.includes("polska") || loc.includes("poland") || loc.includes("cała polska");
}

// ── Junior auto-filter ────────────────────────────────────────────────────────
const JUNIOR_TRIGGER_LEVELS = new Set(["0", "0-1", "1-2"]);
const SENIOR_OVERRIDE_LEVELS = new Set(["3-5", "5+"]);

// Patterns in title or description that mark a senior/mid offer
const SENIOR_PATTERNS = [
  /\bsenior\b/i,    /\bstarszy\b/i,   /\bsr\b/i,
  /\blead\b/i,      /\bhead\s+of\b/i, /\bprincipal\b/i,
  /\bexpert\b/i,    /\bekspert\b/i,   /\barchitect\b/i,
  /\bmid\b/i,       /\bregular\b/i,   /\bmedior\b/i,
  /min\.?\s*3\s*lat/i,          /min\.?\s*4\s*lat/i,          /min\.?\s*5\s*lat/i,
  /\b3\+\s*years?\b/i,          /\b4\+\s*years?\b/i,          /\b5\+\s*years?\b/i,
  /\b3\s*years?\s*(?:of\s*)?experience\b/i,
  /\b4\s*years?\s*(?:of\s*)?experience\b/i,
  /\bat\s+least\s+[345]\b/i,
];

// Patterns that explicitly mark a junior/entry offer — override the rejection
const JUNIOR_SAFE_PATTERNS = [
  /\bjunior\b/i,           /\bm[łl]odszy\b/i,         /\bentry[\s-]level\b/i,
  /\bjr\b/i,               /\bassociate\b/i,            /\btrainee\b/i,
  /\bsta[zż]ysta\b/i,      /\bintern\b/i,
  /\b0[\s\-–]2\s*lat/i,    /\b1[\s\-–]2\s*lat/i,       /\bdo\s+2\s*lat\b/i,
  /\bno\s+experience\b/i,  /\bbez\s+do[sś]wiadczenia\b/i,
  /\bfresh\s+graduate\b/i, /\babsolwent\b/i,
];

function isSeniorOffer(offer: JobOffer): boolean {
  const text = `${offer.title ?? ""} ${offer.description ?? ""}`.toLowerCase();
  if (JUNIOR_SAFE_PATTERNS.some((p) => p.test(text))) return false;
  return SENIOR_PATTERNS.some((p) => p.test(text));
}

function filterOffers(offers: JobOffer[], filters: JobSearchFilters): JobOffer[] {
  const levels = filters.experienceLevels ?? [];
  const applyJuniorFilter =
    levels.some((l) => JUNIOR_TRIGGER_LEVELS.has(l)) &&
    !levels.some((l) => SENIOR_OVERRIDE_LEVELS.has(l));

  return offers.filter((offer) => {
    // Position filter: EVERY word (or its synonym) must appear in title or description
    if (filters.position?.trim()) {
      const posWords = filters.position.toLowerCase().split(/\s+/).filter(Boolean);
      const text = `${offer.title} ${offer.description}`.toLowerCase();
      const allMatch = posWords.every((w) => expandWord(w).some((syn) => text.includes(syn)));
      if (!allMatch) return false;
    }

    // Location filter: exclude regions incompatible with Poland search
    if (isPolandSearch(filters.location)) {
      const offerLoc = offer.location.toLowerCase();
      if (EXCLUDED_REGIONS.some((r) => offerLoc.includes(r))) return false;
    }

    // Junior filter: auto-reject senior/mid when user selected entry-level experience
    if (applyJuniorFilter && isSeniorOffer(offer)) return false;

    return true;
  });
}

// ── Parse & deduplicate ───────────────────────────────────────────────────────
function parseOffers(raw: string): JobOffer[] {
  let text = raw.trim();
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) text = fence[1].trim();
  const block = text.match(/\{[\s\S]*\}/);
  if (block) text = block[0];
  try {
    const p = JSON.parse(text);
    return Array.isArray(p.oferty) ? p.oferty : [];
  } catch { return []; }
}

function dedup(offers: JobOffer[]): JobOffer[] {
  const seen = new Map<string, JobOffer>();
  for (const o of offers) {
    const key = computeOfferId(o);
    if (seen.has(key)) {
      const existing = seen.get(key)!;
      existing.sources = [...new Set([...existing.sources, ...o.sources])];
    } else {
      seen.set(key, { ...o, id: key, sources: o.sources ?? [] });
    }
  }
  return Array.from(seen.values()).map((o) => ({
    ...o,
    competition_level: o.competition_level ?? calcCompetition(o),
    application_status: o.application_status ?? null,
  }));
}

async function geminiSearch(prompt: string): Promise<JobOffer[]> {
  const rl = checkRateLimit();
  if (!rl.ok) return [];
  const text = await callGeminiWithFallback(prompt, { tools: [{ googleSearch: {} }] });
  return parseOffers(text);
}

// ── Handlers per mode ─────────────────────────────────────────────────────────
async function searchPortals(filters: JobSearchFilters): Promise<JobOffer[]> {
  const results = await Promise.allSettled(
    PORTAL_GROUPS.map((g) => geminiSearch(buildPortalPrompt(filters, g.name, g.portals)))
  );
  return results.flatMap((r) => r.status === "fulfilled" ? r.value : []);
}

async function searchHidden(filters: JobSearchFilters): Promise<JobOffer[]> {
  const queries = HIDDEN_QUERIES(buildSearchQuery(filters), filters.location);
  const results = await Promise.allSettled(queries.map((q) => geminiSearch(buildHiddenPrompt(filters, q))));
  return results.flatMap((r) => r.status === "fulfilled" ? r.value : []);
}

async function searchRemote(filters: JobSearchFilters): Promise<JobOffer[]> {
  return geminiSearch(buildRemotePrompt(filters));
}

// ── Dedicated portal searches (site: operator) ───────────────────────────────
const DEDICATED_PORTALS = [
  // IT — Polska
  "justjoin.it",
  "nofluffjobs.com",
  "rocketjobs.pl",
  "theprotocol.it",
  "bulldogjob.pl",
  "solid.jobs",
  "inhire.io",
  "bigbrain.pl",
  // Ogólne — Polska
  "pracuj.pl",
  "indeed.com/pl",
  "olx.pl/praca",
  "praca.pl",
  "kariera.pl",
  "goldenline.pl",
  "gratka.pl/praca",
  "bee.pl/praca",
  "jooble.org/pl",
];

function buildSitePrompt(filters: JobSearchFilters, portal: string): string {
  const sq = buildSearchQuery(filters);
  return `Szukaj ofert pracy bezpośrednio na portalu ${portal} dla: ${sq}.

Użyj Google Search z zapytaniem: site:${portal} ${sq}${filters.location ? ` "${filters.location}"` : ""}

Filtry:
${buildFilters(filters)}
${buildExperience(filters)}${buildKeywordsInstruction(filters)}
Zwracaj TYLKO oferty dodane w ciągu ostatnich 30 dni. Ignoruj starsze ogłoszenia.
Cel: 20-25 konkretnych ofert.

Zasady dla pola "url":
✅ Znalazłeś bezpośredni link do ogłoszenia → podaj ten link.
❌ Nie znalazłeś żadnych ofert → zwróć {"oferty":[]}.
❓ Link niepewny lub prowadzi do listy, nie ogłoszenia → podaj URL wyszukiwania na portalu zawierający frazę stanowiska (np. https://${portal}/szukaj?q=${encodeURIComponent(filters.position ?? "")}).
${LINK_INSTRUCTION}
Zwróć WYŁĄCZNIE JSON:
{"oferty":[{"title":"...","company":"...","location":"...","work_mode":"zdalna|hybrydowa|stacjonarna","salary":"...lub null","contract_type":"B2B|UoP|Zlecenie|null","published_at":"...","url":"...","sources":["${portal}"],"description":"...","is_hidden":false,"is_remote_foreign":false,"eu_friendly":false}]}`;
}

async function searchDedicatedPortals(filters: JobSearchFilters): Promise<JobOffer[]> {
  const results = await Promise.allSettled(
    DEDICATED_PORTALS.map((portal) => geminiSearch(buildSitePrompt(filters, portal)))
  );
  return results.flatMap((r) => (r.status === "fulfilled" ? r.value : []));
}

// ── Route handler ─────────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  if (!process.env.GEMINI_API_KEY_1) {
    return NextResponse.json({ error: "Brak GEMINI_API_KEY_1" }, { status: 500 });
  }

  let body: { filters: JobSearchFilters; mode: SearchMode };
  try { body = await req.json(); } catch {
    return NextResponse.json({ error: "Nieprawidłowy JSON" }, { status: 400 });
  }

  const { filters = {}, mode = "portals" } = body;

  let raw: JobOffer[];
  try {
    if (mode === "portals") {
      const [portals, dedicated, remotive, jobicy] = await Promise.allSettled([
        searchPortals(filters),
        searchDedicatedPortals(filters),
        fetchRemotive(filters),
        fetchJobicy(filters),
      ]);
      raw = [
        ...(portals.status   === "fulfilled" ? portals.value   : []),
        ...(dedicated.status === "fulfilled" ? dedicated.value : []),
        ...(remotive.status  === "fulfilled" ? remotive.value  : []),
        ...(jobicy.status    === "fulfilled" ? jobicy.value    : []),
      ];
    } else if (mode === "hidden") raw = await searchHidden(filters);
    else raw = await searchRemote(filters);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Błąd";
    return NextResponse.json({ error: `Gemini API: ${msg}` }, { status: 502 });
  }

  if (raw.length === 0) {
    return NextResponse.json({ error: "Żadne źródło nie zwróciło wyników. Spróbuj ponownie lub zmień filtry." }, { status: 502 });
  }

  // Filtrowanie po lokalizacji i stanowisku przed deduplikacją
  const filtered = filterOffers(raw, filters);

  // Deduplikacja — wyniki z Gemini web search (link_verified: null przed sprawdzeniem)
  const deduplicated = dedup(filtered)
    .filter((o) => hoursAgo(o.published_at) < 720)
    .map((o) => ({ ...o, link_verified: null as boolean | null }));

  // Weryfikacja linków tylko dla ofert z Gemini (nie dla przyszłych źródeł API jak JustJoinIT)
  const oferty = await verifyLinks(deduplicated);

  return NextResponse.json({ oferty, total: oferty.length });
}
