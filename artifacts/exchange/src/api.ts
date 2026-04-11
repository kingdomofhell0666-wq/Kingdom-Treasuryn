import type { Catalog, UserData, DiscordUser } from "./types";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });

  if (!res.ok) {
    let msg = res.statusText;
    try {
      const body = await res.json() as { error?: string };
      if (body.error) msg = body.error;
    } catch {/* ignore */}
    throw new ApiError(res.status, msg);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getMe():      Promise<UserData>     { return request("/api/market/me"); },
  getCatalog(): Promise<Catalog>      { return request("/api/market/catalog"); },
  getUser():    Promise<DiscordUser>  { return request("/api/auth/me"); },

  purchase(item_type: string, item_id: string) {
    return request<{ ok: boolean; name: string; cost: number; new_balance: number }>(
      "/api/market/purchase",
      { method: "POST", body: JSON.stringify({ item_type, item_id }) },
    );
  },
};

export { ApiError };
