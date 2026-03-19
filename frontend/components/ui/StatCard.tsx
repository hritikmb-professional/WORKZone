import { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  sub?: string
  icon: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'accent' | 'jade' | 'ember' | 'rose' | 'amber'
  delay?: number
}

const ICON_COLORS: Record<string, string> = {
  accent: 'var(--accent-glow)',
  jade:   'var(--jade)',
  ember:  'var(--ember)',
  rose:   'var(--rose)',
  amber:  'var(--amber)',
}

export default function StatCard({ label, value, sub, icon: Icon, trend, trendValue, color = 'accent', delay = 0 }: Props) {
  return (
    <div style={{
      background: 'var(--card-bg)',
      border: '1px solid var(--border)',
      borderRadius: 12, padding: 16,
      animation: `fadeUp 0.5s ease ${delay}ms forwards`,
      opacity: 0,
      transition: 'transform 0.2s, box-shadow 0.2s',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: `color-mix(in srgb, ${ICON_COLORS[color]} 15%, transparent)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={17} color={ICON_COLORS[color]} />
        </div>
        {trendValue && (
          <span style={{
            fontSize: 11, fontFamily: 'monospace', padding: '2px 8px', borderRadius: 99,
            background: trend === 'up' ? 'rgba(16,185,129,0.1)' : trend === 'down' ? 'rgba(244,63,94,0.1)' : 'var(--bg-3)',
            color: trend === 'up' ? 'var(--jade)' : trend === 'down' ? 'var(--rose)' : 'var(--text-sub)',
          }}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
        )}
      </div>
      <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: 24, marginBottom: 2 }}>{value}</div>
      <div style={{ color: 'var(--text-sub)', fontSize: 12 }}>{label}</div>
      {sub && <div style={{ color: 'var(--text-dim)', fontSize: 10, marginTop: 4, fontFamily: 'monospace' }}>{sub}</div>}
    </div>
  )
}
