// The reviewer's sign-in lives in sessionStorage for this tab only (set on /review).
export const REVIEWER_SESSION = "oushodh:reviewer";

export type ReviewerSession = { token: string; name: string };

export function reviewerSession(): ReviewerSession | null {
  try {
    const s = sessionStorage.getItem(REVIEWER_SESSION);
    return s ? (JSON.parse(s) as ReviewerSession) : null;
  } catch {
    return null;
  }
}
