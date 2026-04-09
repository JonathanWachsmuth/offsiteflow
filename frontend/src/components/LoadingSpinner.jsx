export default function LoadingSpinner({ text }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '60px 24px', gap: 16,
    }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '3px solid var(--border)',
        borderTopColor: 'var(--blue)',
        animation: 'spin 0.8s linear infinite',
      }} />
      {text && (
        <p style={{ fontSize: 15, color: 'var(--text-mid)' }}>{text}</p>
      )}
    </div>
  )
}
