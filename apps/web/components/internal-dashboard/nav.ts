import type { LucideIcon } from "lucide-react";
import { Activity, Building2, FileText, Phone } from "lucide-react";

export type InternalNavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  description: string;
  previewStats?: { label: string; value: string }[];
};

export const internalNavItems: InternalNavItem[] = [
  {
    href: "/internal/tenants",
    label: "Tenants",
    icon: Building2,
    description: "Manage tenant accounts, plans, and provisioning.",
    previewStats: [
      { label: "Active tenants", value: "—" },
      { label: "New this week", value: "—" },
      { label: "On trial", value: "—" },
    ],
  },
  {
    href: "/internal/calls",
    label: "Calls",
    icon: Phone,
    description: "Browse cross-tenant call logs and recordings.",
    previewStats: [
      { label: "Calls today", value: "—" },
      { label: "Avg duration", value: "—" },
      { label: "Transfer rate", value: "—" },
    ],
  },
  {
    href: "/internal/audit-log",
    label: "Audit Log",
    icon: FileText,
    description: "Review platform actions and internal user activity.",
    previewStats: [
      { label: "Events today", value: "—" },
      { label: "Internal actions", value: "—" },
      { label: "Alerts", value: "—" },
    ],
  },
  {
    href: "/internal/metrics",
    label: "Metrics",
    icon: Activity,
    description: "Monitor platform usage, latency, and health KPIs.",
    previewStats: [
      { label: "API uptime", value: "—" },
      { label: "P95 latency", value: "—" },
      { label: "Active agents", value: "—" },
    ],
  },
];

export const internalDefaultPath = internalNavItems[0].href;

export function getInternalNavItem(href: string) {
  return internalNavItems.find((item) => item.href === href) ?? internalNavItems[0];
}
