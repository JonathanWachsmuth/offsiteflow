import { useState, useEffect, useRef, useCallback } from 'react'
import api from '../api'

const CAT_COLORS = {
  venue:     '#6366F1',
  catering:  '#16A34A',
  activity:  '#EA580C',
  transport: '#1565C0',
}

function ResultItem({ vendor, isActive, onClick }) {
  const catColor = CAT_COLORS[vendor.category] || 'var(--text-mid)'
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px', cursor: 'pointer',
        background: isActive ? '#F5F7FF' : 'transparent',
        borderBottom: '1px solid #F3F4F6',
        transition: 'background 0.1s',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
          {vendor.name}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
          {vendor.city}
          {vendor.email && <span> &middot; {vendor.email}</span>}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        {vendor.rating_external && (
          <span style={{ fontSize: 12, color: 'var(--text-mid)' }}>
            &#9733; {vendor.rating_external}
          </span>
        )}
        <span style={{
          fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
          letterSpacing: '0.5px', color: catColor,
          background: `${catColor}14`, padding: '2px 8px', borderRadius: 6,
        }}>
          {vendor.category}
        </span>
      </div>
    </div>
  )
}

export default function CommandPalette({ open, onClose, onNavigateVendors, onViewVendor }) {
  const [query, setQuery]       = useState('')
  const [results, setResults]   = useState([])
  const [loading, setLoading]   = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const inputRef = useRef(null)

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery('')
      setResults([])
      setActiveIdx(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [open])

  // Debounced search
  useEffect(() => {
    if (!query || query.length < 2) {
      setResults([])
      return
    }
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.get('/api/vendors/search', { params: { q: query } })
        setResults(res.data.results || [])
        setActiveIdx(0)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)
    return () => clearTimeout(timer)
  }, [query])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && results.length > 0) {
      e.preventDefault()
      handleSelect(results[activeIdx])
    }
  }, [results, activeIdx, onClose])

  function handleSelect(vendor) {
    onClose()
    onViewVendor?.(vendor.id)
  }

  // Global Cmd+K listener
  useEffect(() => {
    function handleGlobal(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (open) onClose()
        else onClose.__open?.()
      }
    }
    // Only register if we have the toggle function
    return () => {}
  }, [open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 999,
          background: 'rgba(13,27,62,0.4)', backdropFilter: 'blur(4px)',
        }}
      />

      {/* Palette */}
      <div style={{
        position: 'fixed', top: '15%', left: '50%',
        transform: 'translateX(-50%)', zIndex: 1000,
        width: '100%', maxWidth: 560,
        background: 'white', borderRadius: 16,
        boxShadow: '0 20px 60px rgba(13,27,62,0.25)',
        overflow: 'hidden',
      }}>
        {/* Search input */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '16px 20px', borderBottom: '1px solid var(--border)',
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-light)', flexShrink: 0 }}>
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search vendors by name, tag, or description..."
            style={{
              flex: 1, border: 'none', outline: 'none',
              fontSize: 15, fontFamily: 'Inter, sans-serif',
              color: 'var(--text-dark)', background: 'transparent',
            }}
          />
          <kbd style={{
            padding: '2px 8px', borderRadius: 6,
            background: '#F3F4F6', border: '1px solid var(--border)',
            fontSize: 12, color: 'var(--text-light)', fontFamily: 'Inter, sans-serif',
          }}>
            esc
          </kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: 380, overflowY: 'auto' }}>
          {loading && query.length >= 2 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-light)', fontSize: 14 }}>
              Searching...
            </div>
          )}

          {!loading && query.length >= 2 && results.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-light)', fontSize: 14 }}>
              No vendors found for "{query}"
            </div>
          )}

          {results.map((v, i) => (
            <ResultItem
              key={v.id}
              vendor={v}
              isActive={i === activeIdx}
              onClick={() => handleSelect(v)}
            />
          ))}
        </div>

        {/* Footer */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 20px', borderTop: '1px solid var(--border)',
          background: '#FAFBFC', fontSize: 12, color: 'var(--text-light)',
        }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <span><kbd style={{ padding: '1px 5px', borderRadius: 4, background: '#F3F4F6', border: '1px solid #E5E7EB', fontSize: 11 }}>&uarr;&darr;</kbd> navigate</span>
            <span><kbd style={{ padding: '1px 5px', borderRadius: 4, background: '#F3F4F6', border: '1px solid #E5E7EB', fontSize: 11 }}>&#9166;</kbd> view vendor</span>
          </div>
          <button
            onClick={() => { onClose(); onNavigateVendors?.() }}
            style={{
              background: 'transparent', border: 'none',
              fontSize: 12, color: 'var(--blue)', fontWeight: 600,
              cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            }}
          >
            Browse all vendors &rarr;
          </button>
        </div>
      </div>
    </>
  )
}
