import { useState } from 'react'
import api from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

const DEMO_BRIEF =
  "We're planning a 2-day company offsite for 45 people in London. " +
  "We need a venue with meeting rooms and outdoor space, catering with " +
  "vegetarian and vegan options, a team-building activity (something creative, " +
  "not sports), and coach transport from central London. Budget is £25,000."

function parsePills(text) {
  const pills = []
  const headcount = text.match(/(\d+)\s*(?:people|persons?|guests?|delegates?|attendees?)/i)
  if (headcount) pills.push(`${headcount[1]} people`)

  const duration = text.match(/(\d+)[- ]?day/i)
  if (duration) pills.push(`${duration[1]} day${parseInt(duration[1]) > 1 ? 's' : ''}`)

  const cities = ['London','Manchester','Edinburgh','Birmingham','Bristol','Leeds',
    'Glasgow','Liverpool','Paris','Barcelona','Berlin','Amsterdam','Lisbon','Rome',
    'Europe','UK','Scotland']
  for (const city of cities) {
    if (new RegExp(`\\b${city}\\b`, 'i').test(text)) { pills.push(city); break }
  }

  const budget = text.match(/[£€$](\d[\d,]*(?:k)?)/i)
  if (budget) {
    let raw = budget[1].replace(/,/g, '')
    const val = raw.toLowerCase().endsWith('k') ? parseInt(raw) * 1000 : parseInt(raw)
    if (val >= 50000)      pills.push('Large budget')
    else if (val >= 15000) pills.push('Mid-range budget')
    else if (val > 0)      pills.push('Smaller budget')
  }

  return pills
}

export default function Step1Brief({ onComplete }) {
  const [briefText, setBriefText] = useState('')
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)

  const pills = parsePills(briefText)

  async function handleSubmit() {
    if (!briefText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.post('/api/route', { brief: briefText })
      onComplete(res.data, res.data.brief)
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Check the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner text="Parsing your brief and matching vendors..." />

  return (
    <div className="page-container narrow" style={{ textAlign: 'center' }}>
      {/* Badge + demo button row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{
          background: 'rgba(99,102,241,0.1)',
          border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 20, padding: '6px 16px',
          fontSize: 13, fontWeight: 500, color: 'var(--purple)',
        }}>
          * AI-Powered Event Planning
        </div>
        <button
          onClick={() => setBriefText(DEMO_BRIEF)}
          style={{
            background: 'transparent',
            border: '1px dashed var(--border)',
            borderRadius: 20, padding: '6px 14px',
            fontSize: 13, fontWeight: 500, color: 'var(--text-mid)',
            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
          }}
        >
          Try a demo brief
        </button>
      </div>

      {/* Headline */}
      <h1 style={{
        fontSize: 40, fontWeight: 800, color: 'var(--navy)',
        lineHeight: 1.15, marginBottom: 12,
      }}>
        Describe your{' '}
        <span style={{
          background: 'var(--gradient)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          perfect event
        </span>
      </h1>

      <p style={{ fontSize: 17, color: 'var(--text-mid)', marginBottom: 32 }}>
        Tell us everything about your company event &mdash;
        we'll find the ideal vendors for you.
      </p>

      {/* Input card */}
      <div style={{
        background: 'white', borderRadius: 20, padding: 28,
        boxShadow: '0 4px 24px rgba(13,27,62,0.08)',
      }}>
        <textarea
          value={briefText}
          onChange={e => setBriefText(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) handleSubmit() }}
          placeholder={
            "e.g. We're planning a 3-day team offsite for 50 people somewhere in the UK. " +
            "We need a venue with meeting rooms, outdoor team-building activities, catering for " +
            "various dietary needs, and evening entertainment. Budget is around £30,000..."
          }
          style={{
            width: '100%', minHeight: 160, border: 'none', outline: 'none',
            resize: 'none', fontSize: 16, fontFamily: 'Inter, sans-serif',
            color: 'var(--text-dark)', lineHeight: 1.6,
          }}
        />

        <div style={{ borderTop: '1px solid var(--border)', margin: '16px 0' }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, flex: 1 }}>
            {pills.length > 0
              ? pills.map(p => <span key={p} className="pill">{p}</span>)
              : <span style={{ fontSize: 13, color: 'var(--text-light)' }}>
                  Start typing your brief above...
                </span>
            }
          </div>
          <button
            className="btn-primary"
            onClick={handleSubmit}
            disabled={!briefText.trim()}
          >
            Find Vendors &rarr;
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          marginTop: 16, padding: '12px 16px', background: '#FEF2F2',
          border: '1px solid #FECACA', borderRadius: 10,
          color: '#DC2626', fontSize: 14, textAlign: 'left',
        }}>
          {error}
        </div>
      )}
    </div>
  )
}
