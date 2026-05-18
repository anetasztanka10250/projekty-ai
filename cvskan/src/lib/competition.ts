import type { JobOffer } from "./types";

export function hoursAgo(published: string | null): number {
  if (!published) return 72;
  const s = published.toLowerCase();

  const isoMatch = s.match(/^(\d{4}-\d{2}-\d{2})/);
  if (isoMatch) {
    const d = new Date(isoMatch[1]);
    if (!isNaN(d.getTime())) return (Date.now() - d.getTime()) / 3_600_000;
  }

  const n = parseInt(s.match(/\d+/)?.[0] ?? "0");
  if (s.includes("minut") || s.includes("min")) return 0;
  if (s.includes("godzin") || s.includes("hour") || s.includes("godz")) return n;
  if (s.includes("dzień") || s.includes("day") || s.includes("dni")) return n * 24;
  if (s.includes("tydz") || s.includes("week")) return n * 168;
  return 72;
}

export function calcCompetition(
  offer: Pick<JobOffer, "title" | "published_at" | "sources">
): "niska" | "srednia" | "wysoka" {
  const hours = hoursAgo(offer.published_at);
  const isSenior = /senior|lead|principal|head|expert|architect/i.test(offer.title);
  const multiPortal = (offer.sources?.length ?? 1) > 2;

  if (hours < 12 && !multiPortal) return "niska";
  if (hours < 48 && !isSenior) return "niska";
  if (hours > 120 || (hours > 72 && isSenior) || multiPortal) return "wysoka";
  return "srednia";
}
