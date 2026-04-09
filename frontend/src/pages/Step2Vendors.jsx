import { useState } from 'react'

function priceTier(priceFrom) {
  if (!priceFrom) return ''
  if (priceFrom < 2000)  return '£'
  if (priceFrom < 5000)  return '££'
  return '£££'
}

function VendorCard({ vendor, isSelected, onToggle }) {
  const score     = vendor.score
    ? Math.round(vendor.score * 100)
    : Math.round(((vendor.rating_external || 3) / 5) * 80 + 20)
  const tags      = vendor.tags
    ? vendor.tags.split(',').map(t => t.trim()).filter(Boolean).slice(0, 3)
    : vendor.amenities
    ? vendor.amenities.split(',').map(t => t.trim()).filter(Boolean).slice(0, 3)
    : []
  const hasEmail  = Boolean(vendor.email)
  const tier      = priceTier(vendor.price_from)

  return (
    <div
      onClick={() => onToggle(vendor.id)}
      style={{
        background: 'white',
        borderRadius: 16,
        border: isSelected
          ? '2px solid var(--blue)'
          : '1px solid var(--border)',
        boxShadow: isSelected
          ? '0 0 0 3px rgba(21,101,192,0.08)'
          : '0 2px 8px rgba(13,27,62,0.04)',
        padding: '20px 24px',
        cursor: 'pointer',
        transition: 'border 0.15s, box-shadow 0.15s',
        opacity: 1,
      }}
    >
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span className="pill-gradient">{score}% match</span>
        <div style={{
          width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 700,
          ...(isSelected
            ? { background: 'var(--gradient)', color: 'white' }
            : { border: '2px solid #D1D5DB', background: 'white' }),
        }}>
          {isSelected ? '✓' : ''}
        </div>
      </div>

      {/* Name */}
      <div style={{ marginTop: 12 }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--navy)' }}>
          {vendor.name}
        </span>
        {!hasEmail && (
          <span style={{
            marginLeft: 8, display: 'inline-flex', alignItems: 'center',
            background: '#FEF2F2', border: '1px solid #FECACA',
            borderRadius: 20, padding: '2px 8px',
            fontSize: 11, color: '#DC2626', fontWeight: 500,
          }}>
            no email
          </span>
        )}
      </div>

      {/* Meta */}
      <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 4 }}>
        {vendor.city && <span>{vendor.city}</span>}
        {vendor.rating_external && (
          <span> &nbsp;&middot;&nbsp; &#9733; {vendor.rating_external}</span>
        )}
      </div>

      <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 2 }}>
        {vendor.capacity_min && vendor.capacity_max
          ? <span>{vendor.capacity_min}&ndash;{vendor.capacity_max}</span>
          : vendor.capacity_max
          ? <span>Up to {vendor.capacity_max}</span>
          : null
        }
        {tier && <span> &nbsp;&middot;&nbsp; {tier}</span>}
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
          {tags.map(t => (
            <span key={t} style={{
              background: '#F3F4F6', border: '1px solid var(--border)',
              borderRadius: 8, padding: '3px 9px',
              fontSize: 12, color: 'var(--text-mid)',
            }}>
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Step2Vendors({
  routingResult, selected, onToggle, onBack, onContinue,
}) {
  const matches       = routingResult?.matches || {}
  const selectedCount = Object.values(selected).filter(Boolean).length
  const selectedIds   = Object.entries(selected)
    .filter(([, v]) => v).map(([id]) => id)

  return (
    <>
      <div className="page-container wide" style={{ paddingBottom: 100 }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, color: 'var(--navy)' }}>
            Matching vendors found
          </h2>
          <p style={{ fontSize: 16, color: 'var(--text-mid)', marginTop: 8 }}>
            Select the vendors you'd like to send RFQs to.
            We ranked them by match score.
          </p>
        </div>

        {Object.entries(matches).map(([category, vendors]) => {
          if (!vendors || vendors.length === 0) return null
          return (
            <div key={category}>
              <div style={{
                fontSize: 11, fontWeight: 700, letterSpacing: '1.5px',
                color: 'var(--text-light)', textTransform: 'uppercase',
                margin: '28px 0 12px',
              }}>
                {category}s
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                gap: 16,
              }}>
                {vendors.map(v => (
                  <VendorCard
                    key={v.id}
                    vendor={v}
                    isSelected={Boolean(selected[v.id])}
                    onToggle={onToggle}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* Sticky bottom bar */}
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
        background: 'white', borderTop: '1px solid var(--border)',
        padding: '16px 40px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <button className="btn-ghost" onClick={onBack}>
          &larr; Back
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 14, color: 'var(--text-mid)' }}>
            {selectedCount} vendor{selectedCount !== 1 ? 's' : ''} selected
          </span>
          <button
            className="btn-primary"
            disabled={selectedCount === 0}
            onClick={() => onContinue(selectedIds)}
          >
            Send RFQs ({selectedCount}) &rarr;
          </button>
        </div>
      </div>
    </>
  )
}
