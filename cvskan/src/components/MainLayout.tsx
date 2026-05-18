"use client";
import { useState, useCallback, useEffect } from "react";
import Header from "./Header";
import FilterPanel from "./FilterPanel";
import CvSection from "./CvSection";
import JobSearchSection from "./JobSearchSection";
import ApplicationTracker from "./ApplicationTracker";
import MyCvSection from "./MyCvSection";
import FavoritesSection from "./FavoritesSection";
import type { MainTab, JobSearchFilters, Application, GeneratedCv, JobOffer } from "@/lib/types";
import { computeOfferId } from "@/lib/types";

const TABS: { id: MainTab; label: string; icon: string }[] = [
  { id: "analyze",   label: "Analiza CV",      icon: "📄" },
  { id: "search",    label: "Szukaj ofert",     icon: "🔍" },
  { id: "favorites", label: "Ulubione",         icon: "❤️" },
  { id: "tracker",   label: "Moje Aplikacje",   icon: "📋" },
  { id: "mycv",      label: "Moje CV",          icon: "⭐" },
];

export default function MainLayout() {
  const [activeTab, setActiveTab] = useState<MainTab>("analyze");
  const [filters, setFilters] = useState<JobSearchFilters>({
    workMode: [],
    contractType: [],
    timeAdded: "any",
  });
  const [applications, setApplications] = useState<Application[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("cvskan_applications") ?? "[]");
    } catch {
      return [];
    }
  });
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  const [generatedCvs, setGeneratedCvs] = useState<GeneratedCv[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("cvskan_cvs") ?? "[]");
    } catch {
      return [];
    }
  });

  const saveApplication = useCallback((app: Application) => {
    setApplications((prev) => {
      const next = [app, ...prev];
      localStorage.setItem("cvskan_applications", JSON.stringify(next));
      return next;
    });
  }, []);

  const updateApplication = useCallback((id: string, changes: Partial<Application>) => {
    setApplications((prev) => {
      const next = prev.map((a) => (a.id === id ? { ...a, ...changes } : a));
      localStorage.setItem("cvskan_applications", JSON.stringify(next));
      return next;
    });
  }, []);

  const deleteApplication = useCallback((id: string) => {
    setApplications((prev) => {
      const next = prev.filter((a) => a.id !== id);
      localStorage.setItem("cvskan_applications", JSON.stringify(next));
      return next;
    });
  }, []);

  const [favorites, setFavorites] = useState<JobOffer[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = JSON.parse(localStorage.getItem("cvskan_favorites") ?? "[]") as JobOffer[];
      return stored.map((f) => ({ ...f, id: computeOfferId(f) }));
    } catch {
      return [];
    }
  });

  const toggleFavorite = useCallback((offer: JobOffer) => {
    const key = computeOfferId(offer);
    setFavorites((prev) => {
      const exists = prev.some((f) => computeOfferId(f) === key);
      const next = exists
        ? prev.filter((f) => computeOfferId(f) !== key)
        : [{ ...offer, id: key }, ...prev];
      localStorage.setItem("cvskan_favorites", JSON.stringify(next));
      return next;
    });
  }, []);

  const saveGeneratedCv = useCallback((cv: GeneratedCv) => {
    setGeneratedCvs((prev) => {
      const next = [cv, ...prev];
      localStorage.setItem("cvskan_cvs", JSON.stringify(next));
      return next;
    });
  }, []);

  const showSearch = activeTab === "search";

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      {/* Tab bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-screen-xl mx-auto px-4">
          <div className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                {tab.id === "tracker" && mounted && applications.length > 0 && (
                  <span className="bg-indigo-100 text-indigo-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                    {applications.length}
                  </span>
                )}
                {tab.id === "favorites" && mounted && favorites.length > 0 && (
                  <span className="bg-rose-100 text-rose-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                    {favorites.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 max-w-screen-xl mx-auto w-full px-4 py-6">
        {showSearch ? (
          <div className="flex gap-6">
            {/* Left sidebar — filters */}
            <aside className="w-72 shrink-0">
              <FilterPanel filters={filters} onChange={setFilters} />
            </aside>
            {/* Right — job results */}
            <div className="flex-1 min-w-0">
              <JobSearchSection
                filters={filters}
                applications={applications}
                onApply={saveApplication}
                onSaveCv={saveGeneratedCv}
                favorites={favorites}
                onToggleFavorite={toggleFavorite}
              />
            </div>
          </div>
        ) : activeTab === "analyze" ? (
          <CvSection
            onSaveCv={saveGeneratedCv}
            onGoToSearch={() => setActiveTab("search")}
          />
        ) : activeTab === "favorites" ? (
          <FavoritesSection
            favorites={favorites}
            applications={applications}
            onApply={saveApplication}
            onToggleFavorite={toggleFavorite}
          />
        ) : activeTab === "tracker" ? (
          <ApplicationTracker
            applications={applications}
            onUpdate={updateApplication}
            onDelete={deleteApplication}
          />
        ) : (
          <MyCvSection cvs={generatedCvs} />
        )}
      </div>

      <footer className="border-t border-gray-200 py-4 text-center text-xs text-gray-400">
        © 2026 CVSkan.pl — AI analizator CV i wyszukiwarka ofert pracy
      </footer>
    </div>
  );
}
