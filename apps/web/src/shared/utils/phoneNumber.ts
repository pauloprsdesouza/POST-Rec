import {
  defaultCountryIsoForLocale,
  getCountryByIso,
  PHONE_COUNTRIES,
  type PhoneCountry,
} from "@/shared/constants/phoneCountries";

export type ParsedPhone = {
  countryIso: string;
  nationalNumber: string;
};

function countriesByDialCodeLength(): PhoneCountry[] {
  return [...PHONE_COUNTRIES].sort((a, b) => b.dialCode.length - a.dialCode.length);
}

/** Split stored digits (with or without +) into country + local number. */
export function parseStoredPhone(
  stored: string | null | undefined,
  fallbackIso = "BR",
): ParsedPhone {
  const digits = (stored ?? "").replace(/\D/g, "");
  if (!digits) {
    return { countryIso: fallbackIso, nationalNumber: "" };
  }

  for (const country of countriesByDialCodeLength()) {
    if (!digits.startsWith(country.dialCode)) {
      continue;
    }
    const national = digits.slice(country.dialCode.length);
    if (national.length >= 4) {
      return { countryIso: country.iso2, nationalNumber: national };
    }
  }

  return { countryIso: fallbackIso, nationalNumber: digits };
}

/** Build E.164-style value for the API (`+` prefix, digits only). */
export function composePhone(countryIso: string, nationalNumber: string): string {
  const country = getCountryByIso(countryIso);
  const national = nationalNumber.replace(/\D/g, "").replace(/^0+/, "");
  if (!national) {
    return "";
  }
  return `+${country.dialCode}${national}`;
}

export function defaultPhoneCountryIso(locale: string): string {
  return defaultCountryIsoForLocale(locale);
}
