"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// Web Speech API: not in every browser (Chrome and Edge have it; Firefox does not).
type Recognition = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
};

function recognitionCtor(): (new () => Recognition) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/** Speak instead of type. `note` is a message key when the mic cannot be used. */
export function useSpeechInput(lang: string, onText: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [note, setNote] = useState<"micUnsupported" | "micBlocked" | null>(null);
  const rec = useRef<Recognition | null>(null);
  const onTextRef = useRef(onText);
  onTextRef.current = onText;

  useEffect(() => () => rec.current?.stop(), []);

  const toggle = useCallback(() => {
    if (listening) {
      rec.current?.stop();
      return;
    }
    const Ctor = recognitionCtor();
    if (!Ctor) {
      setNote("micUnsupported");
      return;
    }
    const r = new Ctor();
    r.lang = lang;
    r.interimResults = false;
    r.continuous = false;
    r.onresult = (e) => {
      const text = Array.from(e.results).map((res) => res[0]?.transcript ?? "").join(" ").trim();
      if (text) onTextRef.current(text);
    };
    r.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") setNote("micBlocked");
    };
    r.onend = () => setListening(false);
    rec.current = r;
    setNote(null);
    setListening(true);
    try {
      r.start();
    } catch {
      setListening(false);
    }
  }, [lang, listening]);

  return { listening, toggle, note };
}

/** A speechSynthesis voice for the language, or null (then no Listen button is shown). */
export function useVoice(lang: "bn" | "en"): SpeechSynthesisVoice | null {
  const [voice, setVoice] = useState<SpeechSynthesisVoice | null>(null);
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const pick = () => {
      const voices = window.speechSynthesis.getVoices();
      setVoice(voices.find((v) => v.lang.toLowerCase().startsWith(lang)) ?? null);
    };
    pick();
    window.speechSynthesis.addEventListener("voiceschanged", pick);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", pick);
  }, [lang]);
  return voice;
}
