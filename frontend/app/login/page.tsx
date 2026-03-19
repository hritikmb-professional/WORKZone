'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api'
import { setAuth, setPendingName } from '@/lib/auth'
import { Zap, Mail, Lock, ArrowRight, Loader2, User, Briefcase } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [form, setForm] = useState({ email: '', password: '' })
  const [name, setName] = useState('')
  const [role, setRole] = useState<'employee' | 'manager'>('employee')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [mode, setMode] = useState<'login' | 'register'>('login')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      if (mode === 'register') {
        setPendingName(name)
        await authApi.register({ ...form, name, role })
      }
      const res = await authApi.login(form)
      setAuth(res.data)
      // Update name in user object
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (mode === 'register') user.name = name
      localStorage.setItem('user', JSON.stringify(user))
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally { setLoading(false) }
  }

  const inp = {
    width: '100%', background: 'var(--bg-3)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '10px 12px 10px 36px', fontSize: 14,
    color: 'var(--text)', outline: 'none', boxSizing: 'border-box' as const,
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 380 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32, justifyContent: 'center' }}>
          <div style={{ width: 42, height: 42, borderRadius: 10, background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={22} color="#fff" />
          </div>
          <div>
            <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: 20 }}>WorkIntel</div>
            <div style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace' }}>AI Workplace Platform</div>
          </div>
        </div>

        <div style={{ background: 'var(--card-bg)', border: '1px solid var(--border-accent)', borderRadius: 16, padding: 28 }}>
          <h2 style={{ color: 'var(--text)', fontWeight: 600, fontSize: 20, margin: '0 0 4px 0' }}>
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </h2>
          <p style={{ color: 'var(--text-sub)', fontSize: 13, margin: '0 0 24px 0' }}>
            {mode === 'login' ? 'Sign in to your workspace' : 'Join your team workspace'}
          </p>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {mode === 'register' && (
              <>
                <div>
                  <label style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', display: 'block', marginBottom: 6 }}>Full Name</label>
                  <div style={{ position: 'relative' }}>
                    <User size={14} color="var(--text-sub)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                    <input type="text" value={name} onChange={e => setName(e.target.value)} required placeholder="John Doe" style={inp} />
                  </div>
                </div>

                {/* Role selector */}
                <div>
                  <label style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', display: 'block', marginBottom: 8 }}>Role</label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                    {(['employee', 'manager'] as const).map(r => (
                      <button key={r} type="button" onClick={() => setRole(r)} style={{
                        padding: '10px 12px', borderRadius: 8, border: `1px solid ${role === r ? 'var(--accent)' : 'var(--border)'}`,
                        background: role === r ? 'rgba(99,102,241,0.12)' : 'var(--bg-3)',
                        color: role === r ? 'var(--accent-glow)' : 'var(--text-sub)',
                        cursor: 'pointer', fontSize: 13, fontWeight: 500,
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                      }}>
                        {r === 'employee' ? <User size={14} /> : <Briefcase size={14} />}
                        {r.charAt(0).toUpperCase() + r.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            <div>
              <label style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', display: 'block', marginBottom: 6 }}>Email</label>
              <div style={{ position: 'relative' }}>
                <Mail size={14} color="var(--text-sub)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                <input type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} required placeholder="you@company.com" style={inp} />
              </div>
            </div>

            <div>
              <label style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', display: 'block', marginBottom: 6 }}>Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={14} color="var(--text-sub)" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                <input type="password" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} required placeholder="••••••••" style={inp} />
              </div>
            </div>

            {error && (
              <div style={{ background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', borderRadius: 8, padding: '8px 12px', color: 'var(--rose)', fontSize: 12 }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={loading} style={{
              background: 'var(--accent)', border: 'none', borderRadius: 8, padding: '11px 16px',
              color: '#fff', fontWeight: 500, fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, opacity: loading ? 0.6 : 1,
            }}>
              {loading
                ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />
                : <>{mode === 'login' ? 'Sign in' : 'Create account'}<ArrowRight size={14} /></>}
            </button>
          </form>

          <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-sub)', marginTop: 16, marginBottom: 0 }}>
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button onClick={() => { setMode(m => m === 'login' ? 'register' : 'login'); setError('') }}
              style={{ background: 'none', border: 'none', color: 'var(--accent-glow)', cursor: 'pointer', fontSize: 12 }}>
              {mode === 'login' ? 'Register' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
