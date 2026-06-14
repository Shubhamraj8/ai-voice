import { getApiBaseUrl } from "./config";

export type TenantListItem = {
  id: string;
  slug: string;
  business_name: string;
  market: string;
  status: "active" | "paused" | "churned";
  plan: string;
  contact_email: string | null;
  contact_phone: string | null;
  agent_count: number;
  calls_last_7d: number;
  mrr_usd: number;
  created_at: string;
};

export type TenantListResponse = {
  items: TenantListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ProviderConfig = {
  stt: string;
  tts: string;
  llm: string;
};

export type TenantDetail = {
  tenant: {
    id: string;
    slug: string;
    business_name: string;
    market: string;
    language: string;
    timezone: string;
    plan: string;
    provider_config: ProviderConfig;
    onboarding_mode: string;
    status: "active" | "paused" | "churned";
    contact_email: string | null;
    contact_name: string | null;
    contact_phone: string | null;
    created_at: string;
    updated_at: string;
  };
  agent_count: number;
  calls_last_7d: number;
  mrr_usd: number;
  agents: Array<{
    id: string;
    name: string;
    phone_number: string;
    voice_id: string;
    is_active: boolean;
    starter_prompt: string;
    system_prompt: string;
    tools: string[];
  }>;
  recent_calls: Array<{
    id: string;
    twilio_call_sid: string;
    from_number: string;
    started_at: string;
    ended_at: string | null;
    duration_secs: number | null;
    outcome: string | null;
  }>;
  call_volume_14d: Array<{ day: string; count: number }>;
  audit_log: Array<{
    id: string;
    action: string;
    actor_user_id: string | null;
    payload: Record<string, unknown> | null;
    created_at: string;
  }>;
  audit_total: number;
  audit_page: number;
  audit_page_size: number;
};

export type TenantAgent = TenantDetail["agents"][number];

type TenantQuery = {
  page?: number;
  page_size?: number;
  status?: string;
  market?: string;
  search?: string;
  has_active_calls?: boolean;
  sort?: string;
};

async function internalFetch<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body?.detail?.message === "string"
        ? body.detail.message
        : `Request failed (${response.status})`;
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function bootstrapInternalSession(accessToken: string): Promise<boolean> {
  try {
    await internalFetch("/internal/ping", accessToken);
    return true;
  } catch {
    return false;
  }
}

export function buildTenantListQuery(params: TenantQuery): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.page_size) search.set("page_size", String(params.page_size));
  if (params.status) search.set("status", params.status);
  if (params.market) search.set("market", params.market);
  if (params.search) search.set("search", params.search);
  if (params.has_active_calls) search.set("has_active_calls", "true");
  if (params.sort) search.set("sort", params.sort);
  const query = search.toString();
  return query ? `?${query}` : "";
}

export async function fetchTenantList(
  accessToken: string,
  params: TenantQuery = {}
): Promise<TenantListResponse> {
  return internalFetch(`/internal/tenants${buildTenantListQuery(params)}`, accessToken);
}

export async function fetchTenantDetail(
  accessToken: string,
  tenantId: string,
  auditPage = 1
): Promise<TenantDetail> {
  const query = auditPage > 1 ? `?audit_page=${auditPage}` : "";
  return internalFetch(`/internal/tenants/${tenantId}${query}`, accessToken);
}

export async function patchTenant(
  accessToken: string,
  tenantId: string,
  body: Record<string, unknown>
): Promise<TenantDetail["tenant"]> {
  return internalFetch(`/internal/tenants/${tenantId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export type AvailableNumber = {
  phone_number: string;
  friendly_name: string | null;
  locality: string | null;
  region: string | null;
};

export async function searchAvailableNumbers(
  accessToken: string,
  region: string,
  limit = 5
): Promise<AvailableNumber[]> {
  const query = `?region=${encodeURIComponent(region)}&limit=${limit}`;
  const result = await internalFetch<{ numbers: AvailableNumber[] }>(
    `/internal/tenants/available-numbers${query}`,
    accessToken
  );
  return result.numbers;
}

export type ProvisionTenantBody = {
  business_name: string;
  phone_number: string;
  market: string;
  region: string;
  contact_name?: string | null;
  contact_email?: string | null;
};

export async function provisionTenant(
  accessToken: string,
  body: ProvisionTenantBody
): Promise<{ id: string; slug: string; business_name: string }> {
  return internalFetch(`/internal/tenants/provision`, accessToken, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function patchAgent(
  accessToken: string,
  tenantId: string,
  agentId: string,
  body: Record<string, unknown>
): Promise<TenantAgent> {
  return internalFetch(`/internal/tenants/${tenantId}/agents/${agentId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function fetchVoiceCatalog(accessToken: string): Promise<string[]> {
  const result = await internalFetch<{ voices: string[]; default: string }>(
    "/internal/voices",
    accessToken
  );
  return result.voices;
}

export async function fetchVoicePreview(accessToken: string, voiceId: string): Promise<Blob> {
  const response = await fetch(
    `${getApiBaseUrl()}/internal/voices/${encodeURIComponent(voiceId)}/preview`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    }
  );
  if (!response.ok) {
    throw new Error(`Voice preview failed (${response.status})`);
  }
  return response.blob();
}
