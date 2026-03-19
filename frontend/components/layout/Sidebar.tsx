'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { LayoutDashboard, Mic, BarChart3, User, Users, LogOut, Zap, ChevronLeft, ChevronRight } from 'lucide-react'
import { clearAuth } from '@/lib/auth'
import Image from 'next/image'
import { useEffect, useState as useStateFS } from 'react'

const NAV = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/meetings',  icon: Mic,             label: 'Meetings'  },
  { href: '/analytics', icon: BarChart3,        label: 'Analytics' },
  { href: '/employee',  icon: User,             label: 'Profile'   },
  { href: '/manager',   icon: Users,            label: 'Team'      },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [hasLogo, setHasLogo] = useState(false)
  const pathname = usePathname()
  const router = useRouter()

  useEffect(() => {
    fetch('/logo.png', { method: 'HEAD' })
      .then(r => { if (r.ok) setHasLogo(true) })
      .catch(() => {})
  }, [])

  return (
    <aside style={{
      width: collapsed ? 56 : 220,
      minWidth: collapsed ? 56 : 220,
      height: '100vh',
      background: 'var(--bg-1)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      transition: 'width 0.25s ease',
      position: 'relative',
      flexShrink: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: hasLogo ? 'transparent' : 'var(--accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, overflow: 'hidden',
          animation: 'pulseGlow 2s ease-in-out infinite',
        }}>
          {hasLogo
            ? <Image src="/logo.png" alt="Logo" width={32} height={32} style={{ objectFit: 'contain' }} />
            : <Zap size={16} color="#fff" />}
        </div>
        {!collapsed && (
          <div>
            <div style={{ color: 'var(--text)', fontWeight: 700, fontSize: 14 }}>WorkIntel</div>
            <div style={{ color: 'var(--text-dim)', fontSize: 10, fontFamily: 'monospace' }}>AI Platform</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href)
          return (
            <Link key={href} href={href} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '9px 12px', borderRadius: 8, textDecoration: 'none',
              background: active ? 'rgba(99,102,241,0.12)' : 'transparent',
              border: active ? '1px solid var(--border-accent)' : '1px solid transparent',
              color: active ? 'var(--accent-glow)' : 'var(--text-sub)',
              fontSize: 13, fontWeight: 500,
              transition: 'all 0.15s ease',
            }}>
              <Icon size={16} />
              {!collapsed && <span>{label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div style={{ padding: '8px', borderTop: '1px solid var(--border)' }}>
        <button onClick={() => { clearAuth(); router.push('/login') }} style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 10,
          padding: '9px 12px', borderRadius: 8, border: 'none', cursor: 'pointer',
          background: 'transparent', color: 'var(--text-sub)', fontSize: 13,
        }}>
          <LogOut size={16} color="var(--text-sub)" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button onClick={() => setCollapsed(!collapsed)} style={{
        position: 'absolute', right: -12, top: '50%', transform: 'translateY(-50%)',
        width: 24, height: 24, borderRadius: '50%',
        background: 'var(--bg-3)', border: '1px solid var(--border)',
        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10,
      }}>
        {collapsed
          ? <ChevronRight size={12} color="var(--text-sub)" />
          : <ChevronLeft size={12} color="var(--text-sub)" />}
      </button>
    </aside>
  )
}
