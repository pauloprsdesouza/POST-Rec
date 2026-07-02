import { useTranslation } from "react-i18next";

import { NOTATION_SYMBOLS } from "@/features/transparency/constants/transparencyModel";

export function NotationTable() {
  const { t } = useTranslation();

  return (
    <div className="transparency-table-wrap">
      <table className="transparency-table">
        <thead>
          <tr>
            <th scope="col">{t("transparency.notation.colSymbol")}</th>
            <th scope="col">{t("transparency.notation.colMeaning")}</th>
          </tr>
        </thead>
        <tbody>
          {NOTATION_SYMBOLS.map((row) => (
            <tr key={row.key}>
              <td>
                <code>{row.symbol}</code>
              </td>
              <td>{t(`transparency.notation.symbols.${row.key}`)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
