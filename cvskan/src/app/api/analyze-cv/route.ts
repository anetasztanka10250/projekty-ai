import { NextRequest, NextResponse } from "next/server";
import type { CvAnalysis } from "@/lib/types";
import { checkRateLimit } from "@/lib/rate-limiter";
import { callGeminiWithFallback } from "@/lib/gemini";

export const runtime = "nodejs";
export const maxDuration = 60;

async function extractText(file: File): Promise<string> {
  const buffer = Buffer.from(await file.arrayBuffer());
  if (file.type === "application/pdf") {
    const pdfParse = (await import("pdf-parse")).default;
    return (await pdfParse(buffer)).text;
  }
  if (file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
    const mammoth = await import("mammoth");
    return (await mammoth.extractRawText({ buffer })).value;
  }
  throw new Error("Nieobsługiwany format — prześlij PDF lub DOCX");
}

async function fetchUrlContent(url: string): Promise<string> {
  return callGeminiWithFallback(
    `Pobierz i zwróć pełną treść oferty pracy z tego linku: ${url}\nZwróć tylko tekst ogłoszenia, bez komentarzy.`,
    { tools: [{ googleSearch: {} }] }
  );
}

function buildPrompt(cvText: string, jobDescription?: string): string {
  const hasJob = !!jobDescription?.trim();
  return `Jesteś ekspertem ATS i rekrutacji na polskim rynku pracy.
Odpowiedz WYŁĄCZNIE poprawnym JSON bez żadnych komentarzy ani markdown.

Przeanalizuj CV i zwróć JSON z DOKŁADNIE tymi polami:
{
  "score": liczba 0-100,
  "pasujace_slowa": ["..."],
  "brakujace_slowa": ["..."],
  "mocne_strony": ["..."],
  "do_poprawy": ["..."],
  "sugestie_ats": ["..."],
  "gap_analysis": ${hasJob ? `{
    "pasuje": ["co z CV pasuje do oferty"],
    "braki": ["czego brakuje w CV względem oferty"],
    "rekomendacje": ["jak uzupełnić braki"]
  }` : "null"},
  "podsumowanie": "2-3 zdania po polsku"
}

CV:
"""
${cvText.slice(0, 8000)}
"""${hasJob ? `

Oferta pracy:
"""
${jobDescription!.slice(0, 3000)}
"""` : ""}`;
}

export async function POST(req: NextRequest) {
  if (!process.env.GEMINI_API_KEY_1) {
    return NextResponse.json({ error: "Brak GEMINI_API_KEY_1" }, { status: 500 });
  }
  const rl = checkRateLimit();
  if (!rl.ok) {
    return NextResponse.json({ error: `Rate limit — spróbuj za ${Math.ceil(rl.retryAfterMs / 1000)}s` }, { status: 429 });
  }

  let cvText = "";
  let jobDescription = "";

  const contentType = req.headers.get("content-type") ?? "";

  if (contentType.includes("multipart/form-data")) {
    let formData: FormData;
    try { formData = await req.formData(); } catch {
      return NextResponse.json({ error: "Nieprawidłowe dane formularza" }, { status: 400 });
    }

    jobDescription = (formData.get("jobDescription") as string | null) ?? "";

    const file = formData.get("cv");
    const text = formData.get("cvText") as string | null;
    const link = formData.get("cvLink") as string | null;

    if (file instanceof File) {
      if (file.size > 10 * 1024 * 1024) return NextResponse.json({ error: "Plik za duży (max 10 MB)" }, { status: 400 });
      try { cvText = await extractText(file); } catch (err) {
        return NextResponse.json({ error: err instanceof Error ? err.message : "Błąd parsowania" }, { status: 422 });
      }
    } else if (text?.trim()) {
      cvText = text.trim();
    } else if (link?.trim()) {
      try { cvText = await fetchUrlContent(link.trim()); } catch {
        return NextResponse.json({ error: "Nie udało się pobrać treści z linku" }, { status: 422 });
      }
    } else {
      return NextResponse.json({ error: "Brak treści CV" }, { status: 400 });
    }
  } else {
    return NextResponse.json({ error: "Nieobsługiwany Content-Type" }, { status: 415 });
  }

  if (cvText.trim().length < 50) {
    return NextResponse.json({ error: "CV jest zbyt krótkie — wklej więcej treści" }, { status: 422 });
  }

  let rawText: string;
  try {
    rawText = (await callGeminiWithFallback(buildPrompt(cvText, jobDescription))).trim();
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Błąd API";
    return NextResponse.json({ error: `Gemini API: ${msg}` }, { status: 502 });
  }

  const fence = rawText.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fence) rawText = fence[1].trim();

  let analysis: CvAnalysis;
  try {
    analysis = JSON.parse(rawText);
  } catch {
    return NextResponse.json({ error: `Nie udało się odczytać odpowiedzi AI. Surowa odpowiedź: ${rawText.slice(0, 200)}` }, { status: 502 });
  }

  return NextResponse.json(analysis);
}
