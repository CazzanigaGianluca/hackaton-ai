"use client";

import { useState } from "react";
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
      setError(
        err instanceof Error ? err.message : "Errore nella chat con il coach.",
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex h-[480px] flex-col rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              message.role === "assistant"
                ? "bg-blue-50 text-gray-800"
                : "ml-auto bg-blue-600 text-white"
            }`}
          >
            {message.content}
          </div>
        ))}
        {isSending && (
          <div className="max-w-[85%] rounded-lg bg-blue-50 px-3 py-2 text-sm text-gray-400">
            Sto scrivendo...
          </div>
        )}
      </div>
      {error && <p className="px-4 text-xs text-red-600">{error}</p>}
      <div className="flex gap-2 border-t border-gray-200 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
          placeholder="Chiedi qualcosa sulle tue spese..."
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSend}
          disabled={isSending || !input.trim()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300"
        >
          Invia
        </button>
      </div>
    </div>
  );
}
