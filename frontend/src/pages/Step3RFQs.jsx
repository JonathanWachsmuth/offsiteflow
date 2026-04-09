const PRICES = { venue: '£5,400', catering: '£4,590', activity: '£3,510', transport: '£960' }
const INCLUSIONS = {
  venue:     ['AV equipment', 'WiFi', 'Outdoor terrace'],
  catering:  ['Full catering', 'Service staff', 'Linen'],
  activity:  ['Equipment', 'Facilitators', 'Debrief'],
  transport: ['Driver', 'Fuel included'],
}
const TIMES = ['Sent 2h ago', 'Sent 4h ago', 'Sent 6h ago', 'Sent 8h ago']

function LoadingBar() {
  return (
    <div style={{ height: 4, borderRadius: 2, marginTop: 16, overflow: 'hidden' }}>
      <div style={{
        height: '100%',
        background: 'linear-gradient(90deg, #6366F1 0%, #1565C0 25%, #7EB3FF 50%, #1565C0 75%, #6366F1 100%)',
        backgroundSize: '200% 100%',
        animation: 'shimmer 1.8s linear infinite',
      }} />
    </div>
  )
}

export default function Step3RFQs({ selectedVendors, onBack, onContinue }) {
  const vendors = selectedVendors || []

  return (
    <>
      <div className="page-container narrow" style={{ paddingBottom: 100 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, color: 'var(--navy)' }}>
            RFQ Responses
          </h2>
          <p style={{ fontSize: 16, color: 'var(--text-mid)', marginTop: 8 }}>
            Track responses from your selected vendors in real-time.
          </p>
        </div>

        {vendors.map((vendor, i) => {
          const isReceived = i < 2
          const cat        = vendor.category || 'venue'
          const price      = PRICES[cat] || '£5,400'
          const inclusions = INCLUSIONS[cat] || []

          return (
            <div
              key={vendor.id}
              className="card"
              style={{ marginBottom: 12, padding: 24 }}
            >
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: 'flex-start', flexWrap: 'wrap', gap: 8,
              }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--navy)' }}>
                    {vendor.name}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-light)', marginTop: 4 }}>
                    {TIMES[i] || 'Sent recently'}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {isReceived && (
                    <span style={{ fontSize: 28, fontWeight: 800, color: 'var(--navy)' }}>
                      {price}
                    </span>
                  )}
                  {isReceived
                    ? <span className="pill-received">&#10003; Received</span>
                    : <span className="pill-pending">Pending</span>
                  }
                </div>
              </div>

              {isReceived && inclusions.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
                  {inclusions.map(inc => (
                    <span key={inc} className="pill" style={{ fontSize: 12 }}>
                      {inc}
                    </span>
                  ))}
                </div>
              )}

              {!isReceived && <LoadingBar />}
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
        <button className="btn-ghost" onClick={onBack}>&larr; Back</button>
        <button className="btn-primary" onClick={onContinue}>
          Show Best Match &rarr;
        </button>
      </div>
    </>
  )
}
