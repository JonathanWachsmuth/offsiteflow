export default function NavBar({ currentPage, onNavigate, onOpenSearch }) {
  const links = [
    { key: 'wizard',    label: 'New Event' },
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'rsvp',      label: 'RSVP' },
    { key: 'analytics', label: 'Analytics' },
    { key: 'vendors',   label: 'Vendors' },
  ]

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 200,
      background: 'white', borderBottom: '1px solid var(--border)',
      height: 64, padding: '0 40px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    }}>
      <img
        src="/logo.png"
        alt="OffsiteFlow"
        style={{ height: 28, width: 'auto', cursor: 'pointer' }}
        onClick={() => onNavigate('dashboard')}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
        {/* Nav links */}
        {links.map(link => (
          <span
            key={link.key}
            onClick={() => onNavigate(link.key)}
            style={{
              fontSize: 14,
              color: currentPage === link.key ? 'var(--blue)' : 'var(--text-light)',
              fontWeight: currentPage === link.key ? 600 : 400,
              cursor: 'pointer',
              transition: 'color 0.15s',
            }}
          >
            {link.label}
          </span>
        ))}

        {/* Search trigger — right side */}
        <button
          onClick={onOpenSearch}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 14px', borderRadius: 8,
            border: '1px solid var(--border)', background: '#F9FAFB',
            fontSize: 13, color: 'var(--text-light)',
            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
            transition: 'border-color 0.15s',
          }}
        >
          <span>Search</span>
          <kbd style={{
            marginLeft: 4, padding: '1px 6px', borderRadius: 4,
            background: '#F3F4F6', border: '1px solid #E5E7EB',
            fontSize: 11, color: 'var(--text-light)',
          }}>
            &#8984;K
          </kbd>
        </button>

        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--gradient)', marginLeft: 4,
        }} />
      </div>
    </nav>
  )
}
