import type { MetadataRoute } from "next";

// Lets a family add OushodhSathi to the home screen. No service worker: data is always live.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "OushodhSathi · ওষুধসাথী",
    short_name: "ওষুধসাথী",
    description: "A pharmacist for every elderly home in Bangladesh.",
    start_url: "/",
    display: "standalone",
    background_color: "#f3f5f9",
    theme_color: "#2a3b91",
    lang: "bn",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" },
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
