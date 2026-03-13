import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export default function TrustScoreChart({ history, title = 'Trust Score History', dataKey = 'trust_score' }) {
  return (
    <div className="panel rounded-3xl p-6">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-xl font-semibold">{title}</h2>
          <p className="text-sm text-mist">Historical trust trend derived from Phantom Twin baseline comparisons.</p>
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={history} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="trustGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4be2c5" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#4be2c5" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(147, 185, 216, 0.12)" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tick={{ fill: '#93b9d8', fontSize: 12 }}
              tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            />
            <YAxis domain={[0, 100]} tick={{ fill: '#93b9d8', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: '#0f2332',
                border: '1px solid rgba(147, 185, 216, 0.2)',
                borderRadius: '16px',
              }}
              labelFormatter={(value) => new Date(value).toLocaleString()}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke="#4be2c5"
              strokeWidth={2.5}
              fill="url(#trustGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
