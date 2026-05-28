import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function HomePage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-16">
      <section className="flex flex-col gap-4 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          AI voice agents for your business
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
          Deploy intelligent phone agents that handle calls, bookings, and customer support — 24/7.
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <Link href="/signup" className={cn(buttonVariants({ size: "lg" }))}>
            Get started
          </Link>
          <Link href="/login" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            Sign in
          </Link>
        </div>
      </section>

      <section className="grid gap-6 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Always on</CardTitle>
            <CardDescription>Never miss a call with 24/7 AI agents.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Handle inbound calls automatically with natural conversation.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Easy setup</CardTitle>
            <CardDescription>Go live in minutes, not weeks.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Choose a starter prompt, configure your voice, and start receiving calls.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Full visibility</CardTitle>
            <CardDescription>Transcripts, summaries, and analytics.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Review every call with detailed logs and outcome tracking.
            </p>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
