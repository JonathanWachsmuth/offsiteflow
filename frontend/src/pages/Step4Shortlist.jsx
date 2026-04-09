import { useEffect, useState } from 'react'
import axios from 'axios'
import LoadingSpinner from '../components/LoadingSpinner'

function IconPeople() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
      stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  )
}

function IconCalendar() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
      stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
  )
}

function StatBox({ icon, label, value }) {
  return (
    <div style={{
      background: '#F5F7FF', borderRadius: 12, padding: '16px 20px',
      flex: 1, textAlign: 'center', minWidth: 130,
    }}>
      <div style={{ display: 'flex', justifyContent: 'center' }}>{icon}</div>
      <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 8 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--navy)', marginTop: 4 }}>{value}</div>
    </div>
  )
}

export default function Step4Shortlist({ brief, selectedVendorIds, onBack, onRestart }) {
  const [shortlist, setShortlist] = useState(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const res = await axios.post('/api/shortlist', {
          brief,
          selected_vendor_ids: selectedVendorIds,
        })
        setShortlist(res.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to build shortlist.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <LoadingSpinner text="Analysing vendor responses..." />

  if (error) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center' }}>
        <div style={{
          padding: '16px 20px', background: '#FEF2F2',
          border: '1px solid #FECACA', borderRadius: 12,
          color: '#DC2626', fontSize: 14,
        }}>
          {error}
        </div>
        <button className="btn-ghost" onClick={onBack} style={{ marginTop: 16 }}>
          &larr; Back
        </button>
      </div>
    )
  }

  const top     = shortlist?.shortlist?.[0]
  const summary = shortlist?.budget_summary || {}

  if (!top) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center' }}>
        <p style={{ color: 'var(--text-mid)' }}>No shortlist results available.</p>
        <button className="btn-ghost" onClick={onBack} style={{ marginTop: 16 }}>
          &larr; Back
        </button>
      </div>
    )
  }

  const matchScore = top.score ? Math.round(top.score * 100) : '—'
  const totalVAT   = top.total_inc_vat
    ? `£${Math.round(top.total_inc_vat).toLocaleString()}`
    : '—'
  const perHead    = top.total_per_head
    ? `£${Math.round(top.total_per_head).toLocaleString()}`
    : '—'

  const inclusions = top.inclusions?.length > 0
    ? top.inclusions
    : Object.entries(top.components || {})
        .filter(([, v]) => v === 'included')
        .map(([k]) => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()))

  return (
    <div className="page-container narrow">
      {/* Badge */}
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{
          display: 'inline-block',
          background: 'rgba(234,179,8,0.1)',
          border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: 20, padding: '6px 16px',
          fontSize: 13, fontWeight: 500, color: 'var(--warning)',
          marginBottom: 20,
        }}>
          Best Match Found
        </div>
        <h2 style={{ fontSize: 36, fontWeight: 800, color: 'var(--navy)', lineHeight: 1.15 }}>
          Your ideal event package
        </h2>
        <p style={{ fontSize: 16, color: 'var(--text-mid)', marginTop: 10 }}>
          Based on your requirements and vendor responses,
          here's our top recommendation.
        </p>
      </div>

      {/* Main card */}
      <div style={{
        background: 'white', borderRadius: 20, padding: 32,
        boxShadow: '0 4px 32px rgba(13,27,62,0.10)',
      }}>
        {/* Top row */}
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          alignItems: 'flex-start', flexWrap: 'wrap', gap: 16,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--navy)' }}>
                {top.vendor_name}
              </span>
              <span className="pill-gradient">{matchScore}% match</span>
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-mid)', marginTop: 6 }}>
              {brief?.city || ''}
              {top.category && ` · ${top.category.charAt(0).toUpperCase() + top.category.slice(1)}`}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--navy)', lineHeight: 1.1 }}>
              {totalVAT}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-light)' }}>total estimate</div>
          </div>
        </div>

        {/* Stat boxes */}
        <div style={{ display: 'flex', gap: 12, marginTop: 20, flexWrap: 'wrap' }}>
          <StatBox
            icon={<IconPeople />}
            label="Capacity"
            value={`${brief?.headcount || '—'} guests`}
          />
          <StatBox
            icon={<IconCalendar />}
            label="Date"
            value={brief?.date_start || '—'}
          />
          <StatBox
            icon={<span style={{ fontSize: 20, fontWeight: 700, color: '#6366F1' }}>£</span>}
            label="Per person"
            value={perHead}
          />
        </div>

        {/* What's included */}
        <div style={{ marginTop: 24 }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--navy)', marginBottom: 12 }}>
            * What's included
          </div>
          {inclusions.length > 0 ? (
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr',
              gap: '8px 16px',
            }}>
              {inclusions.map(item => (
                <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                    background: 'var(--gradient)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontSize: 10, fontWeight: 700,
                  }}>
                    &#10003;
                  </div>
                  <span style={{ fontSize: 14, color: '#374151' }}>{item}</span>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: 14, color: 'var(--text-light)' }}>
              Details pending vendor confirmation.
            </p>
          )}
        </div>

        {/* Recommendation */}
        {shortlist?.recommendation && (
          <div style={{
            marginTop: 20, padding: '14px 18px',
            background: '#F5F7FF', borderRadius: 10,
            fontSize: 14, color: '#374151', lineHeight: 1.6,
          }}>
            {shortlist.recommendation}
          </div>
        )}

        {/* Budget summary */}
        <div style={{
          marginTop: 20, padding: '14px 18px',
          background: summary.within_budget ? '#F0FDF4' : '#FEF2F2',
          borderRadius: 10, fontSize: 14,
          border: `1px solid ${summary.within_budget ? '#BBF7D0' : '#FECACA'}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--text-mid)' }}>
              Budget: £{(summary.budget || 0).toLocaleString()}
            </span>
            <span style={{ color: 'var(--text-mid)' }}>
              Total: £{Math.round(summary.total_inc_vat || 0).toLocaleString()}
            </span>
            <span style={{
              fontWeight: 600,
              color: summary.within_budget ? 'var(--success)' : '#DC2626',
            }}>
              {summary.within_budget
                ? `£${Math.round(summary.remaining || 0).toLocaleString()} remaining`
                : `£${Math.round(Math.abs(summary.remaining || 0)).toLocaleString()} over budget`
              }
            </span>
          </div>
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', gap: 12, marginTop: 28 }}>
          <button
            className="btn-primary"
            style={{ flex: 1, padding: '14px 20px' }}
            onClick={() => alert(
              'Booking flow coming soon \u2014 your event coordinator will be in touch within 24 hours.'
            )}
          >
            Confirm &amp; Book Event
          </button>
          <button className="btn-ghost" onClick={onRestart} style={{ padding: '14px 24px' }}>
            Start Over
          </button>
        </div>
      </div>
    </div>
  )
}
