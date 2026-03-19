'use client'
import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import StatCard from '@/components/ui/StatCard'
import ClusterBadge from '@/components/ui/ClusterBadge'
import { Mic, BarChart3, AlertTriangle, Clock } from 'lucide-react'
import { analyticsApi } from '@/lib/api'
import { getUser } from '@/lib/auth'

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<any>(null)
  const user = getUser()

  useEffect(() => {
    if (user?.employee_id) {
      analyticsApi.getEmployee(user.employee_id).then(r => setAnalytics(r.data)).catch(() => {})
    }
  }, [])

  const current = analytics?.current_week
  const trend = analytics?.trend || []

  return (
    <DashboardLayout title="Dashboard">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 style={{ color: 'var(--text)', fontWeight: 700, fontSize: 24 }}>
              Good morning{user?.name ? `, ${user.name.split(' ')[0]}` : ''}
            </h2>
            <p style={{ color: 'var(--text-sub)', fontSize: 13, marginTop: 4 }}>Your workplace intelligence summary</p>
          </div>
          {current?.cluster_label && <ClusterBadge label={current.cluster_label} />}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <StatCard label="Productivity Score" value={current?.productivity_score?.toFixed(0) ?? '—'} sub="This week" icon={BarChart3} color="accent" trend="up" trendValue="+4%" delay={0} />
          <StatCard label="Meeting Hours" value={current?.meeting_hours?.toFixed(1) ?? '—'} sub="hrs this week" icon={Mic} color="ember" delay={50} />
          <StatCard label="Focus Blocks" value={current?.focus_blocks ?? '—'} sub="90+ min uninterrupted" icon={Clock} color="jade" delay={100} />
          <StatCard label="Consecutive Meetings" value={current ? `${Math.round(current.consecutive_meeting_ratio * 100)}%` : '—'} sub="back-to-back ratio" icon={AlertTriangle} color={current?.consecutive_meeting_ratio > 0.5 ? 'rose' : 'amber'} delay={150} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 16 }}>
          <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-accent)', borderRadius: 12, padding: 20, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
            <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2 }}>Burnout Risk</p>
            {current ? (
              <>
                <div style={{ fontSize: 40, fontWeight: 700, color: current.burnout_risk > 0.6 ? 'var(--rose)' : current.burnout_risk > 0.3 ? 'var(--amber)' : 'var(--jade)' }}>
                  {Math.round((current.burnout_risk ?? 0) * 100)}%
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-sub)' }}>
                  {current.burnout_risk > 0.6 ? 'High Risk' : current.burnout_risk > 0.3 ? 'Medium' : 'Low Risk'}
                </div>
              </>
            ) : <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No data yet</p>}
          </div>

          <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }}>
            <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>12-Week Productivity</p>
            {trend.length > 0 ? (
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 80 }}>
                {trend.map((w: any, i: number) => (
                  <div key={i} title={`Week ${i + 1}: ${w.productivity_score?.toFixed(0)}`} style={{
                    flex: 1, borderRadius: '2px 2px 0 0',
                    background: 'var(--accent)',
                    height: `${((w.productivity_score ?? 0) / 100) * 80}px`,
                    opacity: 0.6,
                  }} />
                ))}
              </div>
            ) : (
              <div style={{ height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>Run analytics scoring to see trend</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
