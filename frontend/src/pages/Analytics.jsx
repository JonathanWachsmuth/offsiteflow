// Analytics — synthetic demo data for presentation
// All data is hardcoded to show what the dashboard would look like at scale

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const DEMO_DATA = {
  eventsPerMonth: { Jan: 2, Feb: 1, Mar: 3, Apr: 4, May: 2, Jun: 5, Jul: 3, Aug: 1, Sep: 4, Oct: 3, Nov: 2, Dec: 1 },
  spendPerHead:   { Jan: 185, Feb: 210, Mar: 195, Apr: 178, May: 190, Jun: 165, Jul: 172, Aug: 205, Sep: 180, Oct: 175, Nov: 188, Dec: 220 },
  categorySpend:  { Venue: 142000, Catering: 86000, Activity: 38000, Transport: 12000 },
  topVendors: [
    { name: '20 Cavendish Square', bookings: 7, category: 'Venue',    avgRating: 4.8 },
    { name: 'Eden Caterers',       bookings: 5, category: 'Catering', avgRating: 4.9 },
    { name: 'Salters Events',      bookings: 4, category: 'Catering', avgRating: 4.7 },
    { name: 'Team Tactics',        bookings: 4, category: 'Activity', avgRating: 4.6 },
    { name: '30 Euston Square',    bookings: 3, category: 'Venue',    avgRating: 4.5 },
  ],
  kpis: {
    totalEvents: 31,
    totalSpend: 278000,
    avgPerHead: 188,
    avgSatisfaction: 4.6,
    budgetUtilisation: 87,
    vendorsUsed: 42,
  },
  upcomingEvents: [
    { name: 'Q2 Strategy Offsite',   date: '2026-05-14', headcount: 45, budget: 25000, status: 'sourcing' },
    { name: 'Summer Team Social',    date: '2026-06-20', headcount: 80, budget: 12000, status: 'booked' },
    { name: 'New Hire Onboarding',   date: '2026-07-03', headcount: 20, budget: 5000,  status: 'sourcing' },
  ],
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{
      background: 'white', borderRadius: 14, border: '1px solid var(--border)',
      boxShadow: '0 2px 8px rgba(13,27,62,0.05)', padding: '22px 24px',
      flex: 1, minWidth: 150,
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

function HorizontalBar({ data, label, color = '#6366F1', prefix = '' }) {
  const max = Math.max(...Object.values(data))
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
        {label}
      </div>
      {Object.entries(data).map(([key, val]) => (
        <div key={key} style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ fontSize: 13, color: 'var(--text-dark)', fontWeight: 500 }}>{key}</span>
            <span style={{ fontSize: 13, color: 'var(--text-mid)', fontWeight: 600 }}>{prefix}{val.toLocaleString()}</span>
          </div>
          <div style={{ height: 8, background: '#F3F4F6', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: 4,
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

function MiniBarChart({ data, label, color = '#6366F1', prefix = '' }) {
  const max = Math.max(...Object.values(data))
  const entries = Object.entries(data)
  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
        {label}
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 120 }}>
        {entries.map(([key, val]) => (
          <div key={key} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ fontSize: 10, color: 'var(--text-mid)', fontWeight: 600, marginBottom: 4 }}>
              {prefix}{val}
            </div>
            <div style={{
              width: '100%', maxWidth: 32, borderRadius: '4px 4px 0 0',
              background: `linear-gradient(180deg, ${color}, ${color}66)`,
              height: `${Math.max(4, (val / max) * 100)}px`,
              transition: 'height 0.6s ease',
            }} />
            <div style={{ fontSize: 10, color: 'var(--text-light)', marginTop: 4 }}>{key}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function GaugeCard({ label, value, max = 100, color = '#6366F1' }) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  return (
    <div style={{
      background: 'white', borderRadius: 16, border: '1px solid var(--border)',
      padding: '24px 28px', textAlign: 'center',
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 16 }}>
        {label}
      </div>
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <svg width="120" height="70" viewBox="0 0 120 70">
          <path d="M10 65 A50 50 0 0 1 110 65" fill="none" stroke="#E5E7EB" strokeWidth="10" strokeLinecap="round" />
          <path d="M10 65 A50 50 0 0 1 110 65" fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
            strokeDasharray={`${pct * 1.57} 157`} />
        </svg>
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, fontSize: 24, fontWeight: 800, color: 'var(--navy)' }}>
          {value}%
        </div>
      </div>
    </div>
  )
}

export default function Analytics() {
  const d = DEMO_DATA
  const k = d.kpis

  return (
    <div className="page-container wide">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: 28, fontWeight: 700, color: 'var(--navy)', marginBottom: 6 }}>
              Analytics
            </h2>
            <p style={{ fontSize: 15, color: 'var(--text-mid)' }}>
              Company-wide event insights and vendor performance
            </p>
          </div>
          <span style={{
            fontSize: 11, fontWeight: 600, color: 'var(--text-light)',
            background: '#F3F4F6', borderRadius: 8, padding: '6px 12px',
          }}>
            Demo data — 12 months
          </span>
        </div>
      </div>

      {/* KPI row */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Events Planned" value={k.totalEvents} sub="this year" />
        <StatCard label="Total Spend" value={`£${k.totalSpend.toLocaleString()}`} sub="across all events" color="var(--blue)" />
        <StatCard label="Avg. Per Head" value={`£${k.avgPerHead}`} sub="per event" color="var(--purple)" />
        <StatCard label="Satisfaction" value={`${k.avgSatisfaction}/5`} sub="avg. vendor rating" color="#16A34A" />
        <StatCard label="Vendors Used" value={k.vendorsUsed} sub="unique vendors" />
      </div>

      {/* Charts row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <MiniBarChart data={d.eventsPerMonth} label="Events per month" color="#6366F1" />
        </div>
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <MiniBarChart data={d.spendPerHead} label="Avg. spend per head (£)" color="#1565C0" prefix="£" />
        </div>
      </div>

      {/* Category spend + Gauge */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 24 }}>
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <HorizontalBar data={d.categorySpend} label="Spend by category" color="#6366F1" prefix="£" />
        </div>
        <GaugeCard label="Budget Utilisation" value={k.budgetUtilisation} color="#6366F1" />
      </div>

      {/* Top vendors + Upcoming events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Top vendors */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
            Most booked vendors
          </div>
          {d.topVendors.map((v, i) => (
            <div key={v.name} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '10px 0', borderBottom: i < d.topVendors.length - 1 ? '1px solid var(--border)' : 'none',
            }}>
              <div>
                <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>{v.name}</span>
                <span style={{ fontSize: 12, color: 'var(--text-light)', marginLeft: 8 }}>{v.category}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 12, color: 'var(--text-mid)' }}>&#9733; {v.avgRating}</span>
                <span style={{
                  background: '#F5F7FF', borderRadius: 8, padding: '2px 10px',
                  fontSize: 13, fontWeight: 700, color: 'var(--blue)',
                }}>
                  {v.bookings}x
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Upcoming events */}
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
            Upcoming events
          </div>
          {d.upcomingEvents.map(e => {
            const sc = e.status === 'booked'
              ? { bg: '#F0FDF4', color: '#16A34A' }
              : { bg: '#EFF6FF', color: '#1565C0' }
            return (
              <div key={e.name} style={{
                padding: '12px 0',
                borderBottom: '1px solid var(--border)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>{e.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-light)', marginTop: 2 }}>
                      {e.date} &middot; {e.headcount} people &middot; £{e.budget.toLocaleString()}
                    </div>
                  </div>
                  <span style={{
                    background: sc.bg, color: sc.color,
                    borderRadius: 20, padding: '3px 12px',
                    fontSize: 12, fontWeight: 600,
                  }}>
                    {e.status}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
