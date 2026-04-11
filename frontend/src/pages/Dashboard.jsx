import { useState, useEffect } from 'react'
import api from '../api'
import LoadingSpinner from '../components/LoadingSpinner'

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'white', borderRadius: 14, border: '1px solid var(--border)',
      boxShadow: '0 2px 8px rgba(13,27,62,0.05)', padding: '22px 24px',
      flex: 1, minWidth: 160,
    }}>
      <div style={{ fontSize: 13, color: 'var(--text-light)', fontWeight: 500, marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: 30, fontWeight: 800, color: color || 'var(--navy)', lineHeight: 1.1 }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 13, color: 'var(--text-mid)', marginTop: 4 }}>{sub}</div>
      )}
    </div>
  )
}

function BarChart({ data, label, color = '#6366F1' }) {
  if (!data || Object.keys(data).length === 0) return null
  const max = Math.max(...Object.values(data))
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 12 }}>
        {label}
      </div>
      {Object.entries(data).map(([key, val]) => (
        <div key={key} style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 13, color: 'var(--text-dark)', fontWeight: 500 }}>
              {key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
            </span>
            <span style={{ fontSize: 13, color: 'var(--text-mid)' }}>{val}</span>
          </div>
          <div style={{ height: 6, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 3,
              background: `linear-gradient(90deg, ${color}, ${color}88)`,
              width: `${(val / max) * 100}%`,
              transition: 'width 0.6s ease',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function EventRow({ event }) {
  const statusColors = {
    sourcing:   { bg: '#EFF6FF', color: '#1565C0' },
    booked:     { bg: '#F0FDF4', color: '#16A34A' },
    completed:  { bg: '#F3F4F6', color: '#6B7280' },
    cancelled:  { bg: '#FEF2F2', color: '#DC2626' },
  }
  const sc = statusColors[event.status] || { bg: '#F3F4F6', color: '#6B7280' }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '14px 0', borderBottom: '1px solid var(--border)',
      flexWrap: 'wrap', gap: 8,
    }}>
      <div style={{ flex: 1, minWidth: 200 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
          {event.name || `${event.type || 'Event'} — ${event.city || '—'}`}
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-light)', marginTop: 2 }}>
          {event.city || '—'}
          {event.date_start ? ` · ${event.date_start}` : ''}
          {event.headcount ? ` · ${event.headcount} people` : ''}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        {event.budget_total && (
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
            £{event.budget_total.toLocaleString()}
          </span>
        )}
        <span style={{
          background: sc.bg, color: sc.color,
          borderRadius: 20, padding: '3px 12px',
          fontSize: 12, fontWeight: 600,
        }}>
          {event.status || 'unknown'}
        </span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    api.get('/api/events')
      .then(res => setData(res.data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner text="Loading dashboard..." />
  if (error) return (
    <div className="page-container">
      <p style={{ color: '#DC2626' }}>Failed to load: {error}</p>
    </div>
  )

  const { stats, vendor_stats, events } = data

  return (
    <div className="page-container wide">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: 'var(--navy)', marginBottom: 6 }}>
          Dashboard
        </h2>
        <p style={{ fontSize: 15, color: 'var(--text-mid)' }}>
          Overview of events and vendor database
        </p>
      </div>

      {/* Event KPI row */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard
          label="Total Events"
          value={stats.total_events}
          sub="all time"
        />
        <StatCard
          label="Total Budget"
          value={`£${(stats.total_budget || 0).toLocaleString()}`}
          sub="across all events"
          color="var(--blue)"
        />
        <StatCard
          label="Avg Budget"
          value={`£${(stats.avg_budget || 0).toLocaleString()}`}
          sub="per event"
          color="var(--purple)"
        />
        <StatCard
          label="Total Guests"
          value={(stats.total_headcount || 0).toLocaleString()}
          sub="across all events"
        />
      </div>

      {/* Vendor KPI row */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 32 }}>
        <StatCard
          label="Vendors in DB"
          value={(vendor_stats.total || 0).toLocaleString()}
          sub="across all cities"
          color="var(--navy)"
        />
        <StatCard
          label="With Email"
          value={`${vendor_stats.with_email || 0}`}
          sub={`${vendor_stats.email_rate || 0}% reachable`}
          color="var(--success)"
        />
        {Object.entries(vendor_stats.by_category || {}).map(([cat, count]) => (
          <StatCard
            key={cat}
            label={cat.charAt(0).toUpperCase() + cat.slice(1)}
            value={count}
            sub="vendors"
          />
        ))}
      </div>

      {/* Charts + Events table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>

        {/* By city */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <BarChart
            data={vendor_stats.by_city}
            label="Vendors by city"
            color="#6366F1"
          />
        </div>

        {/* By status + type */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: 28,
        }}>
          <BarChart
            data={stats.by_status}
            label="Events by status"
            color="#1565C0"
          />
          <BarChart
            data={stats.by_type}
            label="Events by type"
            color="#16A34A"
          />
        </div>
      </div>

      {/* Monthly trend */}
      {Object.keys(stats.monthly_trend || {}).length > 0 && (
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px', marginBottom: 24,
        }}>
          <BarChart
            data={stats.monthly_trend}
            label="Events per month"
            color="#6366F1"
          />
        </div>
      )}

      {/* Events table */}
      <div style={{
        background: 'white', borderRadius: 16, border: '1px solid var(--border)',
        padding: '24px 28px',
      }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--navy)', marginBottom: 16 }}>
          All Events
        </div>
        {events.length === 0 ? (
          <p style={{ fontSize: 14, color: 'var(--text-light)', textAlign: 'center', padding: '32px 0' }}>
            No events yet — run the pipeline to create your first event.
          </p>
        ) : (
          events.map(e => <EventRow key={e.id} event={e} />)
        )}
      </div>
    </div>
  )
}
