"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { provisionTenant, searchAvailableNumbers, type AvailableNumber } from "@/lib/api/internal";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const MARKETS = [
  { value: "india_english", label: "India — English" },
  { value: "india_hindi", label: "India — Hindi" },
  { value: "us_hipaa", label: "US — HIPAA" },
];

const REGIONS = [
  { value: "IN", label: "India (+91)" },
  { value: "US", label: "United States (+1)" },
];

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

export function TenantCreateForm() {
  const router = useRouter();

  const [step, setStep] = useState<"details" | "pick">("details");
  const [businessName, setBusinessName] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [market, setMarket] = useState("india_english");
  const [region, setRegion] = useState("IN");

  const [candidates, setCandidates] = useState<AvailableNumber[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  const [searching, setSearching] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function searchNumbers() {
    setError(null);
    if (!businessName.trim()) {
      setError("Business name is required");
      return;
    }
    setSearching(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Not signed in");
        return;
      }
      const numbers = await searchAvailableNumbers(token, region);
      if (numbers.length === 0) {
        setError("No numbers available in this region — try another.");
        return;
      }
      setCandidates(numbers);
      setSelected(numbers[0]?.phone_number ?? null);
      setStep("pick");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search numbers");
    } finally {
      setSearching(false);
    }
  }

  async function createTenant() {
    if (!selected) return;
    setError(null);
    setCreating(true);
    try {
      const token = await getAccessToken();
      if (!token) {
        setError("Not signed in");
        return;
      }
      const tenant = await provisionTenant(token, {
        business_name: businessName.trim(),
        phone_number: selected,
        market,
        region,
        contact_name: contactName.trim() || null,
        contact_email: contactEmail.trim() || null,
      });
      router.push(`/internal/tenants/${tenant.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create tenant");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="flex items-start gap-3">
        <Link
          href="/internal/tenants"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Back
        </Link>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">New tenant</h1>
          <p className="text-sm text-muted-foreground">
            Create a tenant and provision its first Twilio number.
          </p>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {step === "details" ? (
        <section className="space-y-4 rounded-xl border border-zerqo-line bg-white p-5">
          <div className="space-y-1">
            <Label htmlFor="business_name">Business name</Label>
            <Input
              id="business_name"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Acme Dental"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="contact_name">Contact name</Label>
              <Input
                id="contact_name"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="contact_email">Contact email</Label>
              <Input
                id="contact_email"
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="market">Market</Label>
              <select
                id="market"
                className={SELECT_CLASS}
                value={market}
                onChange={(e) => setMarket(e.target.value)}
              >
                {MARKETS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="region">Number region</Label>
              <select
                id="region"
                className={SELECT_CLASS}
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              >
                {REGIONS.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Button
            className="bg-[#f04e00] hover:bg-[#d94400]"
            disabled={searching}
            onClick={() => void searchNumbers()}
          >
            {searching ? "Searching…" : "Search available numbers"}
          </Button>
        </section>
      ) : (
        <section className="space-y-4 rounded-xl border border-zerqo-line bg-white p-5">
          <div>
            <h2 className="font-medium">Choose a number</h2>
            <p className="text-sm text-muted-foreground">
              {businessName} · {region}
            </p>
          </div>

          <div className="space-y-2">
            {candidates.map((n) => (
              <label
                key={n.phone_number}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3",
                  selected === n.phone_number
                    ? "border-[#f04e00] bg-[#f04e00]/5"
                    : "border-zerqo-line"
                )}
              >
                <input
                  type="radio"
                  name="number"
                  value={n.phone_number}
                  checked={selected === n.phone_number}
                  onChange={() => setSelected(n.phone_number)}
                />
                <span className="font-mono text-sm">{n.phone_number}</span>
                {n.locality ? (
                  <span className="text-xs text-muted-foreground">{n.locality}</span>
                ) : null}
              </label>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" disabled={creating} onClick={() => setStep("details")}>
              Back
            </Button>
            <Button
              variant="outline"
              disabled={searching || creating}
              onClick={() => void searchNumbers()}
            >
              Show different
            </Button>
            <Button
              className="bg-[#f04e00] hover:bg-[#d94400]"
              disabled={!selected || creating}
              onClick={() => void createTenant()}
            >
              {creating ? "Creating…" : "Create tenant"}
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
