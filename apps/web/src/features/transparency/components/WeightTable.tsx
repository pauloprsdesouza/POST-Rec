import { useTranslation } from "react-i18next";

interface WeightRow {
  key: string;
  weight: number;
  labelKey?: string;
}

interface WeightTableProps {
  rows: readonly WeightRow[];
  labelPrefix: string;
}

export function WeightTable({ rows, labelPrefix }: WeightTableProps) {
  const { t } = useTranslation();

  return (
    <table className="weight-table">
      <thead>
        <tr>
          <th scope="col">{t("transparency.weights.dimension")}</th>
          <th scope="col">{t("transparency.weights.weight")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.key}>
            <td>
              {t(`${labelPrefix}.${row.key}`, {
                defaultValue: row.key.replace(/_/g, " "),
              })}
            </td>
            <td>{Math.round(row.weight * 100)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
