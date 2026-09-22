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
        err instanceof Error ? err.message : "Errore inatteso durante l'analisi.",
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
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-white p-6 shadow">
        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--primary-light)]">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[var(--text)]">Analisi in corso</h3>
            <p className="text-xs text-[var(--text-muted)]">Questo richiede circa 30 secondi</p>
          </div>
        </div>
        <AgentProgress currentStage={currentStage} />
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => {
          if (!e.currentTarget.contains(e.relatedTarget as Node)) {
            setIsDragging(false);
          }
        }}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 ${
          isDragging
            ? "border-[var(--primary)] bg-[var(--primary-light)]"
            : "border-[var(--border-strong)] bg-white hover:border-[var(--primary)] hover:bg-[var(--primary-light)]"
        }`}
      >
        <div className={`flex h-12 w-12 items-center justify-center rounded-2xl transition-colors ${isDragging ? "bg-[var(--primary)]" : "bg-[var(--bg)]"}`}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={isDragging ? "white" : "var(--text-muted)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <div>
          <p className="text-sm font-medium text-[var(--text)]">
            Trascina qui i tuoi Estratti Conto
          </p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">CSV o PDF · massimo 10 file</p>
        </div>
        <label className="cursor-pointer rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] focus-within:ring-2 focus-within:ring-[var(--primary)] focus-within:ring-offset-2">
          Scegli i file
          <input
            type="file"
            multiple
            accept=".csv,.pdf"
            className="sr-only"
            onChange={(e) => addFiles(e.target.files)}
          />
        </label>
      </div>

      {files.length > 0 && (
        <ul className="space-y-1.5">
          {files.map((file) => (
            <li
              key={file.name}
              className="flex items-center gap-3 rounded-xl border border-[var(--border)] bg-white px-3 py-2.5"
            >
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[var(--primary-light)]">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
              </div>
              <span className="min-w-0 flex-1 truncate text-sm text-[var(--text)]">{file.name}</span>
              <button
                onClick={() => removeFile(file.name)}
                className="flex h-6 w-6 shrink-0 cursor-pointer items-center justify-center rounded-md text-[var(--text-muted)] transition-colors hover:bg-[var(--danger-light)] hover:text-[var(--danger)]"
                aria-label={`Rimuovi ${file.name}`}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-[var(--danger-light)] bg-[var(--danger-light)] px-3 py-2.5">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p className="text-sm text-[var(--danger)]">{error}</p>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={files.length === 0}
        className="w-full cursor-pointer rounded-xl bg-[var(--primary)] px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Analizza le mie spese
      </button>
    </div>
  );
}
