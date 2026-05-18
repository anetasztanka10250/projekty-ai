"use client";
import { useState } from "react";
import type { Application } from "@/lib/types";

const STATUSES: Application["status"][] = [
  "wysłano", "brak_odpowiedzi", "rozmowa", "odrzucono", "oferta",
];

const STATUS_CFG: Record<Application["status"], { label: string; color: string }> = {
  wysłano: { label: "Wysłano", color: "bg-blue-100 text-blue-700" },
  brak_odpowiedzi: { label: "Brak odpowiedzi", color: "bg-gray-100 text-gray-600" },
  rozmowa: { label: "🗓 Rozmowa", color: "bg-yellow-100 text-yellow-700" },
  odrzucono: { label: "Odrzucono", color: "bg-red-100 text-red-700" },
  oferta: { label: "🎉 Oferta!", color: "bg-green-100 text-green-700" },
};

interface Props {
  applications: Application[];
  onUpdate: (id: string, changes: Partial<Application>) => void;
  onDelete: (id: string) => void;
}

export default function ApplicationTracker({ applications, onUpdate, onDelete }: Props) {
  const [filterStatus, setFilterStatus] = useState<Application["status"] | "all">("all");
  const [editingNote, setEditingNote] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const filtered =
    filterStatus === "all" ? applications : applications.filter((a) => a.status === filterStatus);

  if (applications.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-24">
        <p className="text-5xl mb-4">📋</p>
        <h2 className="text-xl font-bold text-gray-800 mb-2">Brak aplikacji</h2>
        <p className="text-gray-500">Aplikacje pojawią się tutaj po potwierdzeniu wysłania na karcie oferty.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900">Moje Aplikacje</h2>
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setFilterStatus("all")}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${filterStatus === "all" ? "bg-indigo-600 border-indigo-600 text-white" : "border-gray-200 text-gray-600"}`}
          >
            Wszystkie ({applications.length})
          </button>
          {STATUSES.map((s) => {
            const cnt = applications.filter((a) => a.status === s).length;
            if (!cnt) return null;
            return (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${filterStatus === s ? "bg-indigo-600 border-indigo-600 text-white" : "border-gray-200 text-gray-600"}`}
              >
                {STATUS_CFG[s].label} ({cnt})
              </button>
            );
          })}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {["Oferta", "Firma", "Portal", "Data", "Status", "Notatka", ""].map((h) => (
                <th key={h} className="text-left text-xs font-semibold text-gray-500 px-4 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((app) => {
              const cfg = STATUS_CFG[app.status];
              return (
                <tr key={app.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <a href={app.url} target="_blank" rel="noopener noreferrer"
                      className="font-medium text-gray-900 hover:text-indigo-600 transition-colors line-clamp-1">
                      {app.offer_title}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{app.company}</td>
                  <td className="px-4 py-3 text-gray-400">{app.portal}</td>
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{app.applied_at}</td>
                  <td className="px-4 py-3">
                    <select
                      value={app.status}
                      onChange={(e) => onUpdate(app.id, { status: e.target.value as Application["status"] })}
                      className={`text-xs font-medium px-2 py-1 rounded-full border-0 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${cfg.color}`}
                    >
                      {STATUSES.map((s) => (
                        <option key={s} value={s}>{STATUS_CFG[s].label}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    {editingNote === app.id ? (
                      <div className="flex gap-1">
                        <input
                          autoFocus
                          value={noteText}
                          onChange={(e) => setNoteText(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              onUpdate(app.id, { note: noteText });
                              setEditingNote(null);
                            }
                            if (e.key === "Escape") setEditingNote(null);
                          }}
                          className="border border-gray-200 rounded px-2 py-1 text-xs w-32 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        />
                        <button onClick={() => { onUpdate(app.id, { note: noteText }); setEditingNote(null); }}
                          className="text-indigo-600 text-xs">✓</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setEditingNote(app.id); setNoteText(app.note); }}
                        className="text-xs text-gray-400 hover:text-gray-600 text-left line-clamp-1 max-w-[120px]"
                      >
                        {app.note || "+ dodaj notatkę"}
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {app.url && (
                        <a href={app.url} target="_blank" rel="noopener noreferrer"
                          className="text-xs text-indigo-600 hover:text-indigo-800">↗</a>
                      )}
                      {deleteConfirm === app.id ? (
                        <span className="flex items-center gap-1 text-xs">
                          <span className="text-gray-500">Usunąć?</span>
                          <button
                            onClick={() => { onDelete(app.id); setDeleteConfirm(null); }}
                            className="text-red-600 hover:text-red-800 font-medium"
                          >
                            Tak
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            Nie
                          </button>
                        </span>
                      ) : (
                        <button
                          onClick={() => setDeleteConfirm(app.id)}
                          className="text-gray-300 hover:text-red-500 transition-colors text-sm"
                          title="Usuń aplikację"
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
