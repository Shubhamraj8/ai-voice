"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BookOpen, Loader2, Trash2, Upload } from "lucide-react";

import { createClient } from "@/lib/supabase/client";
import {
  deletePortalKnowledge,
  fetchPortalKnowledge,
  uploadPortalKnowledge,
  type KnowledgeDoc,
} from "@/lib/api/portal-knowledge";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_STYLE: Record<KnowledgeDoc["status"], string> = {
  pending: "bg-amber-100 text-amber-700",
  processing: "bg-amber-100 text-amber-700",
  ready: "bg-emerald-100 text-emerald-700",
  error: "bg-red-100 text-red-700",
};

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function KnowledgeManager({ initialDocs }: { initialDocs: KnowledgeDoc[] }) {
  const [docs, setDocs] = useState<KnowledgeDoc[]>(initialDocs);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    const token = await getToken();
    if (token) setDocs(await fetchPortalKnowledge(token));
  }, []);

  // Poll while any document is still being processed so status updates live.
  useEffect(() => {
    const busy = docs.some((d) => d.status === "pending" || d.status === "processing");
    if (!busy) return;
    const handle = setInterval(refresh, 3000);
    return () => clearInterval(handle);
  }, [docs, refresh]);

  const onPick = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) event.target.value = "";
    if (!file) return;

    setError(null);
    setUploading(true);
    const token = await getToken();
    if (!token) {
      setError("Your session expired — please refresh.");
      setUploading(false);
      return;
    }
    const result = await uploadPortalKnowledge(token, file);
    setUploading(false);
    if (!result.ok) {
      setError(result.error ?? "Upload failed");
      return;
    }
    await refresh();
  };

  const onDelete = async (doc: KnowledgeDoc) => {
    if (!confirm(`Delete "${doc.filename}"? This removes it from your agent's knowledge.`)) return;
    const token = await getToken();
    if (!token) return;
    await deletePortalKnowledge(token, doc.id);
    await refresh();
  };

  const readyCount = docs.filter((d) => d.status === "ready").length;
  const lastUpload = docs.length
    ? docs.reduce((a, b) => (a.uploaded_at > b.uploaded_at ? a : b)).uploaded_at
    : null;

  return (
    <div className="space-y-8">
      <div>
        <div className="mb-5 flex items-center gap-2.5">
          <span className="h-0.5 w-[22px] shrink-0 bg-zerqo-orange" />
          <span className="font-mono text-xs font-medium text-zerqo-muted">Knowledge</span>
        </div>
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-[clamp(28px,4vw,40px)] font-semibold leading-tight tracking-tight text-zerqo-ink">
              Knowledge
            </h1>
            <p className="mt-2 max-w-lg text-[15px] leading-relaxed text-zerqo-muted">
              Upload PDFs so your agent can answer from your own content.
            </p>
          </div>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 rounded-xl bg-zerqo-orange px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-zerqo-orange/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Uploading…
              </>
            ) : (
              <>
                <Upload className="size-4" /> Upload PDF
              </>
            )}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf,.pdf"
            onChange={onPick}
            className="hidden"
          />
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-700">
          {error}
        </div>
      ) : null}

      {/* Stats */}
      <div className="overflow-hidden rounded-2xl border border-zerqo-line bg-white shadow-sm">
        <div className="grid sm:grid-cols-3">
          {[
            { label: "Documents", value: String(docs.length) },
            { label: "Ready", value: String(readyCount) },
            { label: "Last upload", value: lastUpload ? formatDate(lastUpload) : "—" },
          ].map((stat, i) => (
            <div
              key={stat.label}
              className={cn(
                "flex flex-col items-center px-6 py-7 text-center",
                i > 0 && "border-t border-zerqo-line sm:border-t-0 sm:border-l"
              )}
            >
              <span className="text-[1.6rem] font-bold tabular-nums tracking-tight text-zerqo-orange">
                {stat.value}
              </span>
              <span className="mt-1.5 text-[13px] font-semibold text-zerqo-ink">{stat.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Documents */}
      <div className="rounded-2xl border border-zerqo-line bg-white shadow-sm">
        {docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
            <BookOpen className="size-7 text-zerqo-muted" />
            <p className="mt-3 text-sm font-medium text-zerqo-ink">No documents yet</p>
            <p className="mt-1 max-w-xs text-[13px] text-zerqo-muted">
              Upload a PDF and your agent will start answering from it once it&rsquo;s ready.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-zerqo-line">
            {docs.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between gap-4 px-5 py-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-zerqo-ink">
                      {doc.filename}
                    </span>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize",
                        STATUS_STYLE[doc.status]
                      )}
                    >
                      {doc.status}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[12px] text-zerqo-muted">
                    {formatBytes(doc.bytes)} · {formatDate(doc.uploaded_at)}
                    {doc.chunk_count ? ` · ${doc.chunk_count} chunks` : ""}
                    {doc.status === "error" && doc.error ? ` · ${doc.error}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onDelete(doc)}
                  aria-label={`Delete ${doc.filename}`}
                  className="shrink-0 rounded-lg p-2 text-zerqo-muted transition-colors hover:bg-red-50 hover:text-red-600"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
