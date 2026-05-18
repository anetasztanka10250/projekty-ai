"use client";
import { useState } from "react";
import type { JobOffer, Application } from "@/lib/types";
import { hoursAgo } from "@/lib/competition";

interface Props {
  offer: JobOffer;
  applications: Application[];
  onApply: (app: Application) => void;
  isFavorited?: boolean;
  onToggleFavorite?: () => void;
  onHide?: () => void;
}

const COMPETITION_CFG = {
  niska:   { label: "Niska",   bg: "bg-green-100 text-green-700" },
  srednia: { label: "Średnia", bg: "bg-yellow-100 text-yellow-700" },
  wysoka:  { label: "Wysoka",  bg: "bg-red-100 text-red-700" },
};

const SOURCE_COLOR: Record<string, string> = {
  "justjoin.it":     "bg-emerald-100 text-emerald-700",
  "pracuj.pl":       "bg-blue-100 text-blue-700",
  "nofluffjobs.com": "bg-orange-100 text-orange-700",
  "linkedin":        "bg-sky-100 text-sky-700",
  "rocketjobs.pl":   "bg-purple-100 text-purple-700",
  "theprotocol.it":  "bg-teal-100 text-teal-700",
  "bulldogjob.pl":   "bg-indigo-100 text-indigo-700",
};

function isValidUrl(url: string | null | undefined): boolean {
  return !!url && url.startsWith("http");
}

function googleSearchUrl(title: string, company: string): string {
  return `https://www.google.com/search?q=${encodeURIComponent(`${title} ${company} oferta pracy`)}`;
}

export default function JobOfferCard({ offer, applications, onApply, isFavorited = false, onToggleFavorite, onHide }: Props) {
  const [step, setStep] = useState<"idle" | "opened" | "confirming">("idle");
  const [applied, setApplied] = useState(false);
  const [portal, setPortal] = useState("");
  const [customPortal, setCustomPortal] = useState("");
  const [applyDate, setApplyDate] = useState("");
  const [note, setNote] = useState("");

  const existingApp = applications.find(
    (a) => a.offer_title === offer.title && a.company === offer.company
  );
  const hasApplied = applied || !!existingApp;
  const appliedDate = existingApp?.applied_at ?? new Date().toLocaleDateString("pl-PL");

  const isStale = hoursAgo(offer.published_at) >= 504;
  const competition = COMPETITION_CFG[offer.competition_level] ?? COMPETITION_CFG.srednia;
  const sourceColor = SOURCE_COLOR[offer.sources?.[0]] ?? "bg-gray-100 text-gray-600";
  const hasUrl = isValidUrl(offer.url);
  const linkBroken = hasUrl && offer.link_verified === false;
  const linkVerified = hasUrl && offer.link_verified === true;
  const canApply = hasUrl && !linkBroken;

  const handleApplyClick = () => {
    window.open(offer.url, "_blank", "noopener,noreferrer");
    setStep("opened");
  };

  const handleConfirmClick = () => {
    setPortal(offer.sources?.[0] ?? "");
    setCustomPortal("");
    setApplyDate(new Date().toLocaleDateString("pl-PL"));
    setNote("");
    setStep("confirming");
  };

  const handleSave = () => {
    const chosenPortal = portal === "inne" ? customPortal.trim() || "inne" : portal;
    const app: Application = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      offer_title: offer.title,
      company: offer.company,
      portal: chosenPortal,
      applied_at: applyDate,
      status: "wysłano",
      note,
      url: offer.url,
    };
    onApply(app);
    setApplied(true);
    setStep("idle");
  };

  const handleCancel = () => {
    setStep("idle");
  };

  return (
    <div
      className={`relative bg-white border rounded-2xl p-5 transition-all hover:shadow-sm ${
        offer.is_hidden
          ? "border-amber-200"
          : offer.is_remote_foreign
          ? "border-blue-200"
          : "border-gray-200"
      }`}
    >
      {onHide && (
        <button
          onClick={onHide}
          title="Nie pokazuj więcej"
          className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center text-gray-300 hover:text-gray-500 hover:bg-gray-100 rounded-full text-xs transition-colors z-10"
        >
          ✕
        </button>
      )}
      {/* Badges */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            {offer.is_hidden && (
              <span className="text-xs bg-amber-100 text-amber-700 font-medium px-2 py-0.5 rounded-full">
                🔍 Ukryta oferta
              </span>
            )}
            {offer.is_remote_foreign && (
              <span className="text-xs bg-blue-100 text-blue-700 font-medium px-2 py-0.5 rounded-full">
                {offer.eu_friendly ? "🇪🇺 Firma UE" : "🌍 Worldwide B2B"}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900 text-sm leading-tight">{offer.title}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{offer.company}</p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${sourceColor}`}>
            {offer.sources?.[0] ?? "portal"}
          </span>
          {onToggleFavorite && (
            <button
              onClick={onToggleFavorite}
              title={isFavorited ? "Usuń z ulubionych" : "Dodaj do ulubionych"}
              className="text-lg leading-none transition-transform hover:scale-110 active:scale-95"
            >
              {isFavorited ? "❤️" : "🤍"}
            </button>
          )}
        </div>
      </div>

      {/* Meta */}
      <div className="flex flex-wrap gap-2 mb-3 text-xs">
        {offer.work_mode && (
          <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{offer.work_mode}</span>
        )}
        {offer.location && (
          <span className="text-gray-400 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            </svg>
            {offer.location}
          </span>
        )}
        {offer.contract_type && <span className="text-gray-400">{offer.contract_type}</span>}
      </div>

      {offer.salary && (
        <p className="text-sm font-semibold text-indigo-600 mb-2">{offer.salary}</p>
      )}

      {offer.description && (
        <p className="text-xs text-gray-500 leading-relaxed mb-3 line-clamp-2">{offer.description}</p>
      )}

      {offer.sources?.length > 1 && (
        <p className="text-xs text-gray-400 mb-2">
          Dostępna też na: {offer.sources.slice(1).join(", ")}
        </p>
      )}

      {/* Status linku */}
      {linkVerified && (
        <p className="text-xs text-green-600 mb-2">✅ Link zweryfikowany</p>
      )}
      {(linkBroken || !hasUrl) && (
        <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
          {linkBroken ? "⚠️ Link nie działa — " : "⚠️ Brak linku — "}
          <a
            href={googleSearchUrl(offer.title, offer.company)}
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-medium hover:text-amber-800"
          >
            🔍 Znajdź ofertę ręcznie
          </a>
        </div>
      )}

      {/* Ostrzeżenie o starości */}
      {isStale && (
        <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 mb-3">
          ⚠️ Oferta może być nieaktualna (21+ dni)
        </div>
      )}

      {/* Przycisk potwierdzenia wysłania (krok 2) */}
      {step === "opened" && !hasApplied && (
        <button
          onClick={handleConfirmClick}
          className="w-full mb-3 text-xs bg-green-50 hover:bg-green-100 border border-green-200 text-green-700 font-medium px-3 py-2 rounded-lg transition-colors"
        >
          ✅ Potwierdzam że wysłałam aplikację
        </button>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {offer.published_at && (
            <span className="text-xs text-gray-400 shrink-0">{offer.published_at}</span>
          )}
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${competition.bg}`}>
            ⚡ {competition.label}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {hasApplied ? (
            <span className="text-xs text-green-600 font-medium">
              ✅ Aplikowano · {appliedDate}
            </span>
          ) : canApply ? (
            <button
              onClick={handleApplyClick}
              className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-3 py-1.5 rounded-lg transition-colors"
            >
              Aplikuj
            </button>
          ) : (
            <a
              href={googleSearchUrl(offer.title, offer.company)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-amber-600 hover:text-amber-800 font-medium transition-colors"
            >
              🔍 Szukaj ręcznie
            </a>
          )}

          {canApply && !hasApplied && (
            <a
              href={offer.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              ↗
            </a>
          )}
        </div>
      </div>

      {/* Modal — krok 3: formularz aplikacji */}
      {step === "confirming" && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-xl">
            <p className="text-sm font-semibold text-gray-900 mb-0.5">Zapisz aplikację</p>
            <p className="text-xs text-gray-400 mb-5 line-clamp-1">
              {offer.title} · {offer.company}
            </p>

            <div className="space-y-4">
              {/* Portal */}
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Przez który portal?</label>
                <select
                  value={portal}
                  onChange={(e) => setPortal(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {offer.sources?.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                  <option value="inne">Inne (wpisz)</option>
                </select>
                {portal === "inne" && (
                  <input
                    autoFocus
                    value={customPortal}
                    onChange={(e) => setCustomPortal(e.target.value)}
                    placeholder="Nazwa portalu"
                    className="mt-2 w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                )}
              </div>

              {/* Data */}
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Data wysłania</label>
                <input
                  type="text"
                  value={applyDate}
                  onChange={(e) => setApplyDate(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Notatka */}
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">Notatka (opcjonalnie)</label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Np. rekruter: Anna Kowalska, termin odpowiedzi: 2 tygodnie…"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                />
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={handleSave}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors"
              >
                Zapisz
              </button>
              <button
                onClick={handleCancel}
                className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-600 font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Anuluj
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
