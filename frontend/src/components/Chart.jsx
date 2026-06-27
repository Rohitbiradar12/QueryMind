import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

export default function Chart({ chartType, chartData }) {
  if (chartType === 'none' || !chartData || chartData.length === 0) {
    return null
  }

  const axisColor = 'rgba(255, 255, 255, 0.4)'
  const gridColor = 'rgba(255, 255, 255, 0.06)'
  const barColor = '#3b82f6'
  const lineColor = '#3b82f6'

  const tooltipStyle = {
    background: '#0a0a0a',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '6px',
    color: '#fafafa',
    fontSize: '12px',
    fontFamily: 'Geist Mono, monospace',
  }

  if (chartType === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }} />
          <Bar dataKey="value" fill={barColor} radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'rgba(255, 255, 255, 0.1)' }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            dot={{ fill: lineColor, r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return null
}
