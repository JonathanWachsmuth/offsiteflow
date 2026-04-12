import { useState, useEffect, useCallback } from 'react'
import api from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

function VendorCard({ vendor }) {
  const hasEmail = Boolean(vendor.email)
  const tags = vendor.tags
    ? vendor.tags.split(',').map(t => t.trim()).filter(Boolean).slice(0, 3)
    : []

  return (
    <div style={{
      background: 'white', borderRadius: 14, border: '1px solid var(--border)',
      boxShadow: '0 2px 8px rgba(13,27,62,0.05)', padding: '20px 22px',
    }}>
      {/* Top row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--navy)' }}>
            {vendor.name}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 2 }}>
            {vendor.city}{vendor.city && vendor.category ? ' · ' : ''}{vendor.category}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          {vendor.rating_external && (
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>
              &#9733; {vendor.rating_external}
              {vendor.rating_count && (
                <span style={{ fontWeight: 400, color: 'var(--text-light)', marginLeft: 4 }}>
                  ({vendor.rating_count})
                </span>
              )}
            </span>
          )}
          {hasEmail
            ? <span style={{
                background: '#F0FDF4', border: '1px solid #BBF7D0',
                borderRadius: 20, padding: '2px 10px',
                fontSize: 11, color: 'var(--success)', fontWeight: 600,
              }}>email</span>
            : <span style={{
                background: '#FEF2F2', border: '1px solid #FECACA',
                borderRadius: 20, padding: '2px 10px',
                fontSize: 11, color: '#DC2626', fontWeight: 600,
              }}>no email</span>
          }
        </div>
      </div>

      {/* Capacity / price */}
      <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 8 }}>
        {vendor.capacity_max && <span>Up to {vendor.capacity_max} people</span>}
        {vendor.capacity_max && vendor.price_from && <span> &nbsp;&middot;&nbsp; </span>}
        {vendor.price_from && <span>From £{vendor.price_from.toLocaleString()}</span>}
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
          {tags.map(t => (
            <span key={t} style={{
              background: '#F3F4F6', border: '1px solid var(--border)',
              borderRadius: 8, padding: '3px 9px', fontSize: 12, color: 'var(--text-mid)',
            }}>{t}</span>
          ))}
        </div>
      )}

      {/* Links */}
      <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
        {vendor.website && (
          <a href={vendor.website} target="_blank" rel="noreferrer"
            style={{ fontSize: 13, color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>
            Website &rarr;
          </a>
        )}
        {vendor.email && (
          <a href={`mailto:${vendor.email}`}
            style={{ fontSize: 13, color: 'var(--blue)', textDecoration: 'none', fontWeight: 500 }}>
            {vendor.email}
          </a>
        )}
      </div>
    </div>
  )
}

export default function VendorSearch() {
  const [query,      setQuery]      = useState('')
  const [category,   setCategory]   = useState('')
  const [city,       setCity]       = useState('')
  const [minRating,  setMinRating]  = useState(0)
  const [hasEmail,   setHasEmail]   = useState(false)
  const [vendors,    setVendors]    = useState([])
  const [total,      setTotal]      = useState(0)
  const [offset,     setOffset]     = useState(0)
  const [loading,    setLoading]    = useState(false)
  const [cities,     setCities]     = useState([])
  const [categories, setCategories] = useState([])

  const LIMIT = 24

  const fetchVendors = useCallback(async (newOffset = 0) => {
    setLoading(true)
    try {
      const res = await api.get('/api/vendors', {
        params: {
          q:          query,
          category,
          city,
          min_rating: minRating,
          has_email:  hasEmail,
          limit:      LIMIT,
          offset:     newOffset,
        },
      })
      if (newOffset === 0) {
        setVendors(res.data.vendors)
        setCities(res.data.cities)
        setCategories(res.data.categories)
      } else {
        setVendors(prev => [...prev, ...res.data.vendors])
      }
      setTotal(res.data.total)
      setOffset(newOffset)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [query, category, city, minRating, hasEmail])

  // Fetch on filter change with debounce for text input
  useEffect(() => {
    const timer = setTimeout(() => fetchVendors(0), query ? 300 : 0)
    return () => clearTimeout(timer)
  }, [query, category, city, minRating, hasEmail])

  const filterStyle = {
    padding: '9px 14px', borderRadius: 10, border: '1px solid var(--border)',
    fontSize: 14, fontFamily: 'Inter, sans-serif', color: 'var(--text-dark)',
    background: 'white', outline: 'none', cursor: 'pointer',
  }

  return (
    <div className="page-container wide">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: 'var(--navy)', marginBottom: 6 }}>
          Vendors
        </h2>
        <p style={{ fontSize: 15, color: 'var(--text-mid)' }}>
          {total.toLocaleString()} vendors · search and filter by category, city, and rating
        </p>
      </div>

      {/* Search + filters */}
      <div style={{
        background: 'white', borderRadius: 16, border: '1px solid var(--border)',
        padding: '20px 24px', marginBottom: 24,
        display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center',
      }}>
        {/* Search input */}
        <div style={{ flex: 2, minWidth: 220, position: 'relative' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{
            position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-light)', pointerEvents: 'none',
          }}>
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by name, tag, or amenity..."
            style={{
              ...filterStyle, width: '100%', paddingLeft: 36, cursor: 'text',
            }}
          />
        </div>

        {/* Category */}
        <select value={category} onChange={e => setCategory(e.target.value)} style={filterStyle}>
          <option value="">All categories</option>
          {categories.map(c => (
            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>

        {/* City */}
        <select value={city} onChange={e => setCity(e.target.value)} style={filterStyle}>
          <option value="">All cities</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        {/* Min rating */}
        <select value={minRating} onChange={e => setMinRating(Number(e.target.value))} style={filterStyle}>
          <option value={0}>Any rating</option>
          <option value={3}>&#9733; 3+</option>
          <option value={4}>&#9733; 4+</option>
          <option value={4.5}>&#9733; 4.5+</option>
        </select>

        {/* Has email toggle */}
        <label style={{
          display: 'flex', alignItems: 'center', gap: 8,
          fontSize: 14, color: 'var(--text-mid)', cursor: 'pointer', whiteSpace: 'nowrap',
        }}>
          <div
            onClick={() => setHasEmail(v => !v)}
            style={{
              width: 40, height: 22, borderRadius: 11, cursor: 'pointer',
              background: hasEmail ? 'var(--gradient)' : '#E5E7EB',
              position: 'relative', transition: 'background 0.2s', flexShrink: 0,
            }}
          >
            <div style={{
              position: 'absolute', top: 3, left: hasEmail ? 21 : 3,
              width: 16, height: 16, borderRadius: '50%', background: 'white',
              transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
            }} />
          </div>
          Email only
        </label>

        {/* Reset */}
        {(query || category || city || minRating > 0 || hasEmail) && (
          <button
            className="btn-ghost"
            style={{ padding: '9px 16px', fontSize: 13 }}
            onClick={() => {
              setQuery(''); setCategory(''); setCity('');
              setMinRating(0); setHasEmail(false)
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results */}
      {loading && vendors.length === 0 ? (
        <LoadingSpinner text="Loading vendors..." />
      ) : vendors.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px 24px',
          color: 'var(--text-light)', fontSize: 15,
        }}>
          No vendors match your filters.
        </div>
      ) : (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: 16,
          }}>
            {vendors.map(v => <VendorCard key={v.id} vendor={v} />)}
          </div>

          {/* Load more */}
          {vendors.length < total && (
            <div style={{ textAlign: 'center', marginTop: 32 }}>
              <button
                className="btn-ghost"
                onClick={() => fetchVendors(offset + LIMIT)}
                disabled={loading}
              >
                {loading ? 'Loading...' : `Load more (${total - vendors.length} remaining)`}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
