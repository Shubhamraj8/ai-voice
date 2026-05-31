import { redirect } from "next/navigation";
import { portalDefaultPath } from "@/components/portal-dashboard";

export default function PortalIndexPage() {
  redirect(portalDefaultPath);
}
