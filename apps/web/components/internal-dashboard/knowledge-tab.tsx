"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, Loader2, RefreshCw, Trash2, Upload, X } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import {
  deleteKnowledgeDocument,
  fetchKnowledgeChunks,
  fetchKnowledgeDocuments,
  reprocessKnowledgeDocument,
  uploadKnowledgeDocument,
  type KnowledgeChunk,
  type KnowledgeDocument,
  type KnowledgeStatus,
} from "@/lib/api/internal";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MAX_BYTES = 20 * 1024 * 1024;
const POLL_MS = 5000;

const STATUS_CLASS: Record<KnowledgeStatus, string> = {
  pending: "bg-zinc-200 text-zinc-700",
  processing: "bg-amber-100 text-amber-800",
  ready: "bg-emerald-100 text-emerald-800",
  error: "bg-red-100 text-red-800",
};

type KnowledgeTabProps = { tenantId: string };

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function KnowledgeTab({ tenantId }: KnowledgeTabProps) {
  const [docs, setDocs] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selected, setSelected] = useState<KnowledgeDocument | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunk[] | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<KnowledgeDocument | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocs = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      const token = await getToken();
      if (!token) {
        setError("Not signed in");
        setLoading(false);
        return;
      }
      try {
        setDocs(await fetchKnowledgeDocuments(token, tenantId));
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load documents");
      } finally {
        setLoading(false);
      }
    },
    [tenantId]
  );

  useEffect(() => {
    void loadDocs();
  }, [loadDocs]);

  // Auto-refresh while any document is still processing.
  const hasActive = docs.some((d) => d.status === "pending" || d.status === "processing");
  useEffect(() => {
    if (!hasActive) return;
    const timer = setInterval(() => void loadDocs(true), POLL_MS);
    return () => clearInterval(timer);
  }, [hasActive, loadDocs]);

  async function handleFile(file: File) {
    setError(null);
    if (file.type !== "application/pdf") {
      setError("Only PDF files are allowed");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("File exceeds the 20MB limit");
      return;
    }
    const token = await getToken();
    if (!token) {
      setError("Not signed in");
      return;
    }
    setUploading(true);
    try {
      await uploadKnowledgeDocument(token, tenantId, file);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function openDetail(doc: KnowledgeDocument) {
    setSelected(doc);
    setChunks(null);
    const token = await getToken();
    if (!token) return;
    try {
      setChunks(await fetchKnowledgeChunks(token, tenantId, doc.id, 3));
    } catch {
      setChunks([]);
    }
  }

  async function reprocess(doc: KnowledgeDocument) {
    const token = await getToken();
    if (!token) return;
    try {
      await reprocessKnowledgeDocument(token, tenantId, doc.id);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reprocess failed");
    }
  }

  async function doDelete(doc: KnowledgeDocument) {
    const token = await getToken();
    if (!token) return;
    try {
      await deleteKnowledgeDocument(token, tenantId, doc.id);
      setConfirmDelete(null);
      if (selected?.id === doc.id) setSelected(null);
      await loadDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          const file = e.dataTransfer.files?.[0];
          if (file) void handleFile(file);
        }}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed bg-white px-6 py-10 text-center transition-colors",
          dragActive ? "border-[#f04e00] bg-[#fff6f1]" : "border-zerqo-line"
        )}
      >
        <Upload className="mb-2 size-6 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">Drag &amp; drop a PDF here, or</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-2"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? "Uploading…" : "Choose file"}
        </Button>
        <p className="mt-2 text-xs text-muted-foreground">PDF only · max 20MB</p>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
            e.target.value = "";
          }}
        />
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {/* Document list */}
      <section className="rounded-xl border border-zerqo-line bg-white">
        {loading && docs.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">Loading documents…</p>
        ) : docs.length === 0 ? (
          <p className="p-5 text-sm text-muted-foreground">No documents uploaded yet.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="border-b border-zerqo-line text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left">Filename</th>
                <th className="px-4 py-3 text-left">Uploaded</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Chunks</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id} className="border-b border-zerqo-line/70">
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      className="flex items-center gap-2 text-left hover:text-[#f04e00]"
                      onClick={() => void openDetail(doc)}
                    >
                      <FileText className="size-4 shrink-0 text-muted-foreground" />
                      <span className="truncate">{doc.filename}</span>
                    </button>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(doc.uploaded_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        STATUS_CLASS[doc.status]
                      )}
                    >
                      {doc.status === "processing" ? (
                        <Loader2 className="size-3 animate-spin" />
                      ) : null}
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{doc.chunk_count ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Reprocess"
                        onClick={() => void reprocess(doc)}
                      >
                        <RefreshCw className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => setConfirmDelete(doc)}
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {/* Detail drawer */}
      {selected ? (
        <div className="fixed inset-0 z-40 flex justify-end">
          <button
            type="button"
            aria-label="Close"
            className="absolute inset-0 bg-black/30"
            onClick={() => setSelected(null)}
          />
          <div className="relative z-10 flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-zerqo-line bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between">
              <h3 className="font-medium break-all">{selected.filename}</h3>
              <Button variant="ghost" size="icon-sm" onClick={() => setSelected(null)}>
                <X className="size-4" />
              </Button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground capitalize">
              {selected.status}
              {selected.chunk_count != null ? ` · ${selected.chunk_count} chunks` : ""}
            </p>

            {selected.status === "error" && selected.error ? (
              <div className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {selected.error}
              </div>
            ) : null}

            <h4 className="mt-5 text-sm font-medium">Sample chunks</h4>
            {chunks === null ? (
              <p className="mt-2 text-sm text-muted-foreground">Loading…</p>
            ) : chunks.length === 0 ? (
              <p className="mt-2 text-sm text-muted-foreground">No chunks yet.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {chunks.map((chunk) => (
                  <li
                    key={chunk.chunk_index}
                    className="rounded-lg border border-zerqo-line bg-[#faf7f3] p-3 text-xs"
                  >
                    <div className="mb-1 text-muted-foreground">
                      #{chunk.chunk_index}
                      {chunk.token_count != null ? ` · ${chunk.token_count} tokens` : ""}
                    </div>
                    <p className="whitespace-pre-wrap">{chunk.content}</p>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-6 flex gap-2">
              <Button variant="outline" size="sm" onClick={() => void reprocess(selected)}>
                <RefreshCw className="mr-2 size-4" />
                Reprocess
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-destructive"
                onClick={() => setConfirmDelete(selected)}
              >
                <Trash2 className="mr-2 size-4" />
                Delete
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {/* Delete confirmation modal */}
      {confirmDelete ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            type="button"
            aria-label="Cancel"
            className="absolute inset-0 bg-black/40"
            onClick={() => setConfirmDelete(null)}
          />
          <div className="relative z-10 w-full max-w-sm rounded-xl border border-zerqo-line bg-white p-6 shadow-xl">
            <h3 className="font-medium">Delete document?</h3>
            <p className="mt-2 text-sm text-muted-foreground break-all">
              “{confirmDelete.filename}” and its embeddings will be removed permanently.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setConfirmDelete(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-destructive text-white hover:bg-destructive/90"
                onClick={() => void doDelete(confirmDelete)}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
