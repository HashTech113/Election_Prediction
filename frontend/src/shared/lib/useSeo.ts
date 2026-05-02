import { useEffect } from "react";

type SeoOptions = {
  title: string;
  description?: string;
  canonicalPath?: string;
};

const SITE_ORIGIN = "https://owlytics.in";

function setMeta(name: string, content: string, attr: "name" | "property" = "name") {
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${name}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, name);
    document.head.appendChild(el);
  }
  el.setAttribute("content", content);
}

function setCanonical(href: string) {
  let el = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!el) {
    el = document.createElement("link");
    el.rel = "canonical";
    document.head.appendChild(el);
  }
  el.href = href;
}

export function useSeo({ title, description, canonicalPath }: SeoOptions) {
  useEffect(() => {
    document.title = title;
    setMeta("og:title", title, "property");
    setMeta("twitter:title", title);

    if (description) {
      setMeta("description", description);
      setMeta("og:description", description, "property");
      setMeta("twitter:description", description);
    }

    if (canonicalPath) {
      const url = `${SITE_ORIGIN}${canonicalPath}`;
      setCanonical(url);
      setMeta("og:url", url, "property");
    }
  }, [title, description, canonicalPath]);
}
