import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const pages = ["", "/biletlar", "/imtihon", "/mavzular", "/belgilar", "/tasodifiy", "/qidiruv", "/xatolar", "/kirish", "/royxat"];
  return pages.map((p) => ({ url: `${SITE_URL}${p}`, changeFrequency: "weekly", priority: p === "" ? 1 : 0.7 }));
}
