'use client'
import { Bell, Search, Sun, Moon } from 'lucide-react'
import { getUser } from '@/lib/auth'
import { useTheme } from '@/lib/theme'
import Image from 'next/image'
import { useState, useEffect } from 'react'

export default function Header({ title }: { title: string }) {
  const user = getUser()
  const { theme, toggle } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])

  const s = {
    header: {
      height: 56,
      display: 'flex' as const,
      alignItems: 'center' as const,
      justifyContent: 'space-between' as const,
      padding: '0 24px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--bg-1)',
      flexShrink: 0,
    },
    btn: {
      width: 34, height: 34, borderRadius: 8,
      background: 'var(--bg-3)', border: '1px solid var(--border)',
      cursor: 'pointer', display: 'flex' as const,
      alignItems: 'center' as const, justifyContent: 'center' as const,
    },
  }

  return (
    <header style={s.header}>
      <h1 style={{ color: 'var(--text)', fontWeight: 600, fontSize: 15 }}>{title}</h1>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {/* Search */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          background: 'var(--bg-3)', border: '1px solid var(--border)',
          borderRadius: 8, padding: '6px 12px', color: 'var(--text-sub)', fontSize: 12,
        }}>
          <Search size={13} color="var(--text-sub)" />
          <span>Search meetings...</span>
        </div>

        {/* Theme toggle */}
        {mounted && (
          <button onClick={toggle} style={s.btn} title="Toggle theme">
            {theme === 'dark'
              ? <Sun size={15} color="var(--text-sub)" />
              : <Moon size={15} color="var(--text-sub)" />}
          </button>
        )}

        {/* Bell */}
        <button style={s.btn}>
          <Bell size={15} color="var(--text-sub)" />
        </button>

        {/* Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--accent), var(--ember))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontSize: 12, fontWeight: 700, flexShrink: 0,
          }}>
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div>
            <div style={{ color: 'var(--text)', fontSize: 12, fontWeight: 500 }}>{user?.name || 'User'}</div>
            <div style={{ color: 'var(--text-sub)', fontSize: 10 }}>{user?.role || 'employee'}</div>
          </div>
        </div>
      </div>
    </header>
  )
}
