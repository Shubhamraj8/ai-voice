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
