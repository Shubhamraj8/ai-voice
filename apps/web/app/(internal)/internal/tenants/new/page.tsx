import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NewTenantPlaceholderPage() {
  return (
    <div className="rounded-xl border border-dashed border-zerqo-line bg-white p-10 text-center">
      <h1 className="text-xl font-semibold">New tenant</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Full create flow with Twilio number provisioning is ticket 3.06. Use the API{" "}
        <code className="rounded bg-muted px-1 py-0.5 text-xs">POST /internal/tenants</code> until
        then.
      </p>
      <Link
        href="/internal/tenants"
        className={cn(buttonVariants({ variant: "outline" }), "mt-6 inline-flex")}
      >
        Back to tenants
      </Link>
    </div>
  );
}
