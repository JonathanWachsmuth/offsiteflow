import { useState } from 'react'

const CAT_LABEL = {
  venue: 'Venue', catering: 'Catering',
  activity: 'Activity', transport: 'Transport',
}

// Synthetic RFQ statuses for demo
const STATUS_MAP = {
  sent:     { label: 'Sent',     bg: '#EFF6FF', color: '#1565C0' },
  opened:   { label: 'Opened',   bg: '#FFF7ED', color: '#EA580C' },
  replied:  { label: 'Replied',  bg: '#F0FDF4', color: '#16A34A' },
  pending:  { label: 'Pending',  bg: '#F3F4F6', color: '#6B7280' },
}

function RFQStatusCard({ vendor, status }) {
  const s = STATUS_MAP[status] || STATUS_MAP.pending
  return (
    <div style={{
      background: 'white', borderRadius: 14,
      border: '1px solid var(--border)',
      padding: '16px 20px',
      boxShadow: '0 2px 8px rgba(13,27,62,0.04)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--navy)' }}>
            {vendor.name}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
            {CAT_LABEL[vendor.category] || vendor.category}
            {vendor.email && <span> &middot; {vendor.email}</span>}
          </div>
          {vendor.website && (
            <a
              href={vendor.website}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 11, color: 'var(--blue)', textDecoration: 'none' }}
            >
              {vendor.website.replace(/^https?:\/\//, '').replace(/\/$/, '').substring(0, 35)}
              &nbsp;&#8599;
            </a>
          )}
        </div>
        <span style={{
          background: s.bg, color: s.color,
          borderRadius: 20, padding: '4px 12px',
          fontSize: 12, fontWeight: 600,
        }}>
          {s.label}
        </span>
      </div>
    </div>
  )
}

function assignDemoStatus(index) {
  // Simulate realistic status distribution for demo
  const statuses = ['replied', 'replied', 'opened', 'sent', 'pending']
  return statuses[index % statuses.length]
}

export default function Dashboard({ brief, selectedVendors, onFindBestMatch, onNewEvent }) {
  const hasEvent = brief && selectedVendors && selectedVendors.length > 0
  const [sent, setSent] = useState(false)

  if (!hasEvent) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{
          width: 72, height: 72, borderRadius: '50%',
          background: '#F5F7FF', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 24px',
        }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M8 12h8M8 8h8M8 16h4" />
          </svg>
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 700, color: 'var(--navy)', marginBottom: 12 }}>
          No active events
        </h2>
        <p style={{ fontSize: 15, color: 'var(--text-mid)', marginBottom: 28, lineHeight: 1.6 }}>
          Start by creating a new event brief. We'll match you with the best vendors
          and help you send RFQs.
        </p>
        <button className="btn-primary" onClick={onNewEvent}>
          Create New Event &rarr;
        </button>
      </div>
    )
  }

  const categories = [...new Set(selectedVendors.map(v => v.category))]
  const repliedCount = selectedVendors.filter((_, i) => assignDemoStatus(i) === 'replied').length

  return (
    <div className="page-container wide">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: 'var(--navy)', marginBottom: 6 }}>
          Event Dashboard
        </h2>
        <p style={{ fontSize: 15, color: 'var(--text-mid)' }}>
          Track your RFQ responses and find the best vendor package
        </p>
      </div>

      {/* Event summary card */}
      <div style={{
        background: 'white', borderRadius: 16, border: '1px solid var(--border)',
        padding: '24px 28px', marginBottom: 24,
        boxShadow: '0 2px 8px rgba(13,27,62,0.05)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1.2px', textTransform: 'uppercase', color: 'var(--text-light)', marginBottom: 8 }}>
              Current Event
            </div>
            <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--navy)' }}>
              {brief.event_type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Corporate Event'}
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-mid)', marginTop: 4 }}>
              {brief.city || 'London'}
              {brief.headcount && <span> &middot; {brief.headcount} people</span>}
              {brief.budget_total && <span> &middot; £{Number(brief.budget_total).toLocaleString()} budget</span>}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <div style={{ textAlign: 'center', padding: '8px 20px', background: '#F5F7FF', borderRadius: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--blue)' }}>{selectedVendors.length}</div>
              <div style={{ fontSize: 11, color: 'var(--text-light)', marginTop: 2 }}>RFQs Sent</div>
            </div>
            <div style={{ textAlign: 'center', padding: '8px 20px', background: '#F0FDF4', borderRadius: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#16A34A' }}>{repliedCount}</div>
              <div style={{ fontSize: 11, color: 'var(--text-light)', marginTop: 2 }}>Responses</div>
            </div>
            <div style={{ textAlign: 'center', padding: '8px 20px', background: '#F3F4F6', borderRadius: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--navy)' }}>{categories.length}</div>
              <div style={{ fontSize: 11, color: 'var(--text-light)', marginTop: 2 }}>Categories</div>
            </div>
          </div>
        </div>
      </div>

      {/* RFQ Status Grid */}
      {categories.map(cat => {
        const catVendors = selectedVendors.filter(v => v.category === cat)
        return (
          <div key={cat} style={{ marginBottom: 24 }}>
            <div style={{
              fontSize: 11, fontWeight: 700, letterSpacing: '1.5px',
              color: 'var(--text-light)', textTransform: 'uppercase',
              marginBottom: 12,
            }}>
              {CAT_LABEL[cat] || cat}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
              {catVendors.map((v, i) => (
                <RFQStatusCard
                  key={v.id}
                  vendor={v}
                  status={assignDemoStatus(selectedVendors.indexOf(v))}
                />
              ))}
            </div>
          </div>
        )
      })}

      {/* Find Best Match CTA */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1b4b 0%, #2d3a8c 100%)',
        borderRadius: 16, padding: '32px 36px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 20, marginTop: 8,
      }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'white', marginBottom: 6 }}>
            Ready to find your best match?
          </div>
          <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.7)' }}>
            Our AI will analyse all {repliedCount} vendor responses and recommend the optimal package for your budget.
          </div>
        </div>
        <button
          onClick={onFindBestMatch}
          style={{
            background: 'white', border: 'none',
            borderRadius: 10, padding: '14px 28px',
            fontSize: 15, fontWeight: 700, color: '#1a1b4b',
            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
            transition: 'transform 0.15s',
          }}
        >
          Find Best Match &rarr;
        </button>
      </div>
    </div>
  )
}
