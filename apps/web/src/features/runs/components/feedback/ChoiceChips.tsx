interface ChoiceOption<T extends string | boolean> {
  value: T;
  label: string;
}

interface ChoiceChipsProps<T extends string | boolean> {
  options: ChoiceOption<T>[];
  value: T | null;
  disabled?: boolean;
  ariaLabel: string;
  onChange: (value: T) => void;
}

export function ChoiceChips<T extends string | boolean>({
  options,
  value,
  disabled = false,
  ariaLabel,
  onChange,
}: ChoiceChipsProps<T>) {
  return (
    <div className="choice-chips" role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const active = value === option.value;

        return (
          <button
            key={String(option.value)}
            type="button"
            className={`choice-chips__btn ${active ? "choice-chips__btn--active" : ""}`}
            disabled={disabled}
            aria-pressed={active}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
