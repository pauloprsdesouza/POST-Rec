type NavIconName = "new" | "runs" | "projects" | "profile" | "insights" | "setup" | "help";

interface NavIconProps {
  name: NavIconName;
  className?: string;
}

export function NavIcon({ name, className = "bottom-nav__svg" }: NavIconProps) {
  const common = { className, viewBox: "0 0 24 24", fill: "none", "aria-hidden": true as const };

  switch (name) {
    case "new":
      return (
        <svg {...common}>
          <path
            d="M12 5v14M5 12h14"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      );
    case "runs":
      return (
        <svg {...common}>
          <path
            d="M4 6h16M4 12h16M4 18h10"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "projects":
      return (
        <svg {...common}>
          <path
            d="M5 5h5v5H5V5Zm9 0h5v5h-5V5ZM5 14h5v5H5v-5Zm9 3h5v2h-5v-2Z"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "profile":
      return (
        <svg {...common}>
          <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "insights":
      return (
        <svg {...common}>
          <path
            d="M4 19V5M4 19h16M8 15l3-4 3 2 4-6"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "setup":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M12 7v5l3 2"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    case "help":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.75" />
          <path
            d="M9.5 9a2.5 2.5 0 0 1 4.2 1.8c0 1.5-2.2 1.8-2.2 3.2M12 17h.01"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
        </svg>
      );
    default:
      return null;
  }
}
