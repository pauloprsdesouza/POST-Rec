import { useState } from "react";

import { countryFlag } from "@/shared/constants/phoneCountries";

interface CountryFlagProps {
  iso2: string;
  size?: number;
  className?: string;
}

/** Renders a country flag icon (PNG on Windows; emoji fallback if the image fails). */
export function CountryFlag({ iso2, size = 20, className = "" }: CountryFlagProps) {
  const code = iso2.toLowerCase();
  const [imageFailed, setImageFailed] = useState(false);

  if (imageFailed) {
    return (
      <span
        className={`country-flag country-flag--emoji ${className}`.trim()}
        aria-hidden
        style={{ fontSize: size }}
      >
        {countryFlag(iso2)}
      </span>
    );
  }

  return (
    <img
      className={`country-flag ${className}`.trim()}
      src={`https://flagcdn.com/w40/${code}.png`}
      srcSet={`https://flagcdn.com/w80/${code}.png 2x`}
      width={size}
      height={Math.round(size * 0.75)}
      alt=""
      loading="lazy"
      decoding="async"
      onError={() => setImageFailed(true)}
    />
  );
}
