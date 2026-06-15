"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  fetchVoiceCatalog,
  fetchVoicePreview,
  patchAgent,
  type TenantAgent,
} from "@/lib/api/internal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const MAX_PROMPT = 4000;

const SELECT_CLASS =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 " +
  "text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 " +
  "focus-visible:ring-ring";

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

type AgentEditFormProps = {
  tenantId: string;
  agent: TenantAgent;
  onSaved: () => void;
};

export function AgentEditForm({ tenantId, agent, onSaved }: AgentEditFormProps) {
  const [name, setName] = useState(agent.name);
  const [systemPrompt, setSystemPrompt] = useState(agent.system_prompt);
  const [voiceId, setVoiceId] = useState(agent.voice_id);
  const [isActive, setIsActive] = useState(agent.is_active);

  const [voices, setVoices] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const token = await getAccessToken();
      if (!token) return;
      try {
        setVoices(await fetchVoiceCatalog(token));
      } catch {
        // Dropdown still works with the current value below.
      }
    })();
  }, []);

  // Keep the agent's current voice selectable even if it isn't in the
  // catalogue (e.g. a legacy value).
  const voiceOptions = voices.includes(voiceId) ? voices : [voiceId, ...voices];

  const promptTooLong = systemPrompt.length > MAX_PROMPT;
  const canSave = name.trim().length > 0 && systemPrompt.trim().length > 0 && !promptTooLong;

  async function preview() {
    setError(null);
    setPreviewing(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Not signed in");
        return;
      }
      const blob = await fetchVoicePreview(token, voiceId);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      await audio.play();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setPreviewing(false);
    }
  }

  async function save() {
    if (!canSave) return;
    setError(null);
    setSaved(false);
    setSaving(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Not signed in");
        return;
      }
      await patchAgent(token, tenantId, agent.id, {
        name: name.trim(),
        system_prompt: systemPrompt,
        voice_id: voiceId,
        is_active: isActive,
      });
      setSaved(true);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-4 rounded-xl border border-zerqo-line bg-white p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-mono text-sm">{agent.phone_number}</h3>
        <span className="text-xs text-muted-foreground">
          {agent.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      ) : null}
      {saved ? (
        <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          Saved ✓
        </div>
      ) : null}

      <div className="space-y-1">
        <Label htmlFor={`name-${agent.id}`}>Name</Label>
        <Input id={`name-${agent.id}`} value={name} onChange={(e) => setName(e.target.value)} />
      </div>

      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <Label htmlFor={`prompt-${agent.id}`}>System prompt</Label>
          <span
            className={cn("text-xs", promptTooLong ? "text-destructive" : "text-muted-foreground")}
          >
            {systemPrompt.length} / {MAX_PROMPT}
          </span>
        </div>
        <textarea
          id={`prompt-${agent.id}`}
          className="min-h-32 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <Label htmlFor={`voice-${agent.id}`}>Voice</Label>
          <div className="flex gap-2">
            <select
              id={`voice-${agent.id}`}
              className={SELECT_CLASS}
              value={voiceId}
              onChange={(e) => setVoiceId(e.target.value)}
            >
              {voiceOptions.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={previewing}
              onClick={() => void preview()}
            >
              {previewing ? "…" : "Preview"}
            </Button>
          </div>
        </div>
        <div className="space-y-1">
          <Label htmlFor={`status-${agent.id}`}>Status</Label>
          <select
            id={`status-${agent.id}`}
            className={SELECT_CLASS}
            value={isActive ? "active" : "inactive"}
            onChange={(e) => setIsActive(e.target.value === "active")}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <div className="space-y-1">
        <Label>Tools</Label>
        <p className="text-xs text-muted-foreground">
          {agent.tools.length
            ? agent.tools.join(", ")
            : "No tools yet — multi-select arrives in Phase 4."}
        </p>
      </div>

      <Button
        className="bg-[#f04e00] hover:bg-[#d94400]"
        disabled={saving || !canSave}
        onClick={() => void save()}
      >
        {saving ? "Saving…" : "Save changes"}
      </Button>
    </section>
  );
}
