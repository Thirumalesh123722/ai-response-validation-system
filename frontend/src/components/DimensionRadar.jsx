import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'
export default function DimensionRadar({ relevance, accuracy, hallucination, completeness }) {
  const data = [
    { dimension: 'Relevance', score: relevance }, { dimension: 'Accuracy', score: accuracy },
    { dimension: 'Groundedness', score: hallucination }, { dimension: 'Completeness', score: completeness },
  ]
  return (
    <div className="rounded-lg border border-base-border card-surface p-5">
      <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-2">Dimension Profile</p>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer>
          <RadarChart data={data} outerRadius="70%">
            <PolarGrid stroke="#242B38" />
            <PolarAngleAxis dataKey="dimension" tick={{ fill: '#8891A3', fontSize: 12 }} />
            <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
            <Radar dataKey="score" stroke="#4FD1C5" fill="#4FD1C5" fillOpacity={0.25} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
