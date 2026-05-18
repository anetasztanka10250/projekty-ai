"use client";
import { useState, useCallback } from "react";
import CvDropzone from "./CvDropzone";
import CvAnalysisResult from "./CvAnalysisResult";
import type { CvAnalysis, GeneratedCv } from "@/lib/types";

type InputMode = "file" | "text" | "link";
type Step = "input" | "analyzing" | "result";

interface Props {
  onSaveCv: (cv: GeneratedCv) => void;
  onGoToSearch: () => void;
}

export default function CvSection({ onSaveCv, onGoToSearch }: Props) {
  const [inputMode, setInputMode] = useState<InputMode>("file");
  const [step, setStep] = useState<Step>("input");
  const [cvText, setCvText] = useState("");
  const [cvLink, setCvLink] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState<CvAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState("");

  const analyze = useCallback(async (formData: FormData) => {
    setStep("analyzing");
    setError(null);
    setStatusMsg("Gemini czyta Twoje CV…");
    try {
      const res = await fetch("/api/analyze-cv", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
      setAnalysis(data);
      setStep("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nieznany błąd");
      setStep("input");
    }
  }, []);

  const handleFile = useCallback(
    (file: File) => {
      const fd = new FormData();
      fd.append("cv", file);
      if (jobDescription.trim()) fd.append("jobDescription", jobDescription.trim());
      analyze(fd);
    },
    [jobDescription, analyze]
  );

  const handleTextSubmit = async () => {
    if (cvText.trim().length < 50) {
      setError("CV jest zbyt krótkie — wklej więcej treści.");
      return;
    }
    const fd = new FormData();
    fd.append("cvText", cvText.trim());
    if (jobDescription.trim()) fd.append("jobDescription", jobDescription.trim());
    analyze(fd);
  };

  const handleLinkSubmit = async () => {
    if (!cvLink.trim()) { setError("Wklej link do oferty."); return; }
    const fd = new FormData();
    fd.append("cvLink", cvLink.trim());
    if (jobDescription.trim()) fd.append("jobDescription", jobDescription.trim());
    analyze(fd);
  };

  const reset = () => { setStep("input"); setAnalysis(null); setError(null); };

  const MODE_TABS: { id: InputMode; label: string }[] = [
    { id: "file", label: "📎 Wgraj plik" },
    { id: "text", label: "✏️ Wklej tekst" },
    { id: "link", label: "🔗 Link do oferty" },
  ];

  if (step === "result" && analysis) {
    return (
      <CvAnalysisResult
        analysis={analysis}
        onReset={reset}
        onGoToSearch={onGoToSearch}
        onSaveCv={onSaveCv}
        jobDescription={jobDescription}
      />
    );
  }

  if (step === "analyzing") {
    return (
      <div className="flex flex-col items-center justify-center py-32 gap-6">
        <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        <div className="text-center">
          <p className="font-semibold text-gray-800 text-lg">{statusMsg}</p>
          <p className="text-gray-400 text-sm mt-1">Gemini 2.5 Flash analizuje ATS — to może potrwać chwilę</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Analiza CV pod systemy ATS</h1>
        <p className="text-gray-500">Wgraj CV, wklej tekst lub podaj link — AI oceni i zaproponuje poprawki</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* Input mode tabs */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        <div className="flex border-b border-gray-100">
          {MODE_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setInputMode(tab.id)}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                inputMode === tab.id
                  ? "bg-indigo-50 text-indigo-600 border-b-2 border-indigo-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6 space-y-4">
          {inputMode === "file" && <CvDropzone onFileAccepted={handleFile} />}

          {inputMode === "text" && (
            <div className="space-y-3">
              <textarea
                rows={12}
                placeholder="Wklej tu treść swojego CV…"
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                value={cvText}
                onChange={(e) => setCvText(e.target.value)}
              />
              <button
                onClick={handleTextSubmit}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
              >
                Analizuj CV →
              </button>
            </div>
          )}

          {inputMode === "link" && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">Podaj link do oferty pracy — Gemini pobierze treść i porówna z Twoim CV.</p>
              <input
                type="url"
                placeholder="https://pracuj.pl/praca/..."
                className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={cvLink}
                onChange={(e) => setCvLink(e.target.value)}
              />
              <p className="text-xs text-gray-400">Uwaga: ta opcja analizuje ofertę pod kątem dopasowania do Twojego profilu — wgraj też CV w zakładce "Wgraj plik".</p>
              <button
                onClick={handleLinkSubmit}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
              >
                Pobierz i analizuj →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Job description */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-3">
        <label className="block text-sm font-medium text-gray-700">
          Opis oferty pracy{" "}
          <span className="text-gray-400 font-normal">(opcjonalnie — dla gap analysis)</span>
        </label>
        <textarea
          rows={5}
          placeholder="Wklej ogłoszenie o pracę na które chcesz aplikować…"
          className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
        />
      </div>
    </div>
  );
}
