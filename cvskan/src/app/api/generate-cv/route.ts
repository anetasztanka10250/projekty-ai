import { NextRequest, NextResponse } from "next/server";
import { checkRateLimit } from "@/lib/rate-limiter";
import { callGeminiWithFallback } from "@/lib/gemini";
import type { CvAnalysis } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  if (!process.env.GEMINI_API_KEY_1) {
    return NextResponse.json({ error: "Brak GEMINI_API_KEY_1" }, { status: 500 });
  }
  const rl = checkRateLimit();
  if (!rl.ok) {
    return NextResponse.json({ error: `Rate limit — spróbuj za ${Math.ceil(rl.retryAfterMs / 1000)}s` }, { status: 429 });
  }

  let body: { analysis: CvAnalysis; jobDescription?: string };
  try { body = await req.json(); } catch {
    return NextResponse.json({ error: "Nieprawidłowy JSON" }, { status: 400 });
  }

  const { analysis, jobDescription } = body;
  const isTargeted = !!jobDescription?.trim();

  const prompt = isTargeted
    ? `Jesteś ekspertem HR i ATS. Przepisz poniższe CV tak, aby było maksymalnie dopasowane do oferty pracy i przeszło przez systemy ATS.
Zachowaj wszystkie prawdziwe informacje — tylko przeformułuj i podkreśl pasujące doświadczenie.
Dodaj brakujące słowa kluczowe z oferty tam gdzie uzasadnione.

Analiza CV (użyj jako podstawę):
- Mocne strony: ${analysis.mocne_strony.join(", ")}
- Słowa kluczowe do dodania: ${analysis.brakujace_slowa.join(", ")}
- Sugestie ATS: ${analysis.sugestie_ats.join("; ")}
${analysis.gap_analysis ? `- Braki względem oferty: ${analysis.gap_analysis.braki.join(", ")}
- Rekomendacje: ${analysis.gap_analysis.rekomendacje.join("; ")}` : ""}

Oferta pracy:
"""
${jobDescription!.slice(0, 3000)}
"""

Wygeneruj kompletne, zoptymalizowane CV w języku polskim. Użyj czytelnej struktury: Dane kontaktowe, Podsumowanie zawodowe, Doświadczenie, Umiejętności, Edukacja.`
    : `Jesteś ekspertem HR i ATS. Wygeneruj uniwersalne CV zoptymalizowane pod systemy ATS.

Baza z analizy:
- Mocne strony: ${analysis.mocne_strony.join(", ")}
- Słowa kluczowe do dodania: ${analysis.brakujace_slowa.join(", ")}
- Sugestie ATS: ${analysis.sugestie_ats.join("; ")}
- Podsumowanie: ${analysis.podsumowanie}

Wygeneruj kompletne, zoptymalizowane CV w języku polskim z sekcjami: Dane kontaktowe, Podsumowanie zawodowe, Doświadczenie, Umiejętności techniczne, Edukacja.
Używaj słów kluczowych które zwiększają widoczność w ATS. Struktura musi być prosta i czytelna dla systemów ATS.`;

  let cv: string;
  try {
    cv = (await callGeminiWithFallback(prompt)).trim();
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Błąd API";
    return NextResponse.json({ error: `Gemini API: ${msg}` }, { status: 502 });
  }

  return NextResponse.json({ cv });
}
