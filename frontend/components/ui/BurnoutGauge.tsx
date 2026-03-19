'use client'

interface Props { risk: number; tier: string }

export default function BurnoutGauge({ risk, tier }: Props) {
  const pct = Math.round(risk * 100)
  const angle = -135 + (pct / 100) * 270
  const color = pct > 70 ? '#f43f5e' : pct > 45 ? '#f59e0b' : '#10b981'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-32 h-20 overflow-hidden">
        <svg viewBox="0 0 120 70" className="w-full h-full">
          {/* Track */}
          <path d="M 15 65 A 50 50 0 0 1 105 65" fill="none" stroke="#1c1c28" strokeWidth="10" strokeLinecap="round" />
          {/* Fill */}
          <path
            d="M 15 65 A 50 50 0 0 1 105 65"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${(pct / 100) * 157} 157`}
            style={{ filter: `drop-shadow(0 0 6px ${color}80)` }}
          />
          {/* Needle */}
          <line
            x1="60" y1="65"
            x2={60 + 38 * Math.cos((angle - 90) * Math.PI / 180)}
            y2={65 + 38 * Math.sin((angle - 90) * Math.PI / 180)}
            stroke={color} strokeWidth="2" strokeLinecap="round"
          />
          <circle cx="60" cy="65" r="4" fill={color} />
        </svg>
      </div>
      <div className="text-center">
        <p className="font-display font-bold text-2xl" style={{ color }}>{pct}%</p>
        <p className="text-xs font-mono" style={{ color }}>{tier}</p>
      </div>
    </div>
  )
}
