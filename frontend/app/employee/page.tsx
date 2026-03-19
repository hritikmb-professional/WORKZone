'use client'
import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { analyticsApi } from '@/lib/api'
import { getUser } from '@/lib/auth'
import ClusterBadge from '@/components/ui/ClusterBadge'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { RefreshCw, Loader2 } from 'lucide-react'

export default function EmployeePage() {
  const [data, setData] = useState<any>(null)
  const [scoring, setScoring] = useState(false)
  const [msg, setMsg] = useState('')
  const user = getUser()

  const load = () => {
    if (user?.employee_id) {
      analyticsApi.getEmployee(user.employee_id).then(r => setData(r.data)).catch(() => setData(null))
    }
  }

  useEffect(() => { load() }, [])

  const triggerScore = async () => {
    if (!user?.employee_id) return
    setScoring(true); setMsg('')
    try {
      await analyticsApi.triggerScore(user.employee_id)
      setMsg('Scoring complete')
      load()
    } catch {
      setMsg('Scoring failed — models may not be trained yet')
    } finally { setScoring(false) }
  }

  const current = data?.current_week
  const trend = data?.trend || []

  const card = { background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }

  return (
    <DashboardLayout title="My Profile">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 720 }}>

        {/* Profile card */}
        <div style={{ ...card, display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{
            width: 64, height: 64, borderRadius: 16, flexShrink: 0,
            background: 'linear-gradient(135deg, var(--accent), var(--ember))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 24, fontWeight: 700,
          }}>
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ color: 'var(--text)', fontWeight: 700, fontSize: 20, margin: 0 }}>{user?.name || 'Employee'}</h2>
            <p style={{ color: 'var(--text-sub)', fontSize: 13, margin: '4px 0 8px' }}>{user?.email || ''}</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' as const }}>
              <span style={{ fontSize: 11, background: 'rgba(99,102,241,0.1)', color: 'var(--accent-glow)', padding: '3px 10px', borderRadius: 99, fontFamily: 'monospace' }}>
                {user?.role || 'employee'}
              </span>
              {current?.cluster_label && <ClusterBadge label={current.cluster_label} />}
            </div>
          </div>

          {/* Burnout risk */}
          {current && (
            <div style={{ textAlign: 'center', flexShrink: 0 }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: current.burnout_risk > 0.6 ? 'var(--rose)' : current.burnout_risk > 0.3 ? 'var(--amber)' : 'var(--jade)' }}>
                {Math.round((current.burnout_risk ?? 0) * 100)}%
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-sub)', fontFamily: 'monospace' }}>Burnout Risk</div>
            </div>
          )}
        </div>

        {/* Trigger scoring */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button onClick={triggerScore} disabled={scoring} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'var(--accent)', border: 'none', borderRadius: 8,
            padding: '9px 18px', color: '#fff', fontSize: 13, fontWeight: 500,
            cursor: scoring ? 'not-allowed' : 'pointer', opacity: scoring ? 0.7 : 1,
          }}>
            {scoring ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <RefreshCw size={14} />}
            {scoring ? 'Scoring...' : 'Run ML Scoring'}
          </button>
          {msg && <span style={{ fontSize: 12, color: msg.includes('failed') ? 'var(--rose)' : 'var(--jade)' }}>{msg}</span>}
        </div>

        {/* This week stats */}
        {current ? (
          <div style={{ ...card }}>
            <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>This Week</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
              {[
                { label: 'Productivity',   value: `${current.productivity_score?.toFixed(0) ?? '—'}`, unit: '/100' },
                { label: 'Meeting Hours',  value: `${current.meeting_hours?.toFixed(1) ?? '—'}`,      unit: 'hrs'  },
                { label: 'Focus Blocks',   value: `${current.focus_blocks ?? '—'}`,                   unit: 'blocks' },
                { label: 'Consec. Ratio',  value: `${Math.round((current.consecutive_meeting_ratio ?? 0) * 100)}`, unit: '%' },
              ].map(({ label, value, unit }) => (
                <div key={label} style={{ background: 'var(--bg-3)', borderRadius: 10, padding: 14 }}>
                  <div style={{ color: 'var(--text-sub)', fontSize: 11, marginBottom: 6 }}>{label}</div>
                  <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: 22 }}>
                    {value}<span style={{ fontSize: 11, color: 'var(--text-dim)', marginLeft: 3 }}>{unit}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ ...card, textAlign: 'center', padding: 40 }}>
            <p style={{ color: 'var(--text-sub)', fontSize: 14, marginBottom: 8 }}>No analytics data yet</p>
            <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>Click "Run ML Scoring" above to generate your productivity metrics</p>
          </div>
        )}

        {/* Productivity timeline */}
        {trend.length > 0 && (
          <div style={card}>
            <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>Productivity Timeline</p>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trend.map((w: any, i: number) => ({ week: `W${i + 1}`, score: w.productivity_score, risk: Math.round((w.burnout_risk ?? 0) * 100) }))}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                <XAxis dataKey="week" tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12, color: 'var(--text)' }} />
                <Area dataKey="score" stroke="var(--accent)" strokeWidth={2} fill="url(#scoreGrad)" name="Productivity" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
