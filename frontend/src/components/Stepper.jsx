const STEPS = ['Describe Event', 'Select Vendors', 'Send RFQs']

export default function Stepper({ currentStep }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      padding: '32px 0 24px', maxWidth: 480, margin: '0 auto',
    }}>
      {STEPS.map((label, i) => {
        const step     = i + 1
        const isDone   = step < currentStep
        const isActive = step === currentStep

        const circleStyle = {
          width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 16, fontWeight: 700,
          ...(isDone || isActive
            ? { background: 'var(--gradient)', color: 'white' }
            : { background: '#E2E6F0', color: 'var(--text-light)' }),
        }

        const labelStyle = {
          fontSize: 13, fontWeight: 500, textAlign: 'center', marginTop: 8,
          color: (isDone || isActive) ? 'var(--text-dark)' : 'var(--text-light)',
          whiteSpace: 'nowrap',
        }

        return (
          <div key={step} style={{ display: 'flex', alignItems: 'flex-start', flex: step < STEPS.length ? '1' : '0' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={circleStyle}>
                {isDone ? '✓' : step}
              </div>
              <div style={labelStyle}>{label}</div>
            </div>
            {step < STEPS.length && (
              <div style={{
                flex: 1, height: 2, marginTop: 20, marginLeft: 8, marginRight: 8,
                background: isDone ? 'var(--gradient)' : 'var(--border)',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
