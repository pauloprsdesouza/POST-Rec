import { useTranslation } from "react-i18next";

interface RunsSearchBarProps {
  value: string;
  loading?: boolean;
  onChange: (value: string) => void;
  onClear: () => void;
}

export function RunsSearchBar({ value, loading = false, onChange, onClear }: RunsSearchBarProps) {
  const { t } = useTranslation();

  return (
    <div className="runs-search">
      <label className="visually-hidden" htmlFor="runs-search-input">
        {t("runs.searchLabel")}
      </label>
      <div className="runs-search__field">
        <span className="runs-search__icon" aria-hidden>
          ⌕
        </span>
        <input
          id="runs-search-input"
          type="search"
          className="runs-search__input"
          value={value}
          placeholder={t("runs.searchPlaceholder")}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => onChange(event.target.value)}
        />
        {loading ? (
          <span className="runs-search__spinner" role="status" aria-label={t("runs.searching")} />
        ) : null}
        {value && !loading ? (
          <button type="button" className="runs-search__clear" onClick={onClear} aria-label={t("runs.searchClear")}>
            ×
          </button>
        ) : null}
      </div>
    </div>
  );
}
