"use client";

import { useParams } from "next/navigation";
import { useEffect } from "react";
import { familyKey, stripKeyFromUrl } from "@/lib/familyKey";

/** Stores a shared link's ?key= for this household, then removes it from the address bar. */
export function FamilyKeyFromUrl() {
  const { id } = useParams<{ id?: string }>();
  useEffect(() => {
    const pid = Number(id);
    if (!Number.isFinite(pid)) return;
    familyKey(pid); // stores a key that arrived in the URL
    stripKeyFromUrl();
  }, [id]);
  return null;
}
