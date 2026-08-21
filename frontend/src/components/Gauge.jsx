const COLOR_MAP = { teal: '#4FD1C5', amber: '#F5A623', red: '#E5484D', violet: '#8B7FD1', blue: '#5B8DEF' }
function colorForScore(score) { if (score >= 75) return COLOR_MAP.teal; if (score >= 50) return COLOR_MAP.amber; return COLOR_MAP.red }
function Ticks({ radius, cx, cy }) {
  const ticks = []
  for (let i = 0; i <= 10; i++) {
    const angle = Math.PI - (i / 10) * Math.PI
    const outer = radius + 9, inner = radius + 3
    const x1 = cx + inner * Math.cos(angle), y1 = cy - inner * Math.sin(angle)
    const x2 = cx + outer * Math.cos(angle), y2 = cy - outer * Math.sin(angle)
    ticks.push(<line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#242B38" strokeWidth={1.5} />)
  }
  return <>{ticks}</>
}
export default function Gauge({ score = 0, size = 120, strokeWidth = 10, accent }) {
  const clamped = Math.max(0, Math.min(100, score))
  const radius = (size - strokeWidth) / 2 - 10
  const cx = size / 2, cy = size / 2
  const circumference = Math.PI * radius
  const offset = circumference * (1 - clamped / 100)
  const color = accent ? COLOR_MAP[accent] : colorForScore(clamped)
  return (
    <div className="relative" style={{ width: size, height: size / 1.7 }}>
      <svg width={size} height={size / 1.7} viewBox={`0 0 ${size} ${size / 1.7}`}>
        <Ticks radius={radius} cx={cx} cy={cy} />
        <path d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`} fill="none" stroke="#1B212D" strokeWidth={strokeWidth} strokeLinecap="round" />
        <path d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)', filter: `drop-shadow(0 0 6px ${color}66)` }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-end pb-0.5">
        <span className="font-mono text-2xl font-semibold" style={{ color }}>{Math.round(clamped)}</span>
      </div>
    </div>
  )
}
