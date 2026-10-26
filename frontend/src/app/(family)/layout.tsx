export default function FamilyLayout({ children }: { children: React.ReactNode }) {
  // Elder-friendly floor: 18px body text everywhere in the family app.
  return <div className="min-h-dvh text-[18px] leading-relaxed">{children}</div>;
}
