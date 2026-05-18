"use client";
import { useState, useCallback, useRef } from "react";

interface Props {
  onFileAccepted: (file: File) => void;
}

const ALLOWED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_SIZE_MB = 10;

export default function CvDropzone({ onFileAccepted }: Props) {
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return "Akceptuję tylko pliki PDF i DOCX.";
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `Plik jest za duży. Maksymalny rozmiar to ${MAX_SIZE_MB} MB.`;
    }
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const err = validate(file);
      if (err) {
        setFileError(err);
        return;
      }
      setFileError(null);
      onFileAccepted(file);
    },
    [onFileAccepted]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all
          ${dragging
            ? "border-indigo-500 bg-indigo-50"
            : "border-gray-300 bg-white hover:border-indigo-400 hover:bg-indigo-50/40"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={onInputChange}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-4">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${dragging ? "bg-indigo-100" : "bg-gray-100"}`}>
            <svg className={`w-8 h-8 ${dragging ? "text-indigo-600" : "text-gray-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>

          <div>
            <p className="text-base font-semibold text-gray-800">
              {dragging ? "Upuść plik tutaj" : "Przeciągnij CV tutaj lub kliknij"}
            </p>
            <p className="text-sm text-gray-500 mt-1">PDF lub DOCX · maksymalnie 10 MB</p>
          </div>

          <button
            type="button"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-6 py-2.5 rounded-lg transition-colors pointer-events-none"
          >
            Wybierz plik
          </button>
        </div>
      </div>

      {fileError && (
        <p className="mt-2 text-sm text-red-600">{fileError}</p>
      )}
    </div>
  );
}
