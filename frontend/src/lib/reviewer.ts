// The reviewer's sign-in lives in sessionStorage for this tab only (set on /review).
export const REVIEWER_SESSION = "oushodh:reviewer";

/** name/role/reg_no come from the server for a personal login; only the demo token uses a typed name. */
export type ReviewerSession = { token: string; name: string; role?: string; reg_no?: string | null; demo?: boolean };

export function reviewerSession(): ReviewerSession | null {
  try {
    const s = sessionStorage.getItem(REVIEWER_SESSION);
    return s ? (JSON.parse(s) as ReviewerSession) : null;
  } catch {
    return null;
  }
}

/** An invite link (/review?invite=...) carries the reviewer's personal token once. It is then
 * removed from the address bar so it does not stay in history or end up in a screenshot. */
export function takeInviteFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  const url = new URL(window.location.href);
  const invite = url.searchParams.get("invite");
  if (!invite) return null;
  url.searchParams.delete("invite");
  window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
  return invite;
}
