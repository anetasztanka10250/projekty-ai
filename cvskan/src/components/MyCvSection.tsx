"use client";
import type { GeneratedCv } from "@/lib/types";

interface Props {
  cvs: GeneratedCv[];
}

export default function MyCvSection({ cvs }: Props) {
  const exportTxt = (cv: GeneratedCv) => {
    const blob = new Blob([cv.content], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `cv_${cv.type}_${cv.id}.txt`;
    a.click();
  };

  const printCv = (cv: GeneratedCv) => {
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(`<html><head><title>CV</title><style>body{font-family:sans-serif;max-width:800px;margin:40px auto;line-height:1.7;white-space:pre-wrap;font-size:14px}</style></head><body>${cv.content.replace(/</g, "&lt;")}</body></html>`);
    win.document.close();
    win.print();
  };

  if (cvs.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24">
        <p className="text-5xl mb-4">⭐</p>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Brak wygenerowanych CV</h2>
        <p className="text-gray-500">Przejdź do zakładki "Analiza CV", wgraj swoje CV i wygeneruj wersję zoptymalizowaną pod ATS.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5">
      <h2 className="text-2xl font-bold text-gray-900">Moje CV ({cvs.length})</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        {cvs.map((cv) => (
          <div key={cv.id} className="bg-white border border-gray-200 rounded-2xl p-5 space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cv.type === "universal" ? "bg-indigo-100 text-indigo-700" : "bg-amber-100 text-amber-700"}`}>
                  {cv.type === "universal" ? "Universalne ATS" : "Pod ofertę"}
                </span>
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(cv.createdAt).toLocaleString("pl-PL")}
                </p>
                {cv.targetOffer && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">🎯 {cv.targetOffer}…</p>
                )}
              </div>
            </div>
            <pre className="bg-gray-50 rounded-xl p-3 text-xs text-gray-600 whitespace-pre-wrap max-h-36 overflow-y-auto font-mono">
              {cv.content}
            </pre>
            <div className="flex gap-2">
              <button onClick={() => exportTxt(cv)}
                className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-medium py-2 rounded-lg transition-colors">
                ⬇ TXT
              </button>
              <button onClick={() => printCv(cv)}
                className="flex-1 border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-medium py-2 rounded-lg transition-colors">
                🖨 PDF
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
