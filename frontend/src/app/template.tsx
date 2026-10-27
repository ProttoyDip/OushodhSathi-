// Re-mounts on every route change, so each page arrives with a short fade.
export default function Template({ children }: { children: React.ReactNode }) {
  return <div className="page-in">{children}</div>;
}
