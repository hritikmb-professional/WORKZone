'use client'
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { meetingsApi } from '@/lib/api'
import { Upload, Mic, CheckCircle, Loader2, FileAudio, X, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'

type Meeting = {
  meeting_id: string; title: string; status: string;
  summary?: string; action_items?: any[]; decisions?: any[]
}

export default function MeetingsPage() {
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [expanded, setExpanded] = useState<string | null>(null)
  const [error, setError] = useState('')

  const onDrop = useCallback((files: File[]) => { if (files[0]) setFile(files[0]) }, [])
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'audio/*': ['.mp3', '.wav', '.mp4', '.flac', '.ogg', '.m4a'] }, maxFiles: 1,
  })

  const handleUpload = async () => {
    if (!file || !title) return
    setUploading(true); setError('')
    try {
      const fd = new FormData()
      fd.append('title', title); fd.append('file', file)
      const res = await meetingsApi.upload(fd)
      setMeetings(p => [{ meeting_id: res.data.meeting_id, title, status: 'processing' }, ...p])
      setFile(null); setTitle('')
      pollMeeting(res.data.meeting_id)
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Upload failed — AWS credentials required for full pipeline')
    } finally { setUploading(false) }
  }

  const pollMeeting = async (id: string) => {
    for (let i = 0; i < 40; i++) {
      await new Promise(r => setTimeout(r, 5000))
      try {
        const res = await meetingsApi.getSummary(id)
        if (res.data.status === 'ready') {
          setMeetings(p => p.map(m => m.meeting_id === id ? { ...m, ...res.data } : m))
          return
        }
      } catch {}
    }
  }

  const card = { background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 12 }

  return (
    <DashboardLayout title="Meeting Intelligence">
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 720 }}>

        {/* Upload card */}
        <div style={{ ...card, padding: 20 }}>
          <h3 style={{ color: 'var(--text)', fontWeight: 600, fontSize: 15, margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mic size={16} color="var(--accent-glow)" /> Upload Meeting Recording
          </h3>

          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Meeting title..."
            style={{ width: '100%', background: 'var(--bg-3)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 12px', fontSize: 13, color: 'var(--text)', outline: 'none', marginBottom: 12, boxSizing: 'border-box' as const }} />

          <div {...getRootProps()} style={{
            border: `2px dashed ${isDragActive ? 'var(--accent)' : 'var(--border)'}`,
            borderRadius: 12, padding: 32, textAlign: 'center', cursor: 'pointer',
            background: isDragActive ? 'rgba(99,102,241,0.05)' : 'var(--bg-3)',
            transition: 'all 0.2s',
          }}>
            <input {...getInputProps()} />
            {file ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
                <FileAudio size={20} color="var(--accent-glow)" />
                <span style={{ color: 'var(--text)', fontSize: 14 }}>{file.name}</span>
                <button onClick={e => { e.stopPropagation(); setFile(null) }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  <X size={14} color="var(--text-sub)" />
                </button>
              </div>
            ) : (
              <>
                <Upload size={24} color="var(--text-dim)" style={{ margin: '0 auto 8px' }} />
                <p style={{ color: 'var(--text-sub)', fontSize: 13 }}>Drag audio file or click to browse</p>
                <p style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>MP3, WAV, MP4, FLAC — max 500MB</p>
              </>
            )}
          </div>

          {error && (
            <div style={{ display: 'flex', gap: 8, background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.2)', borderRadius: 8, padding: '10px 12px', marginTop: 12 }}>
              <AlertCircle size={14} color="var(--rose)" style={{ flexShrink: 0, marginTop: 1 }} />
              <p style={{ color: 'var(--rose)', fontSize: 12, margin: 0 }}>{error}</p>
            </div>
          )}

          <button onClick={handleUpload} disabled={!file || !title || uploading} style={{
            marginTop: 12, width: '100%', background: 'var(--accent)', border: 'none',
            borderRadius: 8, padding: '11px', color: '#fff', fontSize: 13, fontWeight: 500,
            cursor: (!file || !title || uploading) ? 'not-allowed' : 'pointer',
            opacity: (!file || !title || uploading) ? 0.5 : 1,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
            {uploading ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Processing...</> : <><Upload size={14} /> Upload & Analyze</>}
          </button>
        </div>

        {/* Meeting list */}
        {meetings.length === 0 && (
          <div style={{ ...card, padding: 40, textAlign: 'center' }}>
            <Mic size={32} color="var(--text-dim)" style={{ margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--text-sub)', fontSize: 14 }}>No meetings yet</p>
            <p style={{ color: 'var(--text-dim)', fontSize: 12, marginTop: 4 }}>Upload a recording to get started</p>
          </div>
        )}

        {meetings.map(m => (
          <div key={m.meeting_id} style={card}>
            <button onClick={() => setExpanded(e => e === m.meeting_id ? null : m.meeting_id)}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', background: 'none', border: 'none', cursor: 'pointer' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {m.status === 'ready'
                  ? <CheckCircle size={16} color="var(--jade)" />
                  : <Loader2 size={16} color="var(--amber)" style={{ animation: 'spin 1s linear infinite' }} />}
                <span style={{ color: 'var(--text)', fontSize: 14, fontWeight: 500 }}>{m.title}</span>
                <span style={{ fontSize: 11, fontFamily: 'monospace', padding: '2px 8px', borderRadius: 99, background: m.status === 'ready' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)', color: m.status === 'ready' ? 'var(--jade)' : 'var(--amber)' }}>
                  {m.status}
                </span>
              </div>
              {expanded === m.meeting_id ? <ChevronUp size={16} color="var(--text-sub)" /> : <ChevronDown size={16} color="var(--text-sub)" />}
            </button>

            {expanded === m.meeting_id && m.summary && (
              <div style={{ padding: '0 20px 20px', borderTop: '1px solid var(--border)' }}>
                <div style={{ marginTop: 16 }}>
                  <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Summary</p>
                  <p style={{ color: 'var(--text)', fontSize: 13, lineHeight: 1.6 }}>{m.summary}</p>
                </div>

                {m.decisions && m.decisions.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Decisions</p>
                    {(m.decisions as string[]).map((d, i) => (
                      <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                        <span style={{ color: 'var(--accent)', marginTop: 2 }}>•</span>
                        <span style={{ color: 'var(--text-sub)', fontSize: 13 }}>{d}</span>
                      </div>
                    ))}
                  </div>
                )}

                {m.action_items && m.action_items.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <p style={{ color: 'var(--text-sub)', fontSize: 11, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: 2, marginBottom: 8 }}>Action Items</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {m.action_items.map((item: any) => (
                        <div key={item.item_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'var(--bg-3)', borderRadius: 8, border: `1px solid ${item.needs_review ? 'rgba(245,158,11,0.2)' : 'var(--border)'}` }}>
                          <div>
                            <p style={{ color: 'var(--text)', fontSize: 13, margin: 0 }}>{item.task}</p>
                            {item.due_date && <p style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 2 }}>Due: {item.due_date}</p>}
                          </div>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            {item.needs_review && <span style={{ fontSize: 10, background: 'rgba(245,158,11,0.1)', color: 'var(--amber)', padding: '2px 8px', borderRadius: 99, fontFamily: 'monospace' }}>Review</span>}
                            <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace' }}>{Math.round((item.confidence ?? 0) * 100)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </DashboardLayout>
  )
}
