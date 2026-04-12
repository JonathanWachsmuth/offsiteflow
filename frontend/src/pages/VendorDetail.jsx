import { useEffect, useState } from 'react'
import api from '../api'

const CAT_COLORS = {
  venue:     '#6366F1',
  catering:  '#16A34A',
  activity:  '#EA580C',
  transport: '#1565C0',
}

function InfoRow({ label, value, href }) {
  if (!value) return null
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '12px 0', borderBottom: '1px solid var(--border)',
    }}>
      <span style={{ fontSize: 13, color: 'var(--text-light)', fontWeight: 500 }}>{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noopener noreferrer"
          style={{ fontSize: 14, color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>
          {value}
        </a>
      ) : (
        <span style={{ fontSize: 14, color: 'var(--navy)', fontWeight: 500 }}>{value}</span>
      )}
    </div>
  )
}

export default function VendorDetail({ vendorId, onBack }) {
  const [vendor, setVendor]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [notes, setNotes]     = useState('')
  const [saved, setSaved]     = useState(false)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const res = await api.get(`/api/vendors/${vendorId}`)
        setVendor(res.data)
        // Load saved notes from localStorage
        const key = `vendor-notes-${vendorId}`
        setNotes(localStorage.getItem(key) || '')
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not load vendor.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [vendorId])

  function handleSaveNotes() {
    localStorage.setItem(`vendor-notes-${vendorId}`, notes)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{ fontSize: 15, color: 'var(--text-light)' }}>Loading vendor...</div>
      </div>
    )
  }

  if (error || !vendor) {
    return (
      <div className="page-container narrow" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{ fontSize: 15, color: '#DC2626', marginBottom: 16 }}>{error || 'Vendor not found.'}</div>
        <button className="btn-ghost" onClick={onBack}>Back</button>
      </div>
    )
  }

  const catColor = CAT_COLORS[vendor.category] || 'var(--text-mid)'
  const tags = vendor.tags
    ? (typeof vendor.tags === 'string' ? vendor.tags.split(',') : vendor.tags)
        .map(t => t.trim()).filter(Boolean)
    : []
  const amenities = vendor.amenities
    ? (typeof vendor.amenities === 'string' ? vendor.amenities.split(',') : vendor.amenities)
        .map(a => a.trim()).filter(Boolean)
    : []

  return (
    <div className="page-container narrow" style={{ paddingBottom: 60 }}>
      {/* Back button */}
      <button
        onClick={onBack}
        className="btn-ghost"
        style={{ marginBottom: 20, fontSize: 13 }}
      >
        &larr; Back
      </button>

      {/* Header card */}
      <div style={{
        background: 'white', borderRadius: 16, border: '1px solid var(--border)',
        boxShadow: '0 2px 12px rgba(13,27,62,0.06)', padding: '32px 36px', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: 26, fontWeight: 700, color: 'var(--navy)', margin: 0 }}>
                {vendor.name}
              </h2>
              <span style={{
                fontSize: 12, fontWeight: 600, textTransform: 'uppercase',
                letterSpacing: '0.5px', color: catColor,
                background: `${catColor}14`, padding: '3px 10px', borderRadius: 6,
              }}>
                {vendor.category}
              </span>
              {vendor.subcategory && (
                <span style={{
                  fontSize: 12, color: 'var(--text-light)',
                  background: '#F3F4F6', padding: '3px 10px', borderRadius: 6,
                }}>
                  {vendor.subcategory.replace(/_/g, ' ')}
                </span>
              )}
            </div>
            {vendor.city && (
              <div style={{ fontSize: 14, color: 'var(--text-mid)', marginTop: 8 }}>
                {vendor.address || vendor.city}{vendor.country && vendor.country !== 'GB' ? `, ${vendor.country}` : ''}
              </div>
            )}
          </div>
          {vendor.rating_external && (
            <div style={{
              textAlign: 'center', padding: '10px 20px',
              background: '#F5F7FF', borderRadius: 12,
            }}>
              <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--navy)' }}>
                &#9733; {vendor.rating_external}
              </div>
              {vendor.rating_count && (
                <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
                  {vendor.rating_count} reviews
                </div>
              )}
            </div>
          )}
        </div>

        {vendor.description && (
          <p style={{
            fontSize: 14, color: 'var(--text-mid)', lineHeight: 1.7,
            marginTop: 16, marginBottom: 0,
          }}>
            {vendor.description}
          </p>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Contact card */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 12 }}>
            Contact Information
          </div>
          <InfoRow label="Email" value={vendor.email} href={vendor.email ? `mailto:${vendor.email}` : null} />
          <InfoRow label="Phone" value={vendor.phone} href={vendor.phone ? `tel:${vendor.phone}` : null} />
          <InfoRow
            label="Website"
            value={vendor.website ? vendor.website.replace(/^https?:\/\//, '').replace(/\/$/, '') : null}
            href={vendor.website}
          />
          <InfoRow label="Contact Form" value={vendor.contact_form ? 'Available' : null} href={vendor.contact_form} />

          {/* Contact actions */}
          <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
            {vendor.email && (
              <a
                href={`mailto:${vendor.email}`}
                style={{
                  flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  padding: '10px 16px', borderRadius: 10,
                  background: 'var(--gradient)', color: 'white',
                  fontSize: 13, fontWeight: 600, textDecoration: 'none',
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                Send Email
              </a>
            )}
            {vendor.phone && (
              <a
                href={`tel:${vendor.phone}`}
                style={{
                  flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                  padding: '10px 16px', borderRadius: 10,
                  border: '1px solid var(--border)', background: 'white',
                  fontSize: 13, fontWeight: 600, color: 'var(--navy)',
                  textDecoration: 'none', fontFamily: 'Inter, sans-serif',
                }}
              >
                Call
              </a>
            )}
          </div>
        </div>

        {/* Details card */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 12 }}>
            Details
          </div>
          <InfoRow
            label="Capacity"
            value={
              vendor.capacity_min && vendor.capacity_max
                ? `${vendor.capacity_min} – ${vendor.capacity_max} people`
                : vendor.capacity_max ? `Up to ${vendor.capacity_max} people` : null
            }
          />
          <InfoRow
            label="Starting price"
            value={vendor.price_from ? `£${Number(vendor.price_from).toLocaleString()}${vendor.price_unit ? ` ${vendor.price_unit.replace(/_/g, ' ')}` : ''}` : null}
          />
          <InfoRow label="Lead time" value={vendor.lead_time_days ? `${vendor.lead_time_days} days` : null} />
          <InfoRow label="Cancellation" value={vendor.cancellation_policy} />
          <InfoRow label="Deposit" value={vendor.deposit_required ? `£${Number(vendor.deposit_required).toLocaleString()}` : null} />
          <InfoRow label="Sustainability" value={vendor.sustainability} />
        </div>
      </div>

      {/* Tags & Amenities */}
      {(tags.length > 0 || amenities.length > 0) && (
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px', marginBottom: 20,
        }}>
          {tags.length > 0 && (
            <div style={{ marginBottom: amenities.length > 0 ? 16 : 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 10 }}>
                Tags
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {tags.map(t => (
                  <span key={t} style={{
                    background: '#F3F4F6', border: '1px solid var(--border)',
                    borderRadius: 8, padding: '4px 12px', fontSize: 13, color: 'var(--text-mid)',
                  }}>{t}</span>
                ))}
              </div>
            </div>
          )}
          {amenities.length > 0 && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 10 }}>
                Amenities
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {amenities.map(a => (
                  <span key={a} style={{
                    background: '#F0FDF4', border: '1px solid #BBF7D0',
                    borderRadius: 8, padding: '4px 12px', fontSize: 13, color: '#16A34A',
                  }}>{a}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Notes */}
      <div style={{
        background: 'white', borderRadius: 16, border: '1px solid var(--border)',
        padding: '24px 28px',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)' }}>
            Your Notes
          </div>
          {saved && (
            <span style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600 }}>Saved</span>
          )}
        </div>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Add personal notes about this vendor — pricing discussions, contact history, preferences..."
          style={{
            width: '100%', minHeight: 120, padding: '14px 18px',
            borderRadius: 10, border: '1px solid var(--border)',
            fontSize: 14, color: 'var(--text-dark)', lineHeight: 1.7,
            fontFamily: 'Inter, sans-serif', resize: 'vertical',
            outline: 'none', boxSizing: 'border-box',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 10 }}>
          <button
            onClick={handleSaveNotes}
            style={{
              background: 'var(--gradient)', border: 'none',
              borderRadius: 8, padding: '8px 20px',
              fontSize: 13, fontWeight: 600, color: 'white',
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            }}
          >
            Save Notes
          </button>
        </div>
      </div>
    </div>
  )
}
