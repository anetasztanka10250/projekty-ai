import type { JobOffer, JobSearchFilters } from "./types";
import { calcCompetition } from "./competition";

// ── Remotive types ────────────────────────────────────────────────────────────
interface RemotiveJob {
  id: number;
  url: string;
  title: string;
  company_name: string;
  job_type: string;
  candidate_required_location: string;
  salary: string;
  description: string;
  publication_date: string;
}

// ── Jobicy types ──────────────────────────────────────────────────────────────
interface JobicyJob {
  id: number;
  url: string;
  jobTitle: string;
  companyName: string;
  jobType: string | string[];
  jobGeo: string;
  annualSalaryMin: number | null;
  annualSalaryMax: number | null;
  salaryCurrency: string | null;
  jobDescription: string;
  pubDate: string;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function mapRemotive(job: RemotiveJob): JobOffer {
  const base = {
    id: `remotive-${job.id}`,
    title: job.title,
    company: job.company_name,
    location: job.candidate_required_location || "Remote",
    work_mode: "zdalna",
    salary: job.salary || null,
    contract_type: null,
    published_at: job.publication_date ? job.publication_date.slice(0, 10) : null,
    url: job.url,
    sources: ["remotive.com"],
    description: stripHtml(job.description).slice(0, 300),
    is_hidden: false,
    is_remote_foreign: true,
    eu_friendly: true,
    application_status: null,
    link_verified: null,
  };
  return { ...base, competition_level: calcCompetition(base) };
}

function mapJobicy(job: JobicyJob): JobOffer {
  const salary =
    job.annualSalaryMin && job.annualSalaryMax
      ? `${job.annualSalaryMin}–${job.annualSalaryMax} ${job.salaryCurrency ?? "USD"}/rok`
      : null;

  const base = {
    id: `jobicy-${job.id}`,
    title: job.jobTitle,
    company: job.companyName,
    location: job.jobGeo || "Remote",
    work_mode: "zdalna",
    salary,
    contract_type: null,
    published_at: job.pubDate ? job.pubDate.slice(0, 10) : null,
    url: job.url,
    sources: ["jobicy.com"],
    description: stripHtml(job.jobDescription).slice(0, 300),
    is_hidden: false,
    is_remote_foreign: true,
    eu_friendly: true,
    application_status: null,
    link_verified: null,
  };
  return { ...base, competition_level: calcCompetition(base) };
}

const EXCLUDED_REGIONS = [
  "latam", "latin america", "us only", "americas", "north america only",
  "usa only", "united states only", "us-only", "us residents only",
  "us citizens only", "must be in us",
];

function isLocationAllowed(locationStr: string, filters: JobSearchFilters): boolean {
  const loc = (locationStr || "").toLowerCase();
  if (EXCLUDED_REGIONS.some((r) => loc.includes(r))) return false;

  const userLoc = (filters.location || "").toLowerCase();
  const polandSearch =
    userLoc.includes("polska") || userLoc.includes("poland") || userLoc.includes("cała polska");
  if (polandSearch) {
    const COMPATIBLE = ["worldwide", "global", "europe", "europa", "poland", "polska", "eu", "remote", "anywhere", "international", ""];
    if (!COMPATIBLE.some((k) => loc === k || (k && loc.includes(k)))) return false;
  }

  return true;
}

function matchesFilters(text: string, filters: JobSearchFilters): boolean {
  const t = text.toLowerCase();

  if (filters.position?.trim()) {
    const posWords = filters.position.toLowerCase().split(/\s+/).filter(Boolean);
    if (!posWords.every((w) => t.includes(w))) return false;
  }

  const kws = (filters.keywords ?? []).map((k) => k?.trim().toLowerCase()).filter(Boolean);
  if (kws.length > 0 && !kws.every((kw) => t.includes(kw))) return false;

  return true;
}

export async function fetchRemotive(filters: JobSearchFilters): Promise<JobOffer[]> {
  try {
    const params = new URLSearchParams({ limit: "50" });
    const pos = filters.position?.trim();
    const kws = (filters.keywords ?? []).filter(Boolean);
    const searchTerm = pos || kws.join(" ");
    if (searchTerm) params.set("search", searchTerm);

    const res = await fetch(`https://remotive.com/api/remote-jobs?${params}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return [];

    const data = (await res.json()) as { jobs?: RemotiveJob[] };
    const jobs = data.jobs ?? [];

    return jobs
      .filter((j) => isLocationAllowed(j.candidate_required_location, filters))
      .filter((j) => (pos || kws.length) ? matchesFilters(`${j.title} ${j.description}`, filters) : true)
      .map(mapRemotive);
  } catch {
    return [];
  }
}

export async function fetchJobicy(filters: JobSearchFilters): Promise<JobOffer[]> {
  try {
    const res = await fetch("https://jobicy.com/api/v2/remote-jobs?count=50", {
      next: { revalidate: 300 },
    });
    if (!res.ok) return [];

    const data = (await res.json()) as { jobs?: JobicyJob[] };
    const jobs = data.jobs ?? [];

    const pos = filters.position?.trim();
    const kws = (filters.keywords ?? []).filter(Boolean);

    return jobs
      .filter((j) => isLocationAllowed(j.jobGeo, filters))
      .filter((j) => (pos || kws.length) ? matchesFilters(`${j.jobTitle} ${j.jobDescription}`, filters) : true)
      .map(mapJobicy);
  } catch {
    return [];
  }
}
