// Scan thumbnails are returned once by the API and kept only in this tab's session
// storage until the list is confirmed. They are never sent back or stored server-side.
const key = (pid: number) => `oushodh:thumbs:${pid}`;

export function saveThumbs(pid: number, thumbs: Record<number, string>) {
  try {
    sessionStorage.setItem(key(pid), JSON.stringify(thumbs));
  } catch {}
}

export function loadThumbs(pid: number): Record<number, string> {
  try {
    return JSON.parse(sessionStorage.getItem(key(pid)) || "{}");
  } catch {
    return {};
  }
}

export function clearThumbs(pid: number) {
  try {
    sessionStorage.removeItem(key(pid));
  } catch {}
}
