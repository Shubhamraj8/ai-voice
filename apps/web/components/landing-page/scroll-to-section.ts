export function scrollToSection(id: string, offset = -70) {
  const el = document.getElementById(id);
  if (!el) return;

  const lenis = (
    window as Window & {
      __lenis?: { scrollTo: (target: Element, opts?: { offset?: number }) => void };
    }
  ).__lenis;
  if (lenis?.scrollTo) {
    lenis.scrollTo(el, { offset });
    return;
  }

  window.scrollTo({ top: el.offsetTop + offset, behavior: "smooth" });
}
