import { cache } from "react";
import { getApiBaseUrl } from "./config";

export type KnowledgeDoc = {
  id: string;
  filename: string;
  bytes: number;
  status: "pending" | "processing" | "ready" | "error";
  error: string | null;
  chunk_count: number | null;
  uploaded_at: string;
  processed_at: string | null;
};

export async function fetchPortalKnowledge(accessToken: string): Promise<KnowledgeDoc[]> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/portal/knowledge`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok) return [];
    return (await response.json()) as KnowledgeDoc[];
  } catch {
    return [];
  }
}

export const getPortalKnowledge = cache(fetchPortalKnowledge);

export async function uploadPortalKnowledge(
  accessToken: string,
  file: File
): Promise<{ ok: boolean; error?: string }> {
  try {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${getApiBaseUrl()}/portal/knowledge`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: form,
    });
    if (response.ok) return { ok: true };
    const body = await response.json().catch(() => null);
    return { ok: false, error: body?.detail?.message ?? body?.message ?? "Upload failed" };
  } catch {
    return { ok: false, error: "Upload failed" };
  }
}

export async function deletePortalKnowledge(
  accessToken: string,
  documentId: string
): Promise<boolean> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/portal/knowledge/${documentId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.ok;
  } catch {
    return false;
  }
}
