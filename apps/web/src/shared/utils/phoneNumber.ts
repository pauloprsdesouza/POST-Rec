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

function tryParseWithCountry(digits: string, country: PhoneCountry): ParsedPhone | null {
  if (!digits.startsWith(country.dialCode)) {
    return null;
  }
  return {
    countryIso: country.iso2,
    nationalNumber: digits.slice(country.dialCode.length),
  };
}

/** Strip a pasted/typed leading country code from the local number field. */
export function normalizeNationalNumber(countryIso: string, raw: string): string {
  const dialCode = getCountryByIso(countryIso).dialCode;
  let digits = raw.replace(/\D/g, "").replace(/^0+/, "");
  if (digits.startsWith(dialCode)) {
    digits = digits.slice(dialCode.length);
  }
  return digits;
}

/**
 * Split stored digits (with or without +) into country + local number.
 * When `preferredCountryIso` is set, that country is tried first so short
 * in-progress numbers (e.g. +557) keep the dial code out of the local field.
 */
export function parseStoredPhone(
  stored: string | null | undefined,
  fallbackIso = "BR",
  preferredCountryIso?: string,
): ParsedPhone {
  const digits = (stored ?? "").replace(/\D/g, "");
  if (!digits) {
    return { countryIso: preferredCountryIso ?? fallbackIso, nationalNumber: "" };
  }

  if (preferredCountryIso) {
    const preferred = getCountryByIso(preferredCountryIso);
    const parsed = tryParseWithCountry(digits, preferred);
    if (parsed) {
      return parsed;
    }
  }

  for (const country of countriesByDialCodeLength()) {
    const parsed = tryParseWithCountry(digits, country);
    if (!parsed) {
      continue;
    }
    if (parsed.nationalNumber.length > 0 || digits === country.dialCode) {
      return parsed;
    }
  }

  return { countryIso: preferredCountryIso ?? fallbackIso, nationalNumber: digits };
}

/** Build E.164-style value for the API (`+` prefix, digits only). */
export function composePhone(countryIso: string, nationalNumber: string): string {
  const country = getCountryByIso(countryIso);
  const national = normalizeNationalNumber(countryIso, nationalNumber);
  if (!national) {
    return "";
  }
  return `+${country.dialCode}${national}`;
}

export function defaultPhoneCountryIso(locale: string): string {
  return defaultCountryIsoForLocale(locale);
}
