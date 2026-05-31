import type { LucideIcon } from "lucide-react";
import { BookOpen, LayoutDashboard, Phone, Settings } from "lucide-react";

export type PortalNavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  description: string;
  previewStats?: { label: string; value: string }[];
};

export const portalNavItems: PortalNavItem[] = [
  {
    href: "/portal/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    description: "Overview of your voice agents, calls, and account activity.",
    previewStats: [
      { label: "Calls this week", value: "—" },
      { label: "Active agents", value: "—" },
      { label: "Answer rate", value: "—" },
    ],
  },
  {
    href: "/portal/calls",
    label: "Calls",
    icon: Phone,
    description: "Review call history, transcripts, and recordings.",
    previewStats: [
      { label: "Calls today", value: "—" },
      { label: "Avg duration", value: "—" },
      { label: "Missed calls", value: "—" },
    ],
  },
  {
    href: "/portal/knowledge",
    label: "Knowledge",
    icon: BookOpen,
    description: "Upload documents and manage your agent knowledge base.",
    previewStats: [
      { label: "Documents", value: "—" },
      { label: "Chunks indexed", value: "—" },
      { label: "Last updated", value: "—" },
    ],
  },
  {
    href: "/portal/settings",
    label: "Settings",
    icon: Settings,
    description: "Configure agents, team access, and workspace preferences.",
  },
];

export const portalDefaultPath = portalNavItems[0].href;

export function getPortalNavItem(pathname: string) {
  return (
    portalNavItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`)) ??
    portalNavItems[0]
  );
}
