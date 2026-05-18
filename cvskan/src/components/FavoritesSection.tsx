"use client";
import JobOfferCard from "./JobOfferCard";
import type { JobOffer, Application } from "@/lib/types";

interface Props {
  favorites: JobOffer[];
  applications: Application[];
  onApply: (app: Application) => void;
  onToggleFavorite: (offer: JobOffer) => void;
}

export default function FavoritesSection({ favorites, applications, onApply, onToggleFavorite }: Props) {
  if (favorites.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24">
        <p className="text-5xl mb-4">🤍</p>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Brak ulubionych ofert</h2>
        <p className="text-gray-500">
          Kliknij ❤️ na kartach ofert w zakładce "Szukaj ofert", żeby je tutaj zapisać.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Ulubione oferty</h2>
        <span className="text-sm text-gray-500">{favorites.length} zapisanych</span>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        {favorites.map((offer) => (
          <JobOfferCard
            key={offer.id}
            offer={offer}
            applications={applications}
            onApply={onApply}
            isFavorited={true}
            onToggleFavorite={() => onToggleFavorite(offer)}
          />
        ))}
      </div>
    </div>
  );
}
