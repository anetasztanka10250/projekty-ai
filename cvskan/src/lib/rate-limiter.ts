const timestamps: number[] = [];
const MAX = 10;
const WINDOW = 60_000;

export function checkRateLimit(): { ok: boolean; retryAfterMs: number } {
  const now = Date.now();
  while (timestamps.length && timestamps[0] < now - WINDOW) timestamps.shift();
  if (timestamps.length >= MAX) {
    return { ok: false, retryAfterMs: WINDOW - (now - timestamps[0]) };
  }
  timestamps.push(now);
  return { ok: true, retryAfterMs: 0 };
}
