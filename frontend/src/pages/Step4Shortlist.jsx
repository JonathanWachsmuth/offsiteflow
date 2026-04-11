import { useEffect, useState } from 'react'
import api from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

// ─── Category metadata ────────────────────────────────────────

const CAT_LABEL = {
  venue:     'Venue',
  catering:  'Catering',
  activity:  'Activity',
  transport: 'Transport',
}

function catLabel(cat) {
  return CAT_LABEL[cat] || cat.charAt(0).toUpperCase() + cat.slice(1)
}


// ─── Budget bar ───────────────────────────────────────────────

function BudgetBar({ budget, spent }) {
  if (!budget || !spent) return null
  const pct  = Math.min(100, Math.round((spent / budget) * 100))
  const over = spent > budget

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 13, marginBottom: 6,
      }}>
        <span style={{ color: 'var(--text-mid)' }}>Budget utilisation</span>
        <span style={{ fontWeight: 700, color: over ? '#DC2626' : 'var(--success)' }}>
          {pct}%
        </span>
      </div>
      <div style={{ height: 8, borderRadius: 4, background: '#E5E7EB', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          borderRadius: 4,
          background: over
            ? 'linear-gradient(90deg, #DC2626, #F87171)'
            : 'linear-gradient(90deg, #6366F1, #1565C0)',
          transition: 'width 0.6s ease',
        }} />
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 12, marginTop: 5, color: 'var(--text-light)',
      }}>
        <span>£0</span>
        <span>Budget: £{budget.toLocaleString()}</span>
      </div>
    </div>
  )
}


// ─── Per-category winner card ─────────────────────────────────

function CategoryWinnerCard({ category, vendor }) {
  const label   = catLabel(category)
  const score   = vendor.score ? Math.round(vendor.score * 100) : null
  const total   = vendor.total_inc_vat
    ? `£${Math.round(vendor.total_inc_vat).toLocaleString()}`
    : null
  const perHead = vendor.total_per_head
    ? `£${Math.round(vendor.total_per_head)}/head`
    : null

  return (
    <div style={{
      background: 'white',
      borderRadius: 16,
      border: '1px solid var(--border)',
      borderTop: '3px solid transparent',
      backgroundImage: 'linear-gradient(white, white), linear-gradient(90deg, #1565C0, #6366F1)',
      backgroundOrigin: 'border-box',
      backgroundClip: 'padding-box, border-box',
      padding: '20px 22px',
      boxShadow: '0 2px 8px rgba(13,27,62,0.05)',
    }}>
      {/* Category label + score */}
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', marginBottom: 12,
      }}>
        <span style={{
          fontSize: 11, fontWeight: 700, letterSpacing: '1.2px',
          textTransform: 'uppercase', color: 'var(--text-light)',
        }}>
          {label}
        </span>
        {score !== null && (
          <span className="pill-gradient" style={{ fontSize: 11 }}>
            {score}%
          </span>
        )}
      </div>

      {/* Vendor name */}
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--navy)', marginBottom: 8 }}>
        {vendor.vendor_name}
      </div>

      {/* Price — only shown when available */}
      {total && (
        <div style={{ marginBottom: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--navy)' }}>
            {total}
          </span>
          {perHead && (
            <span style={{ fontSize: 12, color: 'var(--text-light)', marginLeft: 6 }}>
              {perHead}
            </span>
          )}
        </div>
      )}

      {/* Inclusions */}
      {vendor.inclusions?.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {vendor.inclusions.slice(0, 4).map(inc => (
            <span key={inc} style={{
              background: '#F5F7FF',
              borderRadius: 6,
              padding: '2px 8px',
              fontSize: 11,
              color: 'var(--text-mid)',
              border: '1px solid var(--border)',
            }}>
              {inc}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}


// ─── Main component ───────────────────────────────────────────

export default function Step4Shortlist({ brief, selectedVendorIds, onBack, onRestart }) {
  const [shortlist, setShortlist] = useState(null)
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    async function load() {
      try {
        const res = await api.post('/api/shortlist', {
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

  if (loading) {
    return <LoadingSpinner text="Analysing vendor quotes and building shortlist…" />
  }

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

  const byCategory = shortlist?.by_category || {}
  const summary    = shortlist?.budget_summary || {}
  const metaInfo   = shortlist?.meta || {}
  const categories = Object.keys(byCategory)

  if (categories.length === 0) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center' }}>
        <p style={{ color: 'var(--text-mid)' }}>No shortlist results available.</p>
        <button className="btn-ghost" onClick={onBack} style={{ marginTop: 16 }}>
          &larr; Back
        </button>
      </div>
    )
  }

  return (
    <div className="page-container narrow">
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{
          display: 'inline-block',
          background: 'rgba(234,179,8,0.1)',
          border: '1px solid rgba(234,179,8,0.3)',
          borderRadius: 20, padding: '6px 16px',
          fontSize: 13, fontWeight: 500, color: 'var(--warning)',
          marginBottom: 16,
        }}>
          Shortlist Ready
        </div>
        <h2 style={{ fontSize: 34, fontWeight: 800, color: 'var(--navy)', lineHeight: 1.2 }}>
          Your event package
        </h2>
        {metaInfo.vendors_evaluated && (
          <p style={{ fontSize: 13, color: 'var(--text-light)', marginTop: 8 }}>
            Agent evaluated {metaInfo.vendors_evaluated} vendor{metaInfo.vendors_evaluated !== 1 ? 's' : ''} across{' '}
            {categories.length} categor{categories.length !== 1 ? 'ies' : 'y'}
          </p>
        )}
      </div>

      {/* Per-category winner cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: categories.length >= 2 ? '1fr 1fr' : '1fr',
        gap: 16,
        marginBottom: 24,
      }}>
        {categories.map(cat => {
          const top = byCategory[cat]?.[0]
          if (!top) return null
          return <CategoryWinnerCard key={cat} category={cat} vendor={top} />
        })}
      </div>

      {/* Budget summary card */}
      <div className="card" style={{ marginBottom: 16, padding: 24 }}>
        <BudgetBar budget={summary.budget} spent={summary.total_inc_vat} />

        <div style={{
          display: 'flex', justifyContent: 'space-around',
          marginTop: 20, paddingTop: 16,
          borderTop: '1px solid var(--border)',
          flexWrap: 'wrap', gap: 8,
          textAlign: 'center',
        }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-light)', marginBottom: 2 }}>Budget</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--navy)' }}>
              £{(summary.budget || 0).toLocaleString()}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-light)', marginBottom: 2 }}>Est. total (inc. VAT)</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--navy)' }}>
              £{Math.round(summary.total_inc_vat || 0).toLocaleString()}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-light)', marginBottom: 2 }}>
              {summary.within_budget ? 'Remaining' : 'Over budget'}
            </div>
            <div style={{
              fontSize: 20, fontWeight: 700,
              color: summary.within_budget ? 'var(--success)' : '#DC2626',
            }}>
              £{Math.round(Math.abs(summary.remaining || 0)).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* AI Recommendation */}
      {shortlist?.recommendation && (
        <div className="card" style={{ marginBottom: 24, padding: 24 }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: '1px',
            textTransform: 'uppercase', color: 'var(--text-light)',
            marginBottom: 10,
          }}>
            AI Recommendation
          </div>
          <p style={{ fontSize: 15, color: '#374151', lineHeight: 1.75, margin: 0 }}>
            {shortlist.recommendation}
          </p>
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 12 }}>
        <button
          className="btn-primary"
          style={{ flex: 1, padding: '14px 20px' }}
          onClick={() => alert(
            'Booking flow coming soon — your event coordinator will be in touch within 24 hours.'
          )}
        >
          Confirm &amp; Book Event
        </button>
        <button className="btn-ghost" onClick={onRestart} style={{ padding: '14px 24px' }}>
          Start Over
        </button>
      </div>
    </div>
  )
}
