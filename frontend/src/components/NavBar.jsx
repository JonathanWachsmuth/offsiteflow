export default function NavBar({ currentPage, onNavigate }) {
  const links = [
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'analytics', label: 'Analytics' },
    { key: 'wizard',    label: 'New Event' },
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
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
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--gradient)', marginLeft: 8,
        }} />
      </div>
    </nav>
  )
}
