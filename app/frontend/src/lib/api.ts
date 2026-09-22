import { PipelineEvent, SessionData } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Invia i file dell'Estratto Conto a /api/analyze e consuma lo stream SSE
 * di progresso della pipeline, invocando `onEvent` per ogni stage.
 */
export async function analyzeFiles(
  files: File[],
  onEvent: (event: PipelineEvent) => void,
): Promise<string> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Upload fallito: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let sessionId: string | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const event: PipelineEvent = JSON.parse(line.slice("data: ".length));
      onEvent(event);
      if (event.session_id) sessionId = event.session_id;
      if (event.error) throw new Error(event.error);
    }
  }

  if (!sessionId) throw new Error("Nessun session_id ricevuto dal server");
  return sessionId;
}

export async function getSession(sessionId: string): Promise<SessionData> {
  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`);
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? "Sessione non trovata"
        : `Errore nel caricamento della sessione: ${response.status}`,
    );
  }
  return response.json();
}

export async function sendCoachMessage(
  sessionId: string,
  message: string,
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/coach/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error(`Errore nella chat con il coach: ${response.status}`);
  }
  const data = await response.json();
  return data.reply as string;
}
