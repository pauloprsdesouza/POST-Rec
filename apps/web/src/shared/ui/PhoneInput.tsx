import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Form } from "react-bootstrap";
import { useTranslation } from "react-i18next";

import { getCountryByIso, phoneCountriesForSelect } from "@/shared/constants/phoneCountries";
import {
  composePhone,
  defaultPhoneCountryIso,
  normalizeNationalNumber,
  parseStoredPhone,
} from "@/shared/utils/phoneNumber";
import { CountryFlag } from "@/shared/ui/CountryFlag";

function phoneDigits(value: string | null | undefined): string {
  return (value ?? "").replace(/\D/g, "");
}

interface PhoneInputProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  autoComplete?: string;
}

export function PhoneInput({
  id,
  value,
  onChange,
  placeholder,
  required = false,
  disabled = false,
  autoComplete = "tel-national",
}: PhoneInputProps) {
  const { t, i18n } = useTranslation();
  const menuId = useId();
  const pickerRef = useRef<HTMLDivElement>(null);
  const lastEmittedRef = useRef<string | null>(null);
  const fallbackIso = useMemo(() => defaultPhoneCountryIso(i18n.language), [i18n.language]);
  const countries = useMemo(() => phoneCountriesForSelect(), []);

  const [countryIso, setCountryIso] = useState(() => parseStoredPhone(value, fallbackIso).countryIso);
  const [nationalNumber, setNationalNumber] = useState(
    () => parseStoredPhone(value, fallbackIso).nationalNumber,
  );
  const [open, setOpen] = useState(false);

  const selectedCountry = getCountryByIso(countryIso);

  // Sync from parent only when value changes externally (e.g. profile load).
  useEffect(() => {
    if (phoneDigits(value) === phoneDigits(lastEmittedRef.current)) {
      return;
    }
    const parsed = parseStoredPhone(value, fallbackIso);
    setCountryIso(parsed.countryIso);
    setNationalNumber(parsed.nationalNumber);
  }, [value, fallbackIso]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const handlePointerDown = (event: MouseEvent) => {
      if (!pickerRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [open]);

  const emitChange = (iso: string, national: string) => {
    const composed = composePhone(iso, national);
    lastEmittedRef.current = composed;
    onChange(composed);
  };

  const selectCountry = (iso: string) => {
    const normalized = normalizeNationalNumber(iso, nationalNumber);
    setCountryIso(iso);
    setNationalNumber(normalized);
    emitChange(iso, normalized);
    setOpen(false);
  };

  return (
    <div className="phone-input">
      <div className="phone-input__picker" ref={pickerRef}>
        <button
          type="button"
          className="phone-input__country-trigger"
          disabled={disabled}
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={menuId}
          aria-label={t("auth.countryCode")}
          onClick={() => setOpen((current) => !current)}
        >
          <CountryFlag iso2={selectedCountry.iso2} size={22} className="phone-input__flag" />
          <span className="phone-input__dial-code">+{selectedCountry.dialCode}</span>
          <span className="phone-input__chevron" aria-hidden>
            {open ? "▴" : "▾"}
          </span>
        </button>

        {open ? (
          <div className="phone-input__menu" id={menuId} role="listbox" aria-label={t("auth.countryCode")}>
            {countries.map((country) => {
              const selected = country.iso2 === countryIso;
              return (
                <button
                  key={country.iso2}
                  type="button"
                  role="option"
                  aria-selected={selected}
                  className={`phone-input__option ${selected ? "phone-input__option--selected" : ""}`}
                  onClick={() => selectCountry(country.iso2)}
                >
                  <CountryFlag iso2={country.iso2} size={20} className="phone-input__flag" />
                  <span className="phone-input__option-name">{country.name}</span>
                  <span className="phone-input__option-code">+{country.dialCode}</span>
                </button>
              );
            })}
          </div>
        ) : null}
      </div>

      <Form.Control
        id={id}
        type="tel"
        className="phone-input__number"
        inputMode="tel"
        value={nationalNumber}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete}
        onChange={(event) => {
          const normalized = normalizeNationalNumber(countryIso, event.target.value);
          setNationalNumber(normalized);
          emitChange(countryIso, normalized);
        }}
      />
    </div>
  );
}
