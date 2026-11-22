import type { MetadataRoute } from "next";
import { SITE_NAME } from "@/lib/site";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: `${SITE_NAME} — YHQ imtihoniga tayyorgarlik`,
    short_name: SITE_NAME,
    description: "Haydovchilik nazariy imtihoniga tayyorgarlik: biletlar, imtihon rejimi, yo'l belgilari.",
    start_url: "/",
    display: "standalone",
    background_color: "#06122b",
    theme_color: "#0b1f4b",
    lang: "uz",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
