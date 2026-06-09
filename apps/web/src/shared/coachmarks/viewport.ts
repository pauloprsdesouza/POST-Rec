export interface ViewportInsets {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export function getViewportInsets(): ViewportInsets {
  const root = getComputedStyle(document.documentElement);
  const navHeight = Number.parseFloat(root.getPropertyValue("--postrec-nav-height")) || 56;
  const bottomNavHeight =
    window.innerWidth < 992
      ? Number.parseFloat(root.getPropertyValue("--postrec-bottom-nav-height")) || 64
      : 0;
  const safeBottom = Number.parseFloat(root.getPropertyValue("--postrec-safe-bottom")) || 0;

  return {
    top: navHeight + 12,
    right: 16,
    bottom: bottomNavHeight + safeBottom + 16,
    left: 16,
  };
}

export function getViewportSize(): { width: number; height: number } {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
  };
}
