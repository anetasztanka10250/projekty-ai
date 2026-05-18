"use client";
import type { JobSearchFilters } from "@/lib/types";

interface Props {
  filters: JobSearchFilters;
  onChange: (f: JobSearchFilters) => void;
}

const WORK_MODES = ["Zdalna", "Hybrydowa", "Stacjonarna"];
const CONTRACT_TYPES = ["B2B", "UoP", "Zlecenie"];
const EXPERIENCE_LEVELS = [
  { label: "Bez doświadczenia", value: "0" },
  { label: "0–1 rok", value: "0-1" },
  { label: "1–2 lata", value: "1-2" },
  { label: "2–3 lata", value: "2-3" },
  { label: "3–5 lat", value: "3-5" },
  { label: "5+ lat", value: "5+" },
];
const TIME_OPTIONS: { label: string; value: NonNullable<JobSearchFilters["timeAdded"]> }[] = [
  { label: "1h", value: "1h" },
  { label: "12h", value: "12h" },
  { label: "24h", value: "24h" },
  { label: "3 dni", value: "3d" },
  { label: "Tydzień", value: "7d" },
  { label: "Dowolny", value: "any" },
];

function Toggle({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
        active
          ? "bg-indigo-600 border-indigo-600 text-white"
          : "border-gray-200 text-gray-600 hover:border-indigo-300"
      }`}
    >
      {children}
    </button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</p>
      {children}
    </div>
  );
}

export default function FilterPanel({ filters, onChange }: Props) {
  const set = (patch: Partial<JobSearchFilters>) => onChange({ ...filters, ...patch });

  const toggleArr = (key: "workMode" | "contractType", val: string) => {
    const arr = filters[key] ?? [];
    set({ [key]: arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val] });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 space-y-5 sticky top-20">
      <h2 className="font-semibold text-gray-800">Filtry wyszukiwania</h2>

      <Section title="Stanowisko (opcjonalne)">
        <input
          type="text"
          placeholder="np. Project Manager, Developer, UX…"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={filters.position ?? ""}
          onChange={(e) => set({ position: e.target.value })}
        />
      </Section>

      <Section title="🔑 Słowa kluczowe (opcjonalne)">
        <div className="space-y-2">
          {(
            [
              "np. React, Excel, zarządzanie",
              "np. zdalnie, Poznań, B2B",
              "np. junior, bez doświadczenia",
            ] as const
          ).map((ph, i) => (
            <input
              key={i}
              type="text"
              placeholder={ph}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={filters.keywords?.[i] ?? ""}
              onChange={(e) => {
                const next = [...(filters.keywords ?? ["", "", ""])];
                while (next.length < 3) next.push("");
                next[i] = e.target.value;
                set({ keywords: next });
              }}
            />
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-1.5">Wszystkie wpisane słowa muszą wystąpić w ofercie (AND)</p>
      </Section>

      <Section title="Lokalizacja">
        <input
          type="text"
          placeholder="np. Warszawa, cała Polska"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={filters.location ?? ""}
          onChange={(e) => set({ location: e.target.value })}
        />
      </Section>

      <Section title="Tryb pracy">
        <div className="flex flex-wrap gap-1.5">
          {WORK_MODES.map((m) => (
            <Toggle key={m} active={filters.workMode?.includes(m) ?? false} onClick={() => toggleArr("workMode", m)}>
              {m}
            </Toggle>
          ))}
        </div>
      </Section>

      <Section title="Typ umowy">
        <div className="flex flex-wrap gap-1.5">
          {CONTRACT_TYPES.map((t) => (
            <Toggle key={t} active={filters.contractType?.includes(t) ?? false} onClick={() => toggleArr("contractType", t)}>
              {t}
            </Toggle>
          ))}
        </div>
      </Section>

      <Section title="Min. wynagrodzenie (zł)">
        <input
          type="number"
          placeholder="np. 8000"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          value={filters.salaryMin ?? ""}
          onChange={(e) => set({ salaryMin: e.target.value ? Number(e.target.value) : undefined })}
        />
      </Section>

      <Section title="Doświadczenie">
        <div className="flex flex-wrap gap-1.5">
          {EXPERIENCE_LEVELS.map((l) => (
            <Toggle
              key={l.value}
              active={filters.experienceLevels?.includes(l.value) ?? false}
              onClick={() => {
                const arr = filters.experienceLevels ?? [];
                set({
                  experienceLevels: arr.includes(l.value)
                    ? arr.filter((v) => v !== l.value)
                    : [...arr, l.value],
                });
              }}
            >
              {l.label}
            </Toggle>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-1.5">Zaznacz kilka → oferty pasujące do któregokolwiek (OR)</p>
        {(filters.experienceLevels ?? []).some((l) => ["0", "0-1", "1-2"].includes(l)) &&
          !(filters.experienceLevels ?? []).some((l) => ["3-5", "5+"].includes(l)) && (
            <p className="text-xs text-emerald-600 mt-1">
              🛡️ Auto-filtr: oferty senior/mid są ukrywane
            </p>
          )}
      </Section>

      <Section title="Czas dodania">
        <div className="flex flex-wrap gap-1.5">
          {TIME_OPTIONS.map((o) => (
            <Toggle key={o.value} active={(filters.timeAdded ?? "any") === o.value} onClick={() => set({ timeAdded: o.value })}>
              {o.label}
            </Toggle>
          ))}
        </div>
      </Section>

      <Section title="Praca zagraniczna">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            className="w-4 h-4 accent-indigo-600"
            checked={filters.remoteInternational ?? false}
            onChange={(e) => set({ remoteInternational: e.target.checked })}
          />
          <span className="text-sm text-gray-700">🌍 Remote dla Polaków (bez wizy)</span>
        </label>
      </Section>

      <button
        onClick={() =>
          onChange({ workMode: [], contractType: [], timeAdded: "any", keywords: [], experienceLevels: [] })
        }
        className="w-full text-xs text-gray-400 hover:text-gray-600 transition-colors py-1"
      >
        Wyczyść filtry
      </button>
    </div>
  );
}
