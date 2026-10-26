import type { CSSProperties } from "react";

/**
 * Props that make an element rise into view when it scrolls in.
 * `delay` staggers siblings that enter together (keep it small: ~60–100ms steps).
 */
export function reveal(delay = 0, style?: CSSProperties) {
  return {
    "data-reveal": "",
    style: { ...style, "--reveal-delay": `${delay}ms` } as CSSProperties,
  };
}

/** Runs before paint (inline in <head>): arm reveals only when they can actually play. */
export const revealArmScript = `(function(){try{if('IntersectionObserver' in window&&!matchMedia('(prefers-reduced-motion: reduce)').matches){document.documentElement.classList.add('reveal-armed')}}catch(e){}})();`;
