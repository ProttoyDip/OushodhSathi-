// A household opens with its private family link: /p/{id}?key=...
// The key is kept per household in this browser and sent as X-Family-Key on every request.
// The invented demo household needs no key.

const storageKey = (pid: number) => `oushodh:key:${pid}`;

export function familyKey(pid: number): string | null {
  if (typeof window === "undefined") return null;
  // a key in the address wins: it is how a shared link arrives
  const fromUrl = new URLSearchParams(window.location.search).get("key");
  if (fromUrl) {
    rememberFamilyKey(pid, fromUrl);
    return fromUrl;
  }
  try {
    return localStorage.getItem(storageKey(pid));
  } catch {
    return null;
  }
}

export function rememberFamilyKey(pid: number, key: string) {
  try {
    localStorage.setItem(storageKey(pid), key);
  } catch {}
}

/** Keeps the key out of the address bar (and out of screenshots) once it is stored. */
export function stripKeyFromUrl() {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("key")) return;
  url.searchParams.delete("key");
  window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
}

/** The private link to share with family. Null when this browser has no key (e.g. the demo). */
export function familyLink(pid: number, path = `/p/${pid}`): string | null {
  const key = familyKey(pid);
  return key ? `${window.location.origin}${path}?key=${encodeURIComponent(key)}` : null;
}
