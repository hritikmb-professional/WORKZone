'use client'
import { useEffect, useState } from 'react'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { analyticsApi } from '@/lib/api'
import { getUser } from '@/lib/auth'
import ClusterBadge from '@/components/ui/ClusterBadge'
import { Users, AlertTriangle, BarChart3, Activity, RefreshCw, Loader2 } from 'lucide-react'

export default function ManagerPage() {
  const [insights, setInsights] = useState<any>(null)
  const [error, setError] = useState('')
  const [scoring, setScoring] = useState(false)
  const user = getUser()

  const load = () => {
    if (!user?.team_id) { setError('No team assigned. Register with manager role and a team_id.'); return }
    analyticsApi.getTeam(user.team_id).then(r => setInsights(r.data)).catch(e => {
      setError(e.response?.data?.detail || 'No team data yet — trigger scoring for team members first.')
    })
  }

  useEffect(() => { load() }, [])

  const card = { background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12, padding: 20 }
  const statBox = (label: string, value: any, color: string) => (
    <div style={{ background: 'var(--bg-3)', borderRadius: 10, padding: 16, flex: 1 }}>
      <div style={{ color: 'var(--text-sub)', fontSize: 11, marginBottom: 6 }}>{label}</div>
      <div style={{ color, fontWeight: 700, fontSize: 26 }}>{value ?? '—'}</div>
    </div>
  )

  return (
    <DashboardLayout title="Team Insights">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {error && (
          <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 10, padding: '12px 16px', color: 'var(--amber)', fontSize: 13 }}>
            {error}
            <p style={{ fontSize: 11, marginTop: 6, color: 'var(--text-sub)' }}>
              Tip: Register employees with the same team_id as your manager account, then trigger scoring on their profiles.
            </p>
          </div>
        )}

        {insights && (
          <>
            {/* Stats row */}
            <div style={{ display: 'flex', gap: 12 }}>
              {statBox('Team Size', insights.team_size, 'var(--accent-glow)')}
              {statBox('Avg Productivity', insights.avg_productivity_score, 'var(--jade)')}
              {statBox('At-Risk Members', insights.at_risk_count, insights.at_risk_count > 0 ? 'var(--rose)' : 'var(--jade)')}
              {statBox('Avg Burnout Risk', `${Math.round((insights.avg_burnout_risk ?? 0) * 100)}%`, 'var(--amber)')}
            </div>

            {/* Cluster distribution */}
            <div style={card}>
              <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>Team Cluster Distribution</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {Object.entries(insights.cluster_distribution || {}).map(([label, count]: any) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 180, flexShrink: 0 }}><ClusterBadge label={label} /></div>
                    <div style={{ flex: 1, background: 'var(--bg-3)', borderRadius: 99, height: 8, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 99, background: 'var(--accent)',
                        width: `${(count / insights.team_size) * 100}%`,
                        transition: 'width 0.7s ease',
                      }} />
                    </div>
                    <span style={{ color: 'var(--text-sub)', fontSize: 12, fontFamily: 'monospace', width: 30, textAlign: 'right' }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* At-risk list */}
            {insights.at_risk_employees?.length > 0 && (
              <div style={{ ...card, border: '1px solid rgba(244,63,94,0.2)' }}>
                <p style={{ color: 'var(--rose)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 16 }}>
                  At-Risk Employees ({insights.at_risk_count})
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {insights.at_risk_employees.map((emp: any) => (
                    <div key={emp.employee_id} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 16px', background: 'rgba(244,63,94,0.05)',
                      border: '1px solid rgba(244,63,94,0.12)', borderRadius: 10,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 36, height: 36, borderRadius: '50%',
                          background: 'rgba(244,63,94,0.15)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          color: 'var(--rose)', fontSize: 12, fontWeight: 700,
                        }}>
                          {emp.employee_id.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p style={{ color: 'var(--text)', fontSize: 13, fontFamily: 'monospace', margin: 0 }}>{emp.employee_id.slice(0, 8)}...</p>
                          <ClusterBadge label={emp.cluster} />
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ color: 'var(--rose)', fontWeight: 700, fontSize: 18 }}>{Math.round(emp.burnout_risk * 100)}%</div>
                        <div style={{ color: 'var(--text-dim)', fontSize: 11 }}>burnout risk</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {insights.at_risk_employees?.length === 0 && (
              <div style={{ ...card, textAlign: 'center', padding: 32 }}>
                <div style={{ color: 'var(--jade)', fontSize: 32, marginBottom: 8 }}>✓</div>
                <p style={{ color: 'var(--text-sub)', fontSize: 14 }}>No at-risk employees this week</p>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  )
}
