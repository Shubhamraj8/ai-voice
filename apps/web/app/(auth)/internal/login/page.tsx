"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Shield } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { bootstrapInternalSession } from "@/lib/api/internal";
import { resolveInternalPostLoginPath } from "@/lib/auth/post-login-path";
import { Button, buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function InternalLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectParam = searchParams.get("redirect");
  const denied = searchParams.get("denied") === "1";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(denied);
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    async function checkExistingSession() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        setCheckingSession(false);
        return;
      }

      const ok = await bootstrapInternalSession(session.access_token);
      if (ok) {
        const result = await resolveInternalPostLoginPath(supabase, redirectParam);
        if (result.ok) {
          router.replace(result.path);
        }
        return;
      }

      setAccessDenied(true);
      setCheckingSession(false);
    }

    void checkExistingSession();
  }, [redirectParam, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setAccessDenied(false);
    setLoading(true);

    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      setError(signInError.message);
      setLoading(false);
      return;
    }

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      setError("Sign-in succeeded but no session was created.");
      setLoading(false);
      return;
    }

    const ok = await bootstrapInternalSession(session.access_token);
    if (!ok) {
      setAccessDenied(true);
      setLoading(false);
      return;
    }

    const result = await resolveInternalPostLoginPath(supabase, redirectParam);
    if (!result.ok) {
      setAccessDenied(true);
      setLoading(false);
      return;
    }

    router.push(result.path);
    router.refresh();
  }

  if (checkingSession) {
    return (
      <div className="internal-grain flex min-h-screen items-center justify-center text-muted-foreground">
        Checking session…
      </div>
    );
  }

  if (accessDenied) {
    return (
      <div className="internal-grain flex min-h-screen items-center justify-center px-4">
        <Card className="w-full max-w-md border-orange-200">
          <CardHeader>
            <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
              <Shield className="size-5" />
            </div>
            <CardTitle>Internal access required</CardTitle>
            <CardDescription>
              This console is for authorized staff only. Your account does not have internal
              permissions. Contact your administrator if you need access.
            </CardDescription>
          </CardHeader>
          <CardFooter className="flex flex-col gap-3">
            <Link href="/login" className={cn(buttonVariants({ variant: "outline" }), "w-full")}>
              Go to client portal login
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="internal-grain flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm border-orange-200 shadow-lg">
        <CardHeader>
          <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
            <Shield className="size-5" />
          </div>
          <CardTitle className="text-[#f04e00]">Internal console</CardTitle>
          <CardDescription>Sign in with your ZERQO staff account</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error ? (
              <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            ) : null}
            <div className="space-y-2">
              <Label htmlFor="email">Work email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@zerqo.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full bg-[#f04e00] hover:bg-[#d94400]"
              disabled={loading}
            >
              {loading ? "Signing in…" : "Sign in to internal"}
            </Button>
            <p className="text-center text-xs text-muted-foreground">
              Client portal?{" "}
              <Link href="/login" className="font-medium text-foreground hover:underline">
                Tenant login
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

export default function InternalLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="internal-grain flex min-h-screen items-center justify-center text-muted-foreground">
          Loading…
        </div>
      }
    >
      <InternalLoginForm />
    </Suspense>
  );
}
