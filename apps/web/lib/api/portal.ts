import { cache } from "react";
import { getApiBaseUrl } from "./config";

export type DashboardStats = {
  calls_this_month: number;
  minutes_used: number;
  minutes_included: number;
  escalations_this_month: number;
};

export type CallPoint = {
  date: string; // YYYY-MM-DD
  count: number;
};

export type RecentCall = {
  id: string;
  from_number: string;
  started_at: string;
  duration_secs: number | null;
  outcome: string | null;
  intent: string | null;
  summary: string | null;
};

export type KnowledgeStatus = {
  document_count: number;
  ready_count: number;
  last_upload: string | null;
};

export type PlanCard = {
  key: string;
  name: string | null;
  included_minutes: number;
  paid_until: string | null;
};

export type DashboardSummary = {
  stats: DashboardStats;
  calls_over_time: CallPoint[];
  recent_calls: RecentCall[];
  knowledge: KnowledgeStatus;
  plan: PlanCard;
};

export async function fetchDashboardSummary(accessToken: string): Promise<DashboardSummary | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/portal/dashboard`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as DashboardSummary;
  } catch {
    return null;
  }
}

export const getDashboardSummary = cache(fetchDashboardSummary);

export type CallListPage = {
  items: RecentCall[];
  total: number;
  page: number;
  page_size: number;
  available_intents: string[];
};

export type CallsQuery = {
  page?: number;
  outcome?: string;
  intent?: string;
  search?: string;
  date_from?: string; // YYYY-MM-DD
  date_to?: string; // YYYY-MM-DD
};

export async function fetchCalls(
  accessToken: string,
  query: CallsQuery
): Promise<CallListPage | null> {
  const params = new URLSearchParams();
  if (query.page && query.page > 1) params.set("page", String(query.page));
  if (query.outcome) params.set("outcome", query.outcome);
  if (query.intent) params.set("intent", query.intent);
  if (query.search) params.set("search", query.search);
  // Date inputs are day-granular; widen to inclusive day bounds for the API.
  if (query.date_from) params.set("date_from", `${query.date_from}T00:00:00`);
  if (query.date_to) params.set("date_to", `${query.date_to}T23:59:59`);

  const qs = params.toString();
  try {
    const response = await fetch(`${getApiBaseUrl()}/portal/calls${qs ? `?${qs}` : ""}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as CallListPage;
  } catch {
    return null;
  }
}

export const getCalls = cache(fetchCalls);

export type TranscriptMessage = {
  role: string;
  content: string;
  created_at: string;
  latency_ms: number | null;
};

export type ToolDispatch = {
  tool_name: string;
  tool_args: Record<string, unknown> | null;
  tool_result: Record<string, unknown> | null;
  created_at: string;
};

export type CallEscalation = {
  summary: string;
  urgency: string;
  created_at: string;
};

export type CallDetail = {
  id: string;
  from_number: string;
  started_at: string;
  ended_at: string | null;
  duration_secs: number | null;
  outcome: string | null;
  intent: string | null;
  summary: string | null;
  agent_name: string | null;
  recording_signed_url: string | null;
  transcript: TranscriptMessage[];
  tools: ToolDispatch[];
  escalation: CallEscalation | null;
};

export async function fetchCallDetail(
  accessToken: string,
  callId: string
): Promise<CallDetail | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/portal/calls/${callId}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as CallDetail;
  } catch {
    return null;
  }
}

export const getCallDetail = cache(fetchCallDetail);
