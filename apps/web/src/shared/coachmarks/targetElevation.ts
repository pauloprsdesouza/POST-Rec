type OverflowFix = {
  element: HTMLElement;
  overflow: string;
  overflowX: string;
  overflowY: string;
};

/** Temporarily release `overflow: hidden` ancestors so the spotlight hole is not clipped. */
export function releaseOverflowClipping(element: HTMLElement): () => void {
  const fixes: OverflowFix[] = [];
  let node: HTMLElement | null = element.parentElement;

  while (node && node !== document.body) {
    const style = window.getComputedStyle(node);
    const clips =
      style.overflow === "hidden" ||
      style.overflowX === "hidden" ||
      style.overflowY === "hidden";

    if (clips) {
      fixes.push({
        element: node,
        overflow: node.style.overflow,
        overflowX: node.style.overflowX,
        overflowY: node.style.overflowY,
      });
      node.style.overflow = "visible";
      node.style.overflowX = "visible";
      node.style.overflowY = "visible";
    }
    node = node.parentElement;
  }

  return () => {
    for (const fix of fixes) {
      fix.element.style.overflow = fix.overflow;
      fix.element.style.overflowX = fix.overflowX;
      fix.element.style.overflowY = fix.overflowY;
    }
  };
}
