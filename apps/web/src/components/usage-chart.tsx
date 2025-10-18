import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format } from "date-fns";

interface Reading {
  ts: string;
  kw: number;
}

interface UsageChartProps {
  readings: Reading[];
}

export function UsageChart({ readings }: UsageChartProps) {
  const chartData = readings
    .slice()
    .reverse()
    .map((r) => ({
      time: format(new Date(r.ts), "HH:mm"),
      kw: r.kw,
    }));

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Energy Usage (Last 24 Hours)</h2>
        <div className="text-sm text-gray-500">
          {readings.length} data points
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            tickFormatter={(value, index) => index % 10 === 0 ? value : ""}
          />
          <YAxis
            label={{ value: "kW", angle: -90, position: "insideLeft" }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number) => [`${value.toFixed(2)} kW`, "Power"]}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Line
            type="monotone"
            dataKey="kw"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}