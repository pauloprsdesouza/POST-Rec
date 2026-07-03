export type PhoneCountry = {
  iso2: string;
  name: string;
  dialCode: string;
};

/** ISO 3166-1 alpha-2 → regional indicator flag emoji. */
export function countryFlag(iso2: string): string {
  const code = iso2.toUpperCase();
  if (code.length !== 2) {
    return "";
  }
  return String.fromCodePoint(...[...code].map((char) => 0x1f1e6 - 65 + char.charCodeAt(0)));
}

const entries: PhoneCountry[] = [
  { iso2: "BR", name: "Brazil", dialCode: "55" },
  { iso2: "US", name: "United States", dialCode: "1" },
  { iso2: "ES", name: "Spain", dialCode: "34" },
  { iso2: "PT", name: "Portugal", dialCode: "351" },
  { iso2: "GB", name: "United Kingdom", dialCode: "44" },
  { iso2: "DE", name: "Germany", dialCode: "49" },
  { iso2: "FR", name: "France", dialCode: "33" },
  { iso2: "MX", name: "Mexico", dialCode: "52" },
  { iso2: "AR", name: "Argentina", dialCode: "54" },
  { iso2: "CO", name: "Colombia", dialCode: "57" },
  { iso2: "CL", name: "Chile", dialCode: "56" },
  { iso2: "CA", name: "Canada", dialCode: "1" },
  { iso2: "IN", name: "India", dialCode: "91" },
  { iso2: "AU", name: "Australia", dialCode: "61" },
  { iso2: "IT", name: "Italy", dialCode: "39" },
  { iso2: "NL", name: "Netherlands", dialCode: "31" },
  { iso2: "BE", name: "Belgium", dialCode: "32" },
  { iso2: "CH", name: "Switzerland", dialCode: "41" },
  { iso2: "AT", name: "Austria", dialCode: "43" },
  { iso2: "SE", name: "Sweden", dialCode: "46" },
  { iso2: "NO", name: "Norway", dialCode: "47" },
  { iso2: "DK", name: "Denmark", dialCode: "45" },
  { iso2: "FI", name: "Finland", dialCode: "358" },
  { iso2: "PL", name: "Poland", dialCode: "48" },
  { iso2: "CZ", name: "Czechia", dialCode: "420" },
  { iso2: "IE", name: "Ireland", dialCode: "353" },
  { iso2: "NZ", name: "New Zealand", dialCode: "64" },
  { iso2: "ZA", name: "South Africa", dialCode: "27" },
  { iso2: "JP", name: "Japan", dialCode: "81" },
  { iso2: "KR", name: "South Korea", dialCode: "82" },
  { iso2: "CN", name: "China", dialCode: "86" },
  { iso2: "SG", name: "Singapore", dialCode: "65" },
  { iso2: "MY", name: "Malaysia", dialCode: "60" },
  { iso2: "PH", name: "Philippines", dialCode: "63" },
  { iso2: "ID", name: "Indonesia", dialCode: "62" },
  { iso2: "TH", name: "Thailand", dialCode: "66" },
  { iso2: "VN", name: "Vietnam", dialCode: "84" },
  { iso2: "TR", name: "Turkey", dialCode: "90" },
  { iso2: "SA", name: "Saudi Arabia", dialCode: "966" },
  { iso2: "AE", name: "United Arab Emirates", dialCode: "971" },
  { iso2: "IL", name: "Israel", dialCode: "972" },
  { iso2: "EG", name: "Egypt", dialCode: "20" },
  { iso2: "NG", name: "Nigeria", dialCode: "234" },
  { iso2: "KE", name: "Kenya", dialCode: "254" },
  { iso2: "PE", name: "Peru", dialCode: "51" },
  { iso2: "UY", name: "Uruguay", dialCode: "598" },
  { iso2: "EC", name: "Ecuador", dialCode: "593" },
  { iso2: "VE", name: "Venezuela", dialCode: "58" },
  { iso2: "BO", name: "Bolivia", dialCode: "591" },
  { iso2: "PY", name: "Paraguay", dialCode: "595" },
  { iso2: "CR", name: "Costa Rica", dialCode: "506" },
  { iso2: "PA", name: "Panama", dialCode: "507" },
  { iso2: "DO", name: "Dominican Republic", dialCode: "1" },
  { iso2: "PR", name: "Puerto Rico", dialCode: "1" },
  { iso2: "GR", name: "Greece", dialCode: "30" },
  { iso2: "RO", name: "Romania", dialCode: "40" },
  { iso2: "HU", name: "Hungary", dialCode: "36" },
  { iso2: "UA", name: "Ukraine", dialCode: "380" },
  { iso2: "RU", name: "Russia", dialCode: "7" },
];

export const PHONE_COUNTRIES: PhoneCountry[] = entries;

const byIso = new Map(PHONE_COUNTRIES.map((country) => [country.iso2, country]));

/** Countries shown first in the picker (research-app locales). */
export const PHONE_COUNTRY_PRIORITY = ["BR", "US", "ES", "PT", "GB", "DE", "FR", "MX"] as const;

export function getCountryByIso(iso2: string): PhoneCountry {
  return byIso.get(iso2.toUpperCase()) ?? byIso.get("BR")!;
}

export function defaultCountryIsoForLocale(locale: string): string {
  const normalized = locale.toLowerCase();
  if (normalized.startsWith("pt")) {
    return "BR";
  }
  if (normalized.startsWith("es")) {
    return "ES";
  }
  return "US";
}

export function phoneCountriesForSelect(): PhoneCountry[] {
  const prioritySet = new Set<string>(PHONE_COUNTRY_PRIORITY);
  const priority = PHONE_COUNTRY_PRIORITY.map((iso) => byIso.get(iso)).filter(Boolean) as PhoneCountry[];
  const rest = PHONE_COUNTRIES.filter((country) => !prioritySet.has(country.iso2)).sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  return [...priority, ...rest];
}
