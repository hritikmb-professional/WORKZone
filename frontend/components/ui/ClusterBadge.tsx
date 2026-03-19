const STYLES: Record<string, { bg: string; color: string }> = {
  'Deep Focus Worker':          { bg: 'rgba(16,185,129,0.1)',  color: 'var(--jade)'        },
  'Balanced Performer':         { bg: 'rgba(99,102,241,0.1)',  color: 'var(--accent-glow)' },
  'Meeting-Heavy Contributor':  { bg: 'rgba(245,158,11,0.1)',  color: 'var(--amber)'       },
  'At-Risk Employee':           { bg: 'rgba(244,63,94,0.1)',   color: 'var(--rose)'        },
}

export default function ClusterBadge({ label }: { label: string }) {
  const s = STYLES[label] || { bg: 'var(--bg-3)', color: 'var(--text-sub)' }
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 99, fontSize: 11, fontWeight: 500,
      background: s.bg, color: s.color,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
      {label}
    </span>
  )
}
