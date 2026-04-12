/**
 * API utility for calling the backend Express API.
 *
 * IMPORTANT: All paths must start with /api/...
 * Do NOT prepend BASE_URL here — the API routes are served at the root /api/
 * regardless of which base path the dashboard SPA is mounted at.
 *
 * The generated @workspace/api-client-react hooks handle their own URL construction.
 * This utility is only for the custom config endpoints not in the OpenAPI spec.
 */

function logError(method: string, path: string, status: number | string, detail: string) {
  console.error(
    `[API] ${method} ${path} → ${status}: ${detail}`
  );
}

export async function apiGet<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { credentials: "include" });
  } catch (e) {
    logError("GET", path, "NETWORK", String(e));
    throw new Error(`Network error fetching ${path}: ${e}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    logError("GET", path, res.status, text.slice(0, 200));
    let message = res.statusText;
    try { message = JSON.parse(text)?.error ?? res.statusText; } catch {}
    throw new Error(`GET ${path} failed (${res.status}): ${message}`);
  }

  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    logError("GET", path, res.status, `Expected JSON but got ${contentType}`);
    throw new Error(`GET ${path}: server returned non-JSON (${contentType}). Check that the URL is correct.`);
  }

  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e) {
    logError("POST", path, "NETWORK", String(e));
    throw new Error(`Network error posting to ${path}: ${e}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    logError("POST", path, res.status, text.slice(0, 200));
    let message = res.statusText;
    try { message = JSON.parse(text)?.error ?? res.statusText; } catch {}
    throw new Error(`POST ${path} failed (${res.status}): ${message}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
  } catch (e) {
    logError("PATCH", path, "NETWORK", String(e));
    throw new Error(`Network error patching ${path}: ${e}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    logError("PATCH", path, res.status, text.slice(0, 200));
    let message = res.statusText;
    try { message = JSON.parse(text)?.error ?? res.statusText; } catch {}
    throw new Error(`PATCH ${path} failed (${res.status}): ${message}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
  } catch (e) {
    logError("PUT", path, "NETWORK", String(e));
    throw new Error(`Network error putting ${path}: ${e}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    logError("PUT", path, res.status, text.slice(0, 200));
    let message = res.statusText;
    try { message = JSON.parse(text)?.error ?? res.statusText; } catch {}
    throw new Error(`PUT ${path} failed (${res.status}): ${message}`);
  }
  return res.json() as Promise<T>;
}

export async function apiDelete<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "DELETE",
      credentials: "include",
    });
  } catch (e) {
    logError("DELETE", path, "NETWORK", String(e));
    throw new Error(`Network error deleting ${path}: ${e}`);
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    logError("DELETE", path, res.status, text.slice(0, 200));
    let message = res.statusText;
    try { message = JSON.parse(text)?.error ?? res.statusText; } catch {}
    throw new Error(`DELETE ${path} failed (${res.status}): ${message}`);
  }
  return res.json() as Promise<T>;
}
