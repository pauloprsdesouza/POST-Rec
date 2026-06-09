import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function TrendLineChart({
  data,
  dataKey,
  label,
}: {
  data: Array<Record<string, string | number | null | undefined>>;
  dataKey: string;
  label: string;
}) {
  if (!data.length) {
    return null;
  }

  return (
    <div className="research-report__chart">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--postrec-border-subtle)" />
          <XAxis dataKey="week" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} name={label} stroke="var(--postrec-primary)" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function GroupedBarChart({
  data,
  keys,
  labels,
}: {
  data: Record<string, string | number>[];
  keys: string[];
  labels: Record<string, string>;
}) {
  if (!data.length) {
    return null;
  }

  const colors = ["var(--postrec-primary)", "var(--postrec-accent, #6366f1)", "#14b8a6"];

  return (
    <div className="research-report__chart">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--postrec-border-subtle)" />
          <XAxis dataKey="label" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          {keys.map((key, index) => (
            <Bar key={key} dataKey={key} name={labels[key] ?? key} fill={colors[index % colors.length]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DistributionBarChart({
  distribution,
  label,
}: {
  distribution: Record<string, number>;
  label: string;
}) {
  const data = Object.entries(distribution).map(([score, count]) => ({ score, count }));
  if (!data.some((item) => item.count > 0)) {
    return null;
  }

  return (
    <div className="research-report__mini-chart">
      <p className="research-report__mini-chart-label">{label}</p>
      <ResponsiveContainer width="100%" height={120}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <XAxis dataKey="score" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={28} />
          <Tooltip />
          <Bar dataKey="count" fill="var(--postrec-primary)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
