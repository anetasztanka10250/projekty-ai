export interface GapAnalysis {
  pasuje: string[];
  braki: string[];
  rekomendacje: string[];
}

export interface CvAnalysis {
  score: number;
  pasujace_slowa: string[];
  brakujace_slowa: string[];
  mocne_strony: string[];
  do_poprawy: string[];
  sugestie_ats: string[];
  gap_analysis: GapAnalysis | null;
  podsumowanie: string;
}

export interface ApplicationStatus {
  portal: string;
  date: string;
  note?: string;
}

export interface JobOffer {
  id: string;
  title: string;
  company: string;
  location: string;
  work_mode: string;
  salary: string | null;
  contract_type: string | null;
  published_at: string | null;
  url: string;
  sources: string[];
  description: string;
  is_hidden: boolean;
  is_remote_foreign: boolean;
  eu_friendly: boolean;
  competition_level: "niska" | "srednia" | "wysoka";
  application_status: ApplicationStatus | null;
  link_verified: boolean | null; // true=działa, false=zepsuty, null=niezweryfikowany (JustJoinIT/inne API)
}

export interface Application {
  id: string;
  offer_title: string;
  company: string;
  portal: string;
  applied_at: string;
  status: "wysłano" | "brak_odpowiedzi" | "rozmowa" | "odrzucono" | "oferta";
  note: string;
  url: string;
}

export interface JobSearchFilters {
  position?: string;
  keywords?: string[];
  location?: string;
  workMode?: string[];
  salaryMin?: number;
  experienceLevels?: string[];
  contractType?: string[];
  timeAdded?: "1h" | "12h" | "24h" | "3d" | "7d" | "any";
  remoteInternational?: boolean;
}

export interface GeneratedCv {
  id: string;
  type: "universal" | "targeted";
  targetOffer?: string;
  content: string;
  createdAt: string;
}

export type SearchMode = "portals" | "hidden" | "remote";

export type MainTab = "analyze" | "search" | "favorites" | "tracker" | "mycv";

export function computeOfferId(offer: {
  company?: string | null;
  title?: string | null;
  location?: string | null;
}): string {
  const slug = (s: string | null | undefined) =>
    (s ?? "")
      .toLowerCase()
      .replace(/[łł]/g, "l")
      .replace(/[ąą]/g, "a")
      .replace(/[ęę]/g, "e")
      .replace(/[żż]/g, "z")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  return (
    `${slug(offer.company)}-${slug(offer.title)}-${slug(offer.location)}`
      .replace(/-+/g, "-")
      .replace(/^-+|-+$/g, "") || "unknown"
  );
}
