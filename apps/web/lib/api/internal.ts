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
    paid_until: string | null;
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

export async function inviteTenantLogin(
  accessToken: string,
  tenantId: string,
  email: string,
  role: "owner" | "admin" | "member" = "owner"
): Promise<{ user_id: string; email: string }> {
  return internalFetch(`/internal/tenants/${tenantId}/invite`, accessToken, {
    method: "POST",
    body: JSON.stringify({ email, role }),
  });
}

export type PaymentRecordBody = {
  amount_inr: number;
  method: string;
  plan: string;
  period_start: string;
  period_end: string;
  reference?: string;
};

export async function recordTenantPayment(
  accessToken: string,
  tenantId: string,
  body: PaymentRecordBody
): Promise<{ status: string; paid_until: string }> {
  return internalFetch(`/internal/tenants/${tenantId}/payments`, accessToken, {
    method: "POST",
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

export type AuditLogRow = {
  id: string;
  actor_user_id: string | null;
  actor_email: string | null;
  actor_type: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  tenant_id: string | null;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type AuditLogListResponse = {
  items: AuditLogRow[];
  total: number;
  page: number;
  page_size: number;
};

export type AuditLogQuery = {
  page?: number;
  page_size?: number;
  actor_type?: string;
  action?: string;
  target_type?: string;
  tenant?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
};

export async function fetchAuditLog(
  accessToken: string,
  params: AuditLogQuery = {}
): Promise<AuditLogListResponse> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  const qs = query.toString();
  return internalFetch(`/internal/audit${qs ? `?${qs}` : ""}`, accessToken);
}

// --- Knowledge base (tickets 4.01–4.03, 4.15) --------------------------------

export type KnowledgeStatus = "pending" | "processing" | "ready" | "error";

export type KnowledgeDocument = {
  id: string;
  tenant_id: string;
  agent_id: string | null;
  filename: string;
  bytes: number;
  status: KnowledgeStatus;
  error: string | null;
  chunk_count: number | null;
  uploaded_at: string;
  processed_at: string | null;
};

export type KnowledgeDocumentDetail = KnowledgeDocument & {
  chunks_total: number | null;
  chunks_done: number;
};

export type KnowledgeChunk = {
  chunk_index: number;
  content: string;
  token_count: number | null;
};

export async function fetchKnowledgeDocuments(
  accessToken: string,
  tenantId: string
): Promise<KnowledgeDocument[]> {
  return internalFetch(`/internal/tenants/${tenantId}/knowledge`, accessToken);
}

export async function fetchKnowledgeChunks(
  accessToken: string,
  tenantId: string,
  documentId: string,
  limit = 3
): Promise<KnowledgeChunk[]> {
  return internalFetch(
    `/internal/tenants/${tenantId}/knowledge/${documentId}/chunks?limit=${limit}`,
    accessToken
  );
}

export async function uploadKnowledgeDocument(
  accessToken: string,
  tenantId: string,
  file: File
): Promise<KnowledgeDocument> {
  const form = new FormData();
  form.append("file", file);
  // No Content-Type header — the browser sets the multipart boundary.
  const response = await fetch(`${getApiBaseUrl()}/internal/tenants/${tenantId}/knowledge`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
    body: form,
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body?.detail?.message === "string"
        ? body.detail.message
        : `Upload failed (${response.status})`;
    throw new Error(message);
  }
  return (await response.json()) as KnowledgeDocument;
}

export async function reprocessKnowledgeDocument(
  accessToken: string,
  tenantId: string,
  documentId: string
): Promise<void> {
  await internalFetch(
    `/internal/tenants/${tenantId}/knowledge/${documentId}/reprocess`,
    accessToken,
    { method: "POST" }
  );
}

export async function deleteKnowledgeDocument(
  accessToken: string,
  tenantId: string,
  documentId: string
): Promise<void> {
  await internalFetch(`/internal/tenants/${tenantId}/knowledge/${documentId}`, accessToken, {
    method: "DELETE",
  });
}

// --- Leads (ticket 5.02) -----------------------------------------------------

export type LeadStatus = "new" | "contacted" | "converted" | "lost";

export type Lead = {
  id: string;
  business_name: string | null;
  contact_name: string | null;
  contact_email: string;
  contact_phone: string | null;
  message: string | null;
  source: string | null;
  status: LeadStatus;
  created_at: string;
};

export async function fetchLeads(accessToken: string, status?: LeadStatus): Promise<Lead[]> {
  const query = status ? `?status=${status}` : "";
  return internalFetch(`/internal/leads${query}`, accessToken);
}

export async function updateLeadStatus(
  accessToken: string,
  leadId: string,
  status: LeadStatus
): Promise<Lead> {
  return internalFetch(`/internal/leads/${leadId}`, accessToken, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
