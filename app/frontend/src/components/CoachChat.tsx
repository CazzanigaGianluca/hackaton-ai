"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { sendCoachMessage } from "@/lib/api";
import { ConversationMessage } from "@/lib/types";

interface CoachChatProps {
  sessionId: string;
  initialConversation: ConversationMessage[];
}

export default function CoachChat({ sessionId, initialConversation }: CoachChatProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>(initialConversation);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

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
    <div className="flex h-[520px] flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-white shadow">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--primary-light)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-[var(--text)]">Assistente Educativo</p>
          <p className="text-xs text-[var(--text-muted)]">Solo educazione finanziaria · non un consulente</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--primary-light)]">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <p className="text-sm font-medium text-[var(--text)]">Ciao! Sono il tuo Assistente Educativo.</p>
            <p className="text-xs text-[var(--text-muted)]">Puoi chiedermi qualsiasi cosa sulle tue spese.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.role === "assistant" && (
              <div className="mr-2 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--primary-light)]">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
            )}
            <div
              className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                message.role === "assistant"
                  ? "bg-[var(--bg)] text-[var(--text)] rounded-tl-sm"
                  : "bg-[var(--primary)] text-white rounded-tr-sm"
              }`}
            >
              {message.role === "assistant" ? (
                <div className="prose prose-sm prose-slate max-w-none
                  prose-p:my-1 prose-p:leading-relaxed
                  prose-headings:font-semibold prose-headings:text-[var(--text)] prose-headings:my-2
                  prose-strong:font-semibold prose-strong:text-[var(--text)]
                  prose-ul:my-1 prose-ul:pl-4 prose-li:my-0.5
                  prose-ol:my-1 prose-ol:pl-4
                  prose-code:rounded prose-code:bg-white prose-code:px-1 prose-code:py-0.5 prose-code:text-xs prose-code:text-[var(--primary)] prose-code:font-mono
                  prose-pre:bg-white prose-pre:rounded-xl prose-pre:p-3 prose-pre:overflow-x-auto
                  prose-blockquote:border-l-2 prose-blockquote:border-[var(--primary)] prose-blockquote:pl-3 prose-blockquote:text-[var(--text-secondary)] prose-blockquote:italic
                  prose-a:text-[var(--primary)] prose-a:underline
                  prose-hr:border-[var(--border)]
                  prose-table:w-full prose-table:border-collapse prose-table:text-xs
                  prose-thead:bg-white prose-th:border prose-th:border-[var(--border)] prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:font-semibold prose-th:text-[var(--text)]
                  prose-td:border prose-td:border-[var(--border)] prose-td:px-3 prose-td:py-2
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
            <div className="mr-2 mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--primary-light)]">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div className="flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-[var(--bg)] px-4 py-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)] [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-[var(--text-muted)]" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-[var(--danger-light)] bg-[var(--danger-light)] px-3 py-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <p className="text-xs text-[var(--danger)]">{error}</p>
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 border-t border-[var(--border)] p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleSend(); }}
          placeholder="Chiedi qualcosa sulle tue spese..."
          className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm text-[var(--text)] placeholder-[var(--text-muted)] outline-none transition-colors focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--primary-light)]"
          disabled={isSending}
        />
        <button
          onClick={handleSend}
          disabled={isSending || !input.trim()}
          aria-label="Invia messaggio"
          className="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl bg-[var(--primary)] text-white transition-colors hover:bg-[var(--primary-hover)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
