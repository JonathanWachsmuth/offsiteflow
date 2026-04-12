import { useEffect, useState } from 'react'
import api from '../api'

const CAT_LABEL = {
  venue:     'Venue',
  catering:  'Catering',
  activity:  'Activity',
  transport: 'Transport',
}

function ShimmerBar() {
  return (
    <div style={{ height: 4, borderRadius: 2, marginTop: 12, overflow: 'hidden' }}>
      <div style={{
        height: '100%',
        background: 'linear-gradient(90deg, #6366F1 0%, #1565C0 25%, #7EB3FF 50%, #1565C0 75%, #6366F1 100%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.8s linear infinite',
      }} />
    </div>
  )
}

function RFQCard({ preview }) {
  const [expanded, setExpanded] = useState(false)
  const cat      = preview.category || 'venue'
  const hasError = Boolean(preview.error)

  return (
    <div className="card" style={{ marginBottom: 12, padding: 24 }}>
      {/* Header row */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'flex-start', gap: 12, flexWrap: 'wrap',
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 17, fontWeight: 700, color: 'var(--navy)' }}>
              {preview.vendor_name}
            </span>
            <span style={{
              fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
              letterSpacing: '0.5px', color: 'var(--text-light)',
              background: '#F3F4F6', padding: '2px 8px', borderRadius: 6,
            }}>
              {CAT_LABEL[cat] || cat}
            </span>
          </div>
          {preview.subject && (
            <div style={{ fontSize: 13, color: 'var(--text-light)', marginTop: 4, wordBreak: 'break-word' }}>
              {preview.subject}
            </div>
          )}
          {preview.has_email && preview.email_to && (
            <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
              To: {preview.email_to}
            </div>
          )}
          {preview.website && (
            <div style={{ fontSize: 12, marginTop: 2 }}>
              <a
                href={preview.website}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--blue)', textDecoration: 'none' }}
              >
                {preview.website.replace(/^https?:\/\//, '').replace(/\/$/, '').substring(0, 45)}
                {preview.website.replace(/^https?:\/\//, '').replace(/\/$/, '').length > 45 ? '…' : ''}
                &nbsp;&#8599;
              </a>
            </div>
          )}
          {preview.description && (
            <div style={{
              fontSize: 12, color: '#4B5563', marginTop: 6, lineHeight: 1.5,
              display: '-webkit-box', WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical', overflow: 'hidden',
            }}>
              {preview.description}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          {hasError ? (
            <span style={{
              background: '#FEF2F2', border: '1px solid #FECACA',
              borderRadius: 20, padding: '4px 12px',
              fontSize: 12, color: '#DC2626',
            }}>
              Generation failed
            </span>
          ) : preview.has_email ? (
            <span className="pill-received">&#10003; Ready to send</span>
          ) : (
            <span style={{
              background: '#FEF3C7', border: '1px solid #FDE68A',
              borderRadius: 20, padding: '4px 12px',
              fontSize: 12, fontWeight: 600, color: 'var(--warning)',
            }}>
              No email on file
            </span>
          )}

          {preview.plain_body && (
            <button
              onClick={() => setExpanded(e => !e)}
              style={{
                background: expanded ? '#F5F7FF' : 'transparent',
                border: '1px solid var(--border)',
                borderRadius: 8, padding: '4px 14px',
                fontSize: 13, color: 'var(--text-mid)',
                cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                transition: 'background 0.15s',
              }}
            >
              {expanded ? 'Hide' : 'Preview'}
            </button>
          )}
        </div>
      </div>

      {/* Expandable email body */}
      {expanded && preview.plain_body && (
        <div style={{
          marginTop: 16,
          padding: '16px 20px',
          background: '#F8FAFF',
          borderRadius: 10,
          border: '1px solid var(--border)',
          fontSize: 14,
          color: '#374151',
          lineHeight: 1.8,
          whiteSpace: 'pre-wrap',
        }}>
          {preview.plain_body}
        </div>
      )}
    </div>
  )
}

function PlaceholderCard({ vendor }) {
  return (
    <div className="card" style={{ marginBottom: 12, padding: 24, opacity: 0.55 }}>
      <div style={{ fontSize: 17, fontWeight: 700, color: 'var(--navy)' }}>
        {vendor.name}
      </div>
      <ShimmerBar />
    </div>
  )
}

export default function Step3RFQs({ selectedVendors, brief, onBack, onContinue }) {
  const [previews, setPreviews] = useState(null)
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  const vendors = selectedVendors || []

  useEffect(() => {
    if (vendors.length === 0) {
      setLoading(false)
      return
    }
    async function load() {
      try {
        const res = await api.post('/api/preview-rfqs', {
          brief,
          selected_vendor_ids: vendors.map(v => v.id),
        })
        setPreviews(res.data.previews)
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not generate RFQ previews.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const readyCount   = previews?.filter(p => p.has_email && !p.error).length ?? 0
  const noEmailCount = previews?.filter(p => !p.has_email).length ?? 0

  return (
    <>
      <div className="page-container narrow" style={{ paddingBottom: 100 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, color: 'var(--navy)' }}>
            RFQ Previews
          </h2>
          <p style={{ fontSize: 16, color: 'var(--text-mid)', marginTop: 8 }}>
            {loading
              ? `Generating personalised emails for ${vendors.length} vendor${vendors.length !== 1 ? 's' : ''}…`
              : `${readyCount} email${readyCount !== 1 ? 's' : ''} ready to send`
                + (noEmailCount > 0 ? ` · ${noEmailCount} without email on file` : '')
            }
          </p>
          {loading && <ShimmerBar />}
        </div>

        {/* Error banner */}
        {error && (
          <div style={{
            marginBottom: 16, padding: '12px 16px',
            background: '#FEF2F2', border: '1px solid #FECACA',
            borderRadius: 10, color: '#DC2626', fontSize: 14,
          }}>
            {error}
          </div>
        )}

        {/* Skeleton cards while loading */}
        {loading && vendors.map(v => <PlaceholderCard key={v.id} vendor={v} />)}

        {/* Real preview cards */}
        {previews?.map(p => <RFQCard key={p.vendor_id} preview={p} />)}
      </div>

      {/* Sticky bottom bar */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
        background: 'white', borderTop: '1px solid var(--border)',
        padding: '16px 40px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <button className="btn-ghost" onClick={onBack}>&larr; Back</button>
        <button
          className="btn-primary"
          onClick={onContinue}
          disabled={loading}
        >
          {loading ? 'Generating…' : 'Show Best Match →'}
        </button>
      </div>
    </>
  )
}
