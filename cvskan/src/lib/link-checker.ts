const TIMEOUT_MS = 5000;
const CONCURRENCY = 10;

async function checkLink(url: string): Promise<boolean> {
  if (!url?.startsWith("http")) return false;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "HEAD",
      signal: controller.signal,
      redirect: "follow",
      headers: { "User-Agent": "Mozilla/5.0 (compatible; CVSkan link checker)" },
    });
    return res.ok || res.status === 405; // 405 = HEAD not allowed ale URL istnieje
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function verifyLinks<T extends { url: string; link_verified: boolean | null }>(
  offers: T[]
): Promise<T[]> {
  const results = [...offers];

  // Przetwarzaj w paczkach CONCURRENCY jednocześnie
  for (let i = 0; i < results.length; i += CONCURRENCY) {
    const batch = results.slice(i, i + CONCURRENCY);
    const checks = await Promise.allSettled(
      batch.map((o) => checkLink(o.url))
    );
    checks.forEach((result, j) => {
      results[i + j].link_verified =
        result.status === "fulfilled" ? result.value : false;
    });
  }

  return results;
}
