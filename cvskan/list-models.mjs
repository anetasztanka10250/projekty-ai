import { readFileSync } from "fs";

const env = readFileSync(".env.local", "utf-8");
const key = env.match(/GEMINI_API_KEY_1=(.+)/)?.[1]?.trim();

if (!key) { console.error("Brak GEMINI_API_KEY_1 w .env.local"); process.exit(1); }

const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${key}`);
const data = await res.json();

if (data.error) { console.error("Błąd API:", data.error.message); process.exit(1); }

console.log("\nDostępne modele Gemini:\n");
data.models.forEach(m => console.log(" -", m.name));
console.log(`\nŁącznie: ${data.models.length} modeli`);
