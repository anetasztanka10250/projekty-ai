"use client";
import { useState, useEffect } from "react";
import JobOfferCard from "./JobOfferCard";
import type { JobOffer, JobSearchFilters, Application, GeneratedCv, SearchMode } from "@/lib/types";
import { computeOfferId } from "@/lib/types";
import { calcCompetition } from "@/lib/competition";

const HIDDEN_LS_KEY = "cvskan_hidden_offers";

function offerKey(offer: JobOffer): string {
  return offer.id || computeOfferId(offer);
}

interface Props {
  filters: JobSearchFilters;
  applications: Application[];
  onApply: (app: Application) => void;
  onSaveCv: (cv: GeneratedCv) => void;
  favorites: JobOffer[];
  onToggleFavorite: (offer: JobOffer) => void;
}

const MODES: { id: SearchMode; label: string; portals: number; desc: string }[] = [
  { id: "portals", label: "📋 Portale pracy", portals: 16, desc: "JustJoin IT + 15 portali ogólnych i IT" },
  { id: "hidden", label: "🔍 Ukryte oferty", portals: 5, desc: "Bezpośrednio na stronach karier firm — niedostępne na portalach" },
  { id: "remote", label: "🌍 Zagraniczne remote", portals: 8, desc: "Remote.co, WeWorkRemotely, Himalayas i inne — otwarcie dla EU" },
];

function enrich(offers: JobOffer[]): JobOffer[] {
  return offers.map((o) => ({
    ...o,
    id: computeOfferId(o),
    sources: o.sources?.length ? o.sources : [o.source as string ?? "nieznany"],
    is_hidden: o.is_hidden ?? false,
    is_remote_foreign: o.is_remote_foreign ?? false,
    eu_friendly: o.eu_friendly ?? false,
    application_status: o.application_status ?? null,
    competition_level:
      o.competition_level ?? calcCompetition({ title: o.title, published_at: o.published_at, sources: o.sources ?? [] }),
  }));
}

export default function JobSearchSection({ filters, applications, onApply, onSaveCv, favorites, onToggleFavorite }: Props) {
  const [mode, setMode] = useState<SearchMode>("portals");
  const [offers, setOffers] = useState<JobOffer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [progress, setProgress] = useState("");
  const [showExpandDialog, setShowExpandDialog] = useState(false);
  const [isBroadened, setIsBroadened] = useState(false);
  const [hiddenKeys, setHiddenKeys] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set();
    try {
      const raw = localStorage.getItem(HIDDEN_LS_KEY);
      return raw ? new Set(JSON.parse(raw) as string[]) : new Set();
    } catch { return new Set(); }
  });

  useEffect(() => {
    try { localStorage.setItem(HIDDEN_LS_KEY, JSON.stringify([...hiddenKeys])); } catch {}
  }, [hiddenKeys]);

  const hideOffer = (offer: JobOffer) =>
    setHiddenKeys((prev) => new Set([...prev, offerKey(offer)]));

  const restoreAll = () => setHiddenKeys(new Set());

  const clearResults = () => { setOffers([]); setSearched(false); setShowExpandDialog(false); };

  const visibleOffers = offers.filter((o) => !hiddenKeys.has(offerKey(o)));
  const hiddenCount = offers.length - visibleOffers.length;

  const PROGRESS_MSGS: Record<SearchMode, string[]> = {
    portals: ["Odpytuję JustJoin IT API…", "Gemini przeszukuje pracuj.pl, OLX, NoFluffJobs…", "Gemini przeszukuje LinkedIn, Indeed, Glassdoor…", "Scalanie i deduplikacja wyników…"],
    hidden: ["Gemini szuka na stronach karier firm — bez portali pracy…", "Analizuję wyniki 5 zapytań równoległych…"],
    remote: ["Gemini przeszukuje Remote.co, WeWorkRemotely, Himalayas…", "Filtrowanie ofert dostępnych dla obywateli EU…"],
  };

  const search = async (overrideFilters?: Partial<JobSearchFilters>, broadened = false) => {
    setLoading(true);
    setError(null);
    setShowExpandDialog(false);
    setIsBroadened(broadened);

    const msgs = PROGRESS_MSGS[mode];
    let i = 0;
    setProgress(msgs[0]);
    const interval = setInterval(() => {
      i = (i + 1) % msgs.length;
      setProgress(msgs[i]);
    }, 4000);

    try {
      const effectiveFilters = overrideFilters ? { ...filters, ...overrideFilters } : filters;
      const res = await fetch("/api/search-jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: effectiveFilters, mode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
      const enriched = enrich(data.oferty ?? []);
      setOffers((prev) => {
        const seen = new Map<string, JobOffer>();
        for (const o of prev) seen.set(offerKey(o), o);
        for (const o of enriched) { if (!seen.has(offerKey(o))) seen.set(offerKey(o), o); }
        return Array.from(seen.values());
      });
      setSearched(true);
      if (!broadened && enriched.length < 5 && filters.position?.trim()) {
        setShowExpandDialog(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nieznany błąd");
    } finally {
      clearInterval(interval);
      setLoading(false);
      setProgress("");
    }
  };

  const searchBroadened = () => {
    const words = (filters.position ?? "").trim().split(/\s+/).filter(Boolean);
    const mainWord = words[words.length - 1] ?? filters.position ?? "";
    search({ position: mainWord }, true);
  };

  const currentMode = MODES.find((m) => m.id === mode)!;

  return (
    <div className="space-y-5">
      {/* Mode tabs */}
      <div className="bg-white border border-gray-200 rounded-2xl p-2 flex gap-1">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => { setMode(m.id); setSearched(false); setOffers([]); }}
            className={`flex-1 rounded-xl py-2.5 px-3 text-sm font-medium transition-colors ${
              mode === m.id
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-gray-600 hover:bg-gray-50"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Mode description + search button */}
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-gray-500">{currentMode.desc}</p>
        <button
          onClick={() => search()}
          disabled={loading}
          className="shrink-0 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-colors flex items-center gap-2"
        >
          {loading ? (
            <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Szukam…</>
          ) : (
            `🔍 Szukaj (${currentMode.portals} portali)`
          )}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          <strong>Błąd:</strong> {error}
        </div>
      )}

      {showExpandDialog && !loading && (
        <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4">
          <p className="text-sm font-medium text-amber-900 mb-3">
            Znaleziono mało ofert dla „{filters.position}". Czy chcesz rozszerzyć wyszukiwanie?
          </p>
          <div className="flex gap-2">
            <button
              onClick={searchBroadened}
              className="bg-amber-600 hover:bg-amber-700 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              Tak, pokaż więcej
            </button>
            <button
              onClick={() => setShowExpandDialog(false)}
              className="bg-white border border-amber-300 hover:bg-amber-50 text-amber-800 text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              Nie, zostaw filtry
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="bg-white border border-gray-200 rounded-2xl p-10 text-center space-y-4">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto" />
          <div>
            <p className="font-medium text-gray-800">{progress}</p>
            <p className="text-xs text-gray-400 mt-1">Równoległe zapytania do Gemini — może potrwać do 60 sekund</p>
          </div>
        </div>
      )}

      {/* Results */}
      {searched && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-800">
                Znaleziono <span className="text-indigo-600">{visibleOffers.length}</span> ofert
                {hiddenCount > 0 && (
                  <span className="text-gray-400 font-normal"> (+ {hiddenCount} ukryte przez Ciebie)</span>
                )}
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">łącznie z poprzednich wyszukiwań</p>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => search()} disabled={loading} className="text-sm text-indigo-600 hover:text-indigo-800 disabled:text-indigo-300 transition-colors">
                Szukaj ponownie →
              </button>
              <button onClick={clearResults} className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
                Wyczyść
              </button>
            </div>
          </div>

          {visibleOffers.length === 0 && !loading ? (
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-12 text-center text-gray-500">
              {hiddenCount > 0
                ? `Wszystkie oferty są ukryte. `
                : "Nie znaleziono ofert. Spróbuj zmienić stanowisko lub poluzować filtry."}
              {hiddenCount > 0 && (
                <button onClick={restoreAll} className="underline text-indigo-600 hover:text-indigo-800">
                  Przywróć {hiddenCount} ukrytych
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="grid sm:grid-cols-2 gap-4">
                {visibleOffers.map((offer) => (
                  <JobOfferCard
                    key={offer.id}
                    offer={offer}
                    applications={applications}
                    onApply={onApply}
                    isFavorited={favorites.some((f) => computeOfferId(f) === computeOfferId(offer))}
                    onToggleFavorite={() => onToggleFavorite(offer)}
                    onHide={() => hideOffer(offer)}
                  />
                ))}
              </div>
              {hiddenCount > 0 && (
                <div className="text-center text-sm text-gray-400 pt-2">
                  🙈 Ukryto {hiddenCount} ofert (przez Ciebie) ·{" "}
                  <button onClick={restoreAll} className="underline hover:text-gray-600 transition-colors">
                    Przywróć wszystkie
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Empty state */}
      {!searched && !loading && (
        <div className="bg-white border border-dashed border-gray-300 rounded-2xl p-16 text-center">
          <p className="text-4xl mb-4">🔍</p>
          <p className="font-semibold text-gray-700 mb-1">Gotowy do wyszukiwania</p>
          <p className="text-sm text-gray-400">Ustaw filtry lub wpisz stanowisko / słowa kluczowe i kliknij "Szukaj"</p>
        </div>
      )}
    </div>
  );
}
