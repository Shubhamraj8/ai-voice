import { redirect } from "next/navigation";
import { internalDefaultPath } from "@/components/internal-dashboard";

export default function InternalIndexPage() {
  redirect(internalDefaultPath);
}
