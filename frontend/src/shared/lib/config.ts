/**
 * Centralised frontend config. Each state's dashboard talks to a different
 * Railway backend; we expose both URLs here so any module can reference
 * them via a single import. Module-level api.ts files still read the env
 * vars directly to keep the existing inference / fallback logic intact;
 * this object is the public surface for shared code (e.g. the Landing
 * page or any future cross-module feature).
 */

function trimSlash(url: string | undefined): string {
  return (url || "").trim().replace(/\/+$/, "");
}

export const API_URLS = {
  kerala: trimSlash(import.meta.env.VITE_API_KERALA_URL),
  tamilnadu: trimSlash(import.meta.env.VITE_API_TN_URL),
} as const;

export type StateKey = keyof typeof API_URLS;

export function getApiUrl(state: StateKey): string {
  return API_URLS[state];
}

if (import.meta.env.DEV) {
  // Dev-only sanity log so missing env vars are obvious in the console.
  // eslint-disable-next-line no-console
  console.info("[config] API_URLS:", API_URLS);
}
