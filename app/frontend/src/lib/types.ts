export type TransactionType = "entrata" | "uscita";

export interface Transaction {
  date: string;
  description: string;
  amount: number;
  type: TransactionType;
  category: string | null;
  source_file?: string | null;
}

export type Severity = "low" | "medium" | "high";

export interface Insight {
  category: string;
  user_pct: number;
  istat_pct: number;
  trend: string;
  severity: Severity;
}

export interface MonthlyTotal {
  entrate: number;
  uscite: number;
}

export interface CategoryTotal {
  total: number;
  pct_of_expenses: number;
}

export interface TopMerchant {
  description: string;
  total: number;
  count: number;
}

export interface SavingsPotentialEntry {
  user_pct: number;
  istat_pct: number;
  delta_eur: number;
}

export interface Analysis {
  monthly_totals: Record<string, MonthlyTotal>;
  by_category: Record<string, CategoryTotal>;
  by_category_by_month: Record<string, Record<string, number>>;
  top_merchants: TopMerchant[];
  heatmap_by_weekday: Record<string, number>;
  savings_potential: Record<string, SavingsPotentialEntry>;
  total_income: number;
  total_expenses: number;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export type SessionStatus =
  | "pending"
  | "parsing"
  | "categorizing"
  | "analyzing"
  | "generating_insights"
  | "coaching_ready"
  | "failed";

export interface SessionData {
  session_id: string;
  status: SessionStatus;
  created_at: string;
  transactions: Transaction[];
  analysis: Analysis | null;
  insights: Insight[];
  coach_intro: string | null;
  conversation: ConversationMessage[];
}

export interface PipelineEvent {
  stage: string;
  done: boolean;
  session_id?: string;
  error?: string;
}

export const PIPELINE_STAGE_LABELS: Record<string, string> = {
  parsing: "Lettura dell'estratto conto",
  categorizing: "Categorizzazione delle transazioni",
  analyzing: "Calcolo dei pattern di spesa",
  generating_insights: "Generazione degli insight",
  coaching_ready: "Preparazione dell'assistente educativo",
  failed: "Analisi non riuscita",
};

export const PIPELINE_STAGES = [
  "parsing",
  "categorizing",
  "analyzing",
  "generating_insights",
  "coaching_ready",
];
