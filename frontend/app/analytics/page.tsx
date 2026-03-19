'use client'
import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { analyticsApi } from '@/lib/api'
import { getUser } from '@/lib/auth'
import ClusterBadge from '@/components/ui/ClusterBadge'
import { LineChart, Line, BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { RefreshCw, Loader2 } from 'lucide-react'

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null)
  const [scoring, setScoring] = useState(false)
  const user = getUser()

  const load = () => {
    if (user?.employee_id) {
      analyticsApi.getEmployee(user.employee_id, 12).then(r => setData(r.data)).catch(() => setData(null))
    }
  }

  useEffect(() => { load() }, [])

  const triggerScore = async () => {
    if (!user?.employee_id) return
    setScoring(true)
    try { await analyticsApi.triggerScore(user.employee_id); load() }
    catch {}
    finally { setScoring(false) }
  }

  const trend = data?.trend || []
  const current = data?.current_week
  const card = { background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }

  const radarData = current ? [
    { metric: 'Focus',        value: Math.round(Math.min((current.focus_blocks / 10) * 100, 100)) },
    { metric: 'Tasks',        value: Math.round(100 - (current.overdue_tasks ?? 0) * 100) },
    { metric: 'Meetings',     value: Math.round(100 - Math.min((current.meeting_hours / 40) * 100, 100)) },
    { metric: 'Rhythm',       value: Math.round(100 - (current.consecutive_meeting_ratio ?? 0) * 100) },
    { metric: 'Availability', value: Math.round(100 - (current.calendar_fragmentation ?? 0) * 100) },
  ] : []

  const ttStyle = { background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12, color: 'var(--text)' }

  return (
    <DashboardLayout title="Analytics">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            {current?.cluster_label && <ClusterBadge label={current.cluster_label} />}
          </div>
          <button onClick={triggerScore} disabled={scoring} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'var(--bg-3)', border: '1px solid var(--border)', borderRadius: 8,
            padding: '8px 14px', color: 'var(--text-sub)', fontSize: 12, cursor: 'pointer',
          }}>
            {scoring ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <RefreshCw size={13} />}
            Refresh Scores
          </button>
        </div>

        {!data ? (
          <div style={{ ...card, textAlign: 'center', padding: 60 }}>
            <p style={{ color: 'var(--text-sub)' }}>No data yet. Click Refresh Scores to generate analytics.</p>
          </div>
        ) : (
          <>
            {/* Top row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16 }}>
              {/* Burnout */}
              <div style={{ ...card, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2 }}>Burnout Risk</p>
                <div style={{ fontSize: 48, fontWeight: 700, color: current?.burnout_risk > 0.6 ? 'var(--rose)' : current?.burnout_risk > 0.3 ? 'var(--amber)' : 'var(--jade)' }}>
                  {Math.round((current?.burnout_risk ?? 0) * 100)}%
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-sub)' }}>
                  {current?.burnout_risk > 0.6 ? 'High Risk' : current?.burnout_risk > 0.3 ? 'Medium' : 'Low Risk'}
                </div>
                <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent-glow)' }}>
                  {current?.productivity_score?.toFixed(0) ?? '—'}<span style={{ fontSize: 13, color: 'var(--text-sub)' }}>/100</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-sub)' }}>Productivity Score</div>
              </div>

              {/* Radar */}
              <div style={card}>
                <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Work Pattern Radar</p>
                <ResponsiveContainer width="100%" height={200}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="var(--border)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--text-sub)', fontSize: 11 }} />
                    <Radar dataKey="value" stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.15} strokeWidth={1.5} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Productivity trend */}
            <div style={card}>
              <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>12-Week Productivity Score</p>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trend.map((w: any, i: number) => ({ week: `W${i + 1}`, score: w.productivity_score }))}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="week" tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={ttStyle} />
                  <Line dataKey="score" stroke="var(--accent)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} name="Score" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Meeting vs Focus */}
            <div style={card}>
              <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>Meeting Hours vs Focus Blocks</p>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={trend.map((w: any, i: number) => ({ week: `W${i + 1}`, meetings: w.meeting_hours ?? 0, focus: w.focus_blocks ?? 0 }))}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
                  <XAxis dataKey="week" tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-sub)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={ttStyle} />
                  <Bar dataKey="meetings" fill="var(--ember)" opacity={0.8} radius={[3, 3, 0, 0]} name="Meeting hrs" />
                  <Bar dataKey="focus" fill="var(--jade)" opacity={0.8} radius={[3, 3, 0, 0]} name="Focus blocks" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
