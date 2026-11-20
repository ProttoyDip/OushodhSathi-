"use client";

import { useEffect, useState } from "react";

/**
 * The site-wide "Pause motion" switch (WCAG 2.2.2). One place decides whether anything moves:
 * `html.motion-ok` is set before first paint by `motionArmScript` when the reader has not asked for
 * reduced motion and has not paused motion here; CSS animations (the marquee) run only under it,
 * and the motion library reads `usePauseMotion()`. Content never depends on it: every section is
 * complete without motion.
 */
const KEY = "motion";
const EVENT = "motionpref";

/** Runs before paint (inline in <head>). */
export const motionArmScript = `(function(){try{var p=localStorage.getItem('${KEY}')==='paused';if(!p&&!matchMedia('(prefers-reduced-motion: reduce)').matches){document.documentElement.classList.add('motion-ok')}}catch(e){}})();`;

function readPaused(): boolean {
  try {
    return localStorage.getItem(KEY) === "paused";
  } catch {
    return false;
  }
}

function reducedByOs(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Whether motion may play now: not reduced by the OS and not paused here. */
export function motionAllowed(): boolean {
  return typeof window !== "undefined" && !reducedByOs() && !readPaused();
}

export function setPaused(paused: boolean) {
  try {
    if (paused) localStorage.setItem(KEY, "paused");
    else localStorage.removeItem(KEY);
  } catch {}
  document.documentElement.classList.toggle("motion-ok", !paused && !reducedByOs());
  window.dispatchEvent(new Event(EVENT));
}

/** [paused, setPaused]. `paused` is also true when the OS asks for reduced motion. */
export function usePauseMotion(): { paused: boolean; reducedByOs: boolean; setPaused: (p: boolean) => void } {
  const [state, setState] = useState({ paused: false, reduced: false });
  useEffect(() => {
    const update = () => setState({ paused: readPaused(), reduced: reducedByOs() });
    update();
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    window.addEventListener(EVENT, update);
    mq.addEventListener("change", update);
    return () => {
      window.removeEventListener(EVENT, update);
      mq.removeEventListener("change", update);
    };
  }, []);
  return { paused: state.paused || state.reduced, reducedByOs: state.reduced, setPaused };
}
