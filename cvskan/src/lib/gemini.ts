import { GoogleGenerativeAI } from "@google/generative-ai";

const geminiKeys = [
  process.env.GEMINI_API_KEY_1,
  process.env.GEMINI_API_KEY_2,
  process.env.GEMINI_API_KEY_3,
].filter(Boolean) as string[];

if (geminiKeys.length === 0) {
  throw new Error("Brak żadnego klucza GEMINI_API_KEY w .env.local");
}

let currentKeyIndex = 0;

export interface GeminiCallOptions {
  model?: string;
  tools?: object[];
  apiVersion?: string;
}

export async function callGeminiWithFallback(
  prompt: string,
  options: GeminiCallOptions = {}
): Promise<string> {
  const {
    model = "gemini-2.5-flash",
    tools,
    apiVersion = "v1beta",
  } = options;

  for (let i = 0; i < geminiKeys.length; i++) {
    const key = geminiKeys[currentKeyIndex % geminiKeys.length];
    try {
      const client = new GoogleGenerativeAI(key);
      const modelParams: Record<string, unknown> = { model };
      if (tools?.length) modelParams.tools = tools;

      const genModel = client.getGenerativeModel(
        modelParams as Parameters<GoogleGenerativeAI["getGenerativeModel"]>[0],
        { apiVersion }
      );

      const result = await genModel.generateContent(prompt);
      return result.response.text();
    } catch (err) {
      const status = (err as { status?: number }).status;
      const message = err instanceof Error ? err.message : String(err);

      if (status === 429 || message.includes("429") || message.toLowerCase().includes("quota")) {
        currentKeyIndex++;
        continue;
      }

      throw err;
    }
  }

  throw new Error("Wszystkie klucze wyczerpane — wróć jutro");
}
