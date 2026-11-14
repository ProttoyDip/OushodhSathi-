import { FamilyKeyFromUrl } from "@/components/FamilyKeyFromUrl";
import { Sathi } from "@/components/sathi/Sathi";

export default function FamilyLayout({ children }: { children: React.ReactNode }) {
  // Elder-friendly floor: 18px body text everywhere in the family app.
  return (
    <div className="min-h-dvh text-[18px] leading-relaxed">
      <FamilyKeyFromUrl />
      {children}
      {/* room so the end of every page can scroll clear of Sathi's button */}
      <div aria-hidden className="h-20" />
      <Sathi />
    </div>
  );
}
