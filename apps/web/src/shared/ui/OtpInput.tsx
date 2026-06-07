import type { ClipboardEvent, KeyboardEvent } from "react";
import { useEffect, useRef } from "react";

const DEFAULT_LENGTH = 6;

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  length?: number;
  disabled?: boolean;
  autoFocus?: boolean;
  "aria-label": string;
  id?: string;
}

function sanitizeDigits(raw: string, maxLength: number): string {
  return raw.replace(/\D/g, "").slice(0, maxLength);
}

export function OtpInput({
  value,
  onChange,
  length = DEFAULT_LENGTH,
  disabled = false,
  autoFocus = false,
  "aria-label": ariaLabel,
  id = "otp-input",
}: OtpInputProps) {
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const digits = Array.from({ length }, (_, index) => value[index] ?? "");

  const focusCell = (index: number) => {
    const clamped = Math.max(0, Math.min(index, length - 1));
    const input = inputRefs.current[clamped];
    if (input) {
      input.focus();
      input.select();
    }
  };

  useEffect(() => {
    if (autoFocus && !disabled) {
      focusCell(0);
    }
  }, [autoFocus, disabled]);

  const applyDigits = (nextDigits: string[], focusAt?: number) => {
    onChange(nextDigits.join("").slice(0, length));
    if (focusAt !== undefined) {
      focusCell(focusAt);
    }
  };

  const handleCellChange = (index: number, raw: string) => {
    const incoming = sanitizeDigits(raw, length);

    if (incoming.length > 1) {
      const merged = [...digits];
      incoming.split("").forEach((digit, offset) => {
        const target = index + offset;
        if (target < length) {
          merged[target] = digit;
        }
      });
      const nextIndex = Math.min(index + incoming.length, length - 1);
      applyDigits(merged, nextIndex);
      return;
    }

    const merged = [...digits];
    merged[index] = incoming;
    applyDigits(merged, incoming && index < length - 1 ? index + 1 : index);
  };

  const handleKeyDown = (index: number, event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace") {
      event.preventDefault();
      const merged = [...digits];

      if (merged[index]) {
        merged[index] = "";
        applyDigits(merged, index);
        return;
      }

      if (index > 0) {
        merged[index - 1] = "";
        applyDigits(merged, index - 1);
      }
      return;
    }

    if (event.key === "ArrowLeft") {
      event.preventDefault();
      focusCell(index - 1);
      return;
    }

    if (event.key === "ArrowRight") {
      event.preventDefault();
      focusCell(index + 1);
    }
  };

  const handlePaste = (event: ClipboardEvent<HTMLInputElement>) => {
    event.preventDefault();
    const pasted = sanitizeDigits(event.clipboardData.getData("text"), length);
    if (!pasted) {
      return;
    }

    const merged = [...digits];
    pasted.split("").forEach((digit, offset) => {
      if (offset < length) {
        merged[offset] = digit;
      }
    });
    applyDigits(merged, Math.min(pasted.length, length) - 1);
  };

  const handleAutofill = (raw: string) => {
    const sanitized = sanitizeDigits(raw, length);
    if (sanitized === value) {
      return;
    }
    onChange(sanitized);
    if (sanitized.length > 0) {
      focusCell(Math.min(sanitized.length, length) - 1);
    }
  };

  return (
    <div className="otp-input-group" role="group" aria-label={ariaLabel}>
      <input
        id={id}
        type="text"
        inputMode="numeric"
        autoComplete="one-time-code"
        className="otp-input-group__autofill"
        tabIndex={-1}
        aria-hidden
        value={value}
        disabled={disabled}
        onChange={(event) => handleAutofill(event.target.value)}
      />
      <div className="otp-input-group__cells">
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(element) => {
              inputRefs.current[index] = element;
            }}
            type="text"
            inputMode="numeric"
            autoComplete="off"
            aria-label={`${ariaLabel} ${index + 1} / ${length}`}
            className="otp-input-group__cell"
            value={digit}
            disabled={disabled}
            maxLength={1}
            onChange={(event) => handleCellChange(index, event.target.value)}
            onKeyDown={(event) => handleKeyDown(index, event)}
            onPaste={handlePaste}
            onFocus={(event) => event.currentTarget.select()}
          />
        ))}
      </div>
    </div>
  );
}
