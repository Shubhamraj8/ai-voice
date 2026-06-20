import { ShieldCheck } from "lucide-react";

import type { ConsentDisclosure } from "@/lib/api/portal";

export function ConsentCard({ disclosure }: { disclosure: ConsentDisclosure | null }) {
  return (
    <div className="rounded-2xl border border-zerqo-line bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 text-zerqo-muted">
        <ShieldCheck className="size-4" />
        <h2 className="text-base font-semibold tracking-tight text-zerqo-ink">
          Call consent disclosure
        </h2>
      </div>
      <p className="mt-2 max-w-xl text-[13px] leading-relaxed text-zerqo-muted">
        This notice is spoken to every caller before any recording begins, so consent is given up
        front (DPDP §6).
      </p>

      <blockquote className="mt-4 rounded-xl border border-zerqo-line bg-zerqo-cream/50 px-4 py-3 text-sm italic text-zerqo-ink">
        “{disclosure?.text ?? disclosure?.default_text ?? "—"}”
      </blockquote>

      <p className="mt-3 text-[12px] text-zerqo-muted">
        {disclosure?.is_custom ? "Custom wording for your market." : "Standard disclosure."} Editing
        your disclosure will be available in a future release — contact us to change it.
      </p>
    </div>
  );
}
