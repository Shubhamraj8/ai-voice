import { cache } from "react";
import { getApiBaseUrl } from "./config";

export type MeUser = {
  id: string;
  email: string | null;
  role: string | null;
};

export type MeTenant = {
  id: string;
  slug: string;
  business_name: string;
  plan: string;
};

export type MeResponse = {
  user: MeUser;
  tenant: MeTenant;
  role: "owner" | "admin" | "member";
};

export async function fetchMe(accessToken: string): Promise<MeResponse | null> {
  try {
    const response = await fetch(`${getApiBaseUrl()}/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      next: { revalidate: 30 },
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as MeResponse;
  } catch {
    return null;
  }
}

export const getMe = cache(fetchMe);
