interface ThumbIconProps {
  className?: string;
}

export function ThumbUpIcon({ className = "binary-feedback__icon" }: ThumbIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M7 10v10H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h3Zm2-1 4.5-4.2a1.5 1.5 0 0 1 2.5 1.1V10h4.3a2 2 0 0 1 1.95 2.45l-1.5 6A2 2 0 0 1 18.8 20H9V9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function ThumbDownIcon({ className = "binary-feedback__icon" }: ThumbIconProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M17 14V4h3a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-3Zm-2 1-4.5 4.2a1.5 1.5 0 0 1-2.5-1.1V14H3.7a2 2 0 0 1-1.95-2.45l1.5-6A2 2 0 0 1 5.2 4H15v11Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}
