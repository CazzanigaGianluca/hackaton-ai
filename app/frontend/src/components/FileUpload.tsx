"use client";

import { useRouter } from "next/navigation";
import { useState, useCallback } from "react";
import { analyzeFiles } from "@/lib/api";
import AgentProgress from "./AgentProgress";

export default function FileUpload() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    const accepted = Array.from(incoming).filter(
      (f) => f.name.toLowerCase().endsWith(".csv") || f.name.toLowerCase().endsWith(".pdf"),
    );
    setFiles((prev) => [...prev, ...accepted]);
  }, []);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setIsProcessing(true);
    setError(null);
    try {
      const sessionId = await analyzeFiles(files, (event) => {
        setCurrentStage(event.stage);
      });
      router.push(`/dashboard/${sessionId}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Errore inatteso durante l'analisi.",
      );
      setIsProcessing(false);
      setCurrentStage(null);
    }
  };

  const removeFile = (name: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  };

  if (isProcessing) {
    return (
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">
          Sto analizzando il tuo estratto conto...
        </h3>
        <AgentProgress currentStage={currentStage} />
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
          isDragging
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 bg-gray-50"
        }`}
      >
        <p className="mb-2 text-sm text-gray-600">
          Trascina qui i tuoi Estratti Conto (CSV o PDF)
        </p>
        <label className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
          Scegli i file
          <input
            type="file"
            multiple
            accept=".csv,.pdf"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </label>
      </div>

      {files.length > 0 && (
        <ul className="space-y-1 text-sm text-gray-700">
          {files.map((file) => (
            <li
              key={file.name}
              className="flex items-center justify-between rounded bg-gray-100 px-3 py-2"
            >
              <span className="truncate">{file.name}</span>
              <button
                onClick={() => removeFile(file.name)}
                className="ml-2 text-gray-400 hover:text-red-500"
                aria-label={`Rimuovi ${file.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        onClick={handleAnalyze}
        disabled={files.length === 0}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
      >
        Analizza le mie spese
      </button>
    </div>
  );
}
