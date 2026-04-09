export default function NavBar() {
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
        style={{ height: 28, width: 'auto' }}
      />
      <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
        {['Dashboard', 'Events', 'Vendors'].map(link => (
          <span key={link} style={{
            fontSize: 14, color: 'var(--text-light)', cursor: 'pointer',
          }}>
            {link}
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
