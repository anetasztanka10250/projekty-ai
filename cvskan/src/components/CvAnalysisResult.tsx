"use client";
import { useState } from "react";
import type { CvAnalysis, GeneratedCv } from "@/lib/types";

interface Props {
  analysis: CvAnalysis;
  onReset: () => void;
  onGoToSearch: () => void;
  onSaveCv: (cv: GeneratedCv) => void;
  jobDescription?: string;
}

function ScoreRing({ score }: { score: number }) {
  const color = score >= 75 ? "text-green-600" : score >= 50 ? "text-yellow-600" : "text-red-600";
  const stroke = score >= 75 ? "stroke-green-500" : score >= 50 ? "stroke-yellow-500" : "stroke-red-500";
  const c = 2 * Math.PI * 40;
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-28 h-28">
        <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="#e5e7eb" strokeWidth="10" />
          <circle cx="50" cy="50" r="40" fill="none" className={stroke} strokeWidth="10"
            strokeDasharray={c} strokeDashoffset={c - (score / 100) * c}
            strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-2xl font-bold ${color}`}>{score}%</span>
          <span className="text-xs text-gray-400">ATS</span>
        </div>
      </div>
      <p className={`text-sm font-semibold ${color}`}>
        {score >= 75 ? "Świetne CV!" : score >= 50 ? "Wymaga poprawek" : "Gruntowna edycja"}
      </p>
    </div>
  );
}

function Tags({ items, bg }: { items: string[]; bg: string }) {
  if (!items?.length) return <p className="text-xs text-gray-400 italic">Brak danych</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((i) => <span key={i} className={`text-xs font-medium px-2.5 py-1 rounded-full ${bg}`}>{i}</span>)}
    </div>
  );
}

function Bullets({ items }: { items: string[] }) {
  if (!items?.length) return <p className="text-xs text-gray-400 italic">Brak danych</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2 text-sm text-gray-700">
          <span className="mt-0.5 shrink-0 text-indigo-400">•</span><span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function CvAnalysisResult({ analysis, onReset, onGoToSearch, onSaveCv, jobDescription }: Props) {
  const [generating, setGenerating] = useState(false);
  const [generatedText, setGeneratedText] = useState<string | null>(null);
  const [genType, setGenType] = useState<"universal" | "targeted">("universal");
  const [genError, setGenError] = useState<string | null>(null);

  const generateCv = async (type: "universal" | "targeted") => {
    setGenerating(true);
    setGenType(type);
    setGenError(null);
    try {
      const res = await fetch("/api/generate-cv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ analysis, jobDescription: type === "targeted" ? jobDescription : undefined }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
      setGeneratedText(data.cv);
      const cv: GeneratedCv = {
        id: Date.now().toString(),
        type,
        targetOffer: type === "targeted" ? jobDescription?.slice(0, 100) : undefined,
        content: data.cv,
        createdAt: new Date().toISOString(),
      };
      onSaveCv(cv);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : "Błąd generowania");
    } finally {
      setGenerating(false);
    }
  };

  const exportTxt = () => {
    if (!generatedText) return;
    const blob = new Blob([generatedText], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cv_zoptymalizowane.txt";
    a.click();
  };

  const printCv = () => {
    if (!generatedText) return;
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<html><head><title>CV</title><style>body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.6;white-space:pre-wrap}</style></head><body>${generatedText.replace(/</g, "&lt;")}</body></html>`);
    win.document.close();
    win.print();
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      {/* Score + summary */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 flex flex-col sm:flex-row gap-6 items-center">
        <ScoreRing score={analysis.score} />
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-2">Podsumowanie</h3>
          <p className="text-sm text-gray-600 leading-relaxed">{analysis.podsumowanie}</p>
        </div>
      </div>

      {/* Keywords */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm">✅ Pasujące słowa kluczowe</h4>
          <Tags items={analysis.pasujace_slowa} bg="bg-green-50 text-green-700" />
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm">❌ Brakujące słowa kluczowe</h4>
          <Tags items={analysis.brakujace_slowa} bg="bg-red-50 text-red-700" />
        </div>
      </div>

      {/* Strengths + improvements */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm">💪 Mocne strony</h4>
          <Bullets items={analysis.mocne_strony} />
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm">🔧 Do poprawy</h4>
          <Bullets items={analysis.do_poprawy} />
        </div>
      </div>

      {/* ATS tips */}
      <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5">
        <h4 className="font-semibold text-indigo-900 mb-3 text-sm">🎯 Sugestie ATS</h4>
        <Bullets items={analysis.sugestie_ats} />
      </div>

      {/* Gap analysis */}
      {analysis.gap_analysis && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 space-y-4">
          <h4 className="font-semibold text-amber-900 text-sm">📊 Gap Analysis — dopasowanie do oferty</h4>
          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <p className="text-xs font-semibold text-green-700 mb-2">✅ Pasuje</p>
              <Bullets items={analysis.gap_analysis.pasuje} />
            </div>
            <div>
              <p className="text-xs font-semibold text-red-700 mb-2">❌ Braki</p>
              <Bullets items={analysis.gap_analysis.braki} />
            </div>
            <div>
              <p className="text-xs font-semibold text-indigo-700 mb-2">💡 Rekomendacje</p>
              <Bullets items={analysis.gap_analysis.rekomendacje} />
            </div>
          </div>
        </div>
      )}

      {/* Generate CV */}
      <div className="bg-white border border-gray-200 rounded-2xl p-5">
        <h4 className="font-semibold text-gray-800 mb-1 text-sm">🤖 Generowanie zoptymalizowanego CV</h4>
        <p className="text-xs text-gray-400 mb-4">AI przepisuje CV z lepszą strukturą i słowami kluczowymi dla ATS</p>
        {genError && <p className="text-sm text-red-600 mb-3">{genError}</p>}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => generateCv("universal")}
            disabled={generating}
            className="flex-1 border border-indigo-200 hover:bg-indigo-50 text-indigo-700 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-50"
          >
            {generating && genType === "universal" ? "Generuję…" : "Universalne CV (ATS)"}
          </button>
          {jobDescription && (
            <button
              onClick={() => generateCv("targeted")}
              disabled={generating}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors disabled:opacity-50"
            >
              {generating && genType === "targeted" ? "Generuję…" : "CV pod tę ofertę"}
            </button>
          )}
        </div>

        {generatedText && (
          <div className="mt-4 space-y-3">
            <pre className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs text-gray-700 whitespace-pre-wrap max-h-60 overflow-y-auto font-mono">
              {generatedText}
            </pre>
            <div className="flex gap-2">
              <button onClick={exportTxt} className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium py-2 rounded-lg transition-colors">
                ⬇ Pobierz TXT
              </button>
              <button onClick={printCv} className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium py-2 rounded-lg transition-colors">
                🖨 Drukuj / PDF
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button onClick={onReset} className="flex-1 border border-gray-200 hover:border-gray-300 text-gray-700 font-medium py-3 rounded-xl text-sm transition-colors">
          ← Wgraj inne CV
        </button>
        <button onClick={onGoToSearch} className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl text-sm transition-colors">
          🔍 Szukaj pasujących ofert →
        </button>
      </div>
    </div>
  );
}
