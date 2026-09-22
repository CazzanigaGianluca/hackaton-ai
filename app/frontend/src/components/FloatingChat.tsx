"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendCoachMessage } from "@/lib/api";
import { Analysis, ConversationMessage, Insight } from "@/lib/types";

interface FloatingChatProps {
  sessionId: string;
  initialConversation: ConversationMessage[];
  analysis: Analysis;
  insights: Insight[];
}

function buildSuggestions(analysis: Analysis, insights: Insight[]): string[] {
  const suggestions: string[] = [];

  // Insights ad alta severità → domanda sulla categoria critica
  const highInsights = insights.filter((i) => i.severity === "high");
  for (const ins of highInsights.slice(0, 2)) {
    suggestions.push(
      `Spendo il ${ins.user_pct}% in "${ins.category}" rispetto alla media ISTAT del ${ins.istat_pct}%. Come posso ridurre?`
    );
  }

  // Categoria con la spesa assoluta più alta
  const topCat = Object.entries(analysis.by_category).sort(
    ([, a], [, b]) => b.total - a.total
  )[0];
  if (topCat && !highInsights.find((i) => i.category === topCat[0])) {
    suggestions.push(`Cosa mi dici sulla mia spesa in "${topCat[0]}"?`);
  }

  // Merchant più frequentato
  const topMerchant = analysis.top_merchants[0];
  if (topMerchant) {
    suggestions.push(`Spendo spesso da "${topMerchant.description}". È nella norma?`);
  }

  // Risparmio potenziale più alto
  const topSaving = Object.entries(analysis.savings_potential).sort(
    ([, a], [, b]) => b.delta_eur - a.delta_eur
  )[0];
  if (topSaving && topSaving[1].delta_eur > 0) {
    suggestions.push(
      `Potrei risparmiare €${topSaving[1].delta_eur.toFixed(0)} in "${topSaving[0]}". Come?`
    );
  }

  // Domanda generica educativa sempre presente
  suggestions.push("Come si calcola la media ISTAT usata per il confronto?");

  return suggestions.slice(0, 4);
}

export default function FloatingChat({ sessionId, initialConversation, analysis, insights }: FloatingChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ConversationMessage[]>(initialConversation);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unread, setUnread] = useState(initialConversation.length > 0 ? 1 : 0);
  const [suggestionsUsed, setSuggestionsUsed] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestions = buildSuggestions(analysis, insights);
  const userMessageCount = messages.filter((m) => m.role === "user").length;
  const showSuggestions = !suggestionsUsed && userMessageCount === 0;

  useEffect(() => {
    if (isOpen) {
      setUnread(0);
      setTimeout(() => {
        bottomRef.current?.scrollIntoView({ behavior: "instant" });
        inputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    } else if (messages.length > 0 && messages[messages.length - 1].role === "assistant") {
      setUnread((n) => n + 1);
    }
  }, [messages]);

  const handleSuggestion = (text: string) => {
    setSuggestionsUsed(true);
    setInput(text);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isSending) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const reply = await sendCoachMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore nella chat con il coach.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      {/* Chat panel */}
      <div
        className={`flex w-[360px] flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-white shadow-2xl transition-all duration-300 ease-out ${
          isOpen
            ? "max-h-[540px] opacity-100 translate-y-0"
            : "max-h-0 opacity-0 translate-y-4 pointer-events-none"
        }`}
        style={{ boxShadow: "0 20px 60px -10px rgb(0 0 0 / 0.2), 0 0 0 1px rgb(0 0 0 / 0.05)" }}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--primary-light)]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-[var(--text)]">Assistente Educativo</p>
            <p className="text-[10px] text-[var(--text-muted)]">Solo educazione finanziaria · non un consulente</p>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            aria-label="Chiudi chat"
            className="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-[var(--text-muted)] transition-colors hover:bg-[var(--bg)] hover:text-[var(--text)]"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 space-y-3 overflow-y-auto p-4" style={{ maxHeight: "380px" }}>
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-2 py-6 text-center">
              <p className="text-sm font-medium text-[var(--text)]">Ciao! Come posso aiutarti?</p>
              <p className="text-xs text-[var(--text-muted)]">Puoi chiedermi qualsiasi cosa sulle tue spese.</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              {message.role === "assistant" && (
                <div className="mr-2 mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--primary-light)]">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    <path d="M2 17l10 5 10-5"/>
                    <path d="M2 12l10 5 10-5"/>
                  </svg>
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                  message.role === "assistant"
                    ? "rounded-tl-sm bg-[var(--bg)] text-[var(--text)]"
                    : "rounded-tr-sm bg-[var(--primary)] text-white"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="prose prose-sm prose-slate max-w-none
                    prose-p:my-0.5 prose-p:leading-relaxed
                    prose-headings:font-semibold prose-headings:text-[var(--text)] prose-headings:my-1.5
                    prose-strong:font-semibold prose-strong:text-[var(--text)]
                    prose-ul:my-0.5 prose-ul:pl-4 prose-li:my-0
                    prose-ol:my-0.5 prose-ol:pl-4
                    prose-code:rounded prose-code:bg-white prose-code:px-1 prose-code:py-0.5 prose-code:text-xs prose-code:text-[var(--primary)] prose-code:font-mono
                    prose-pre:bg-white prose-pre:rounded-lg prose-pre:p-3 prose-pre:overflow-x-auto prose-pre:text-xs
                    prose-blockquote:border-l-2 prose-blockquote:border-[var(--primary)] prose-blockquote:pl-3 prose-blockquote:text-[var(--text-secondary)] prose-blockquote:italic
                    prose-a:text-[var(--primary)] prose-a:underline
                    prose-hr:border-[var(--border)]
                    prose-table:w-full prose-table:border-collapse prose-table:text-xs
                    prose-th:border prose-th:border-[var(--border)] prose-th:px-2 prose-th:py-1.5 prose-th:text-left prose-th:font-semibold prose-th:bg-white prose-th:text-[var(--text)]
                    prose-td:border prose-td:border-[var(--border)] prose-td:px-2 prose-td:py-1.5
                    prose-tr:even:bg-white prose-tr:odd:bg-[var(--bg)]
                  ">
                    <div className="overflow-x-auto">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                    </div>
                  </div>
                ) : (
                  message.content
                )}
              </div>
            </div>
          ))}

          {isSending && (
            <div className="flex justify-start">
              <div className="mr-2 mt-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--primary-light)]">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-[var(--bg)] px-3 py-2.5">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)]" />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Suggested questions — anchored above input, visible until first user message */}
        {showSuggestions && (
          <div className="border-t border-[var(--border)] px-3 pt-2 pb-1">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Domande suggerite
            </p>
            <div className="flex flex-wrap gap-1.5">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSuggestion(s)}
                  className="cursor-pointer rounded-full border border-[var(--border)] bg-[var(--bg)] px-2.5 py-1 text-left text-xs text-[var(--text-secondary)] transition-colors hover:border-[var(--primary)] hover:bg-[var(--primary-light)] hover:text-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-1"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mx-3 mb-2 flex items-center gap-2 rounded-xl bg-[var(--danger-light)] px-3 py-2">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            <p className="text-xs text-[var(--danger)]">{error}</p>
          </div>
        )}

        {/* Input */}
        <div className="flex gap-2 border-t border-[var(--border)] p-3">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleSend(); }}
            placeholder="Chiedi qualcosa sulle tue spese..."
            disabled={isSending}
            className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-sm text-[var(--text)] placeholder-[var(--text-muted)] outline-none transition-colors focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--primary-light)]"
          />
          <button
            onClick={handleSend}
            disabled={isSending || !input.trim()}
            aria-label="Invia messaggio"
            className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-xl bg-[var(--primary)] text-white transition-colors hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>

      {/* FAB */}
      <button
        onClick={() => setIsOpen((o) => !o)}
        aria-label={isOpen ? "Chiudi assistente" : "Apri assistente educativo"}
        className="relative flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-[var(--primary)] text-white shadow-lg shadow-blue-900/30 transition-all duration-200 hover:bg-[var(--primary-hover)] hover:scale-105 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 active:scale-95"
      >
        {/* Unread badge */}
        {unread > 0 && !isOpen && (
          <span className="absolute -right-0.5 -top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-[var(--accent)] text-[10px] font-bold text-white ring-2 ring-white">
            {unread}
          </span>
        )}

        {/* Icon toggles between chat and close */}
        <span className={`absolute transition-all duration-200 ${isOpen ? "opacity-100 rotate-0" : "opacity-0 rotate-90"}`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </span>
        <span className={`absolute transition-all duration-200 ${isOpen ? "opacity-0 -rotate-90" : "opacity-100 rotate-0"}`}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </span>
      </button>
    </div>
  );
}
