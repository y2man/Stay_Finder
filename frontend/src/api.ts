import { useStore } from "./store";
export const API_BASE = (import.meta as any).env?.VITE_API_URL?.replace(/\/$/, "") || "";
export const assetUrl = (url: string) => url?.startsWith("/") ? `${API_BASE}${url}` : url;
export type Property = { id: string; title: string; city: string; country: string; price_per_night: string; rating: string; bedrooms: number; bathrooms?: number; max_guests: number; image_url: string; category: string; description?: string; amenities?: string[]; min_nights?: number; latitude?: number; longitude?: number };
export async function api<T = any>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const state = useStore.getState(); const isForm = typeof FormData !== "undefined" && opts.body instanceof FormData;
  const request = (token: string | null) => fetch(API_BASE + "/api/v1" + path, { method: opts.method ?? "GET", body: opts.body ? (isForm ? opts.body as FormData : JSON.stringify(opts.body)) : undefined,
    headers: { ...(isForm ? {} : { "Content-Type": "application/json" }), ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
  let r = await request(state.token);
  if (r.status === 401 && state.refreshToken && path !== "/auth/refresh") {
    try {
      const rr = await fetch(API_BASE + "/api/v1/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: state.refreshToken }) });
      if (rr.ok) { const next = await rr.json(); useStore.getState().login(next.access_token, next.role, next.refresh_token); r = await request(next.access_token); }
      else useStore.getState().login(null, null, null);
    } catch { /* show the original API error below */ }
  }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Something went wrong. Check your input and try again.");
  return j;
}
