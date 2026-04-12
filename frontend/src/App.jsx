import { useState, useEffect } from 'react'
import NavBar from './components/NavBar'
import Stepper from './components/Stepper'
import CommandPalette from './components/CommandPalette'
import Step1Brief from './pages/Step1Brief'
import Step2Vendors from './pages/Step2Vendors'
import Step3RFQs from './pages/Step3RFQs'
import Step4Shortlist from './pages/Step4Shortlist'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import VendorSearch from './pages/VendorSearch'
import EventRSVP from './pages/EventRSVP'

export default function App() {
  // Page-level navigation: dashboard | wizard | analytics | shortlist | vendors | rsvp
  const [page, setPage] = useState('wizard')

  // Command palette (Cmd+K)
  const [paletteOpen, setPaletteOpen] = useState(false)

  // Wizard state
  const [step,            setStep]            = useState(1)
  const [brief,           setBrief]           = useState(null)
  const [routingResult,   setRoutingResult]   = useState(null)
  const [selected,        setSelected]        = useState({})
  const [selectedIds,     setSelectedIds]     = useState([])
  const [selectedVendors, setSelectedVendors] = useState([])

  // Global Cmd+K listener
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setPaletteOpen(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  function getAllVendors(result) {
    if (!result?.matches) return []
    return Object.values(result.matches).flat()
  }

  function handleStep1Complete(result, parsedBrief) {
    setRoutingResult(result)
    setBrief(parsedBrief)
    const init = {}
    getAllVendors(result).forEach(v => { init[v.id] = false })
    setSelected(init)
    setStep(2)
  }

  function handleToggle(vendorId) {
    setSelected(prev => ({ ...prev, [vendorId]: !prev[vendorId] }))
  }

  function handleStep2Continue(ids) {
    setSelectedIds(ids)
    const allVendors = getAllVendors(routingResult)
    setSelectedVendors(allVendors.filter(v => ids.includes(v.id)))
    setStep(3)
  }

  function handleRFQsSent() {
    setPage('dashboard')
  }

  function handleFindBestMatch() {
    setPage('shortlist')
  }

  function handleNewEvent() {
    setPage('wizard')
    setStep(1)
    setBrief(null)
    setRoutingResult(null)
    setSelected({})
    setSelectedIds([])
    setSelectedVendors([])
  }

  function handleNavigate(target) {
    if (target === 'wizard') {
      if (!brief) {
        setStep(1)
      }
      setPage('wizard')
    } else {
      setPage(target)
    }
  }

  return (
    <div>
      <NavBar
        currentPage={page}
        onNavigate={handleNavigate}
        onOpenSearch={() => setPaletteOpen(true)}
      />
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onNavigateVendors={() => setPage('vendors')}
      />
      <div style={{ paddingTop: 64 }}>

        {/* ─── Wizard Flow ─── */}
        {page === 'wizard' && (
          <>
            <Stepper currentStep={step} />

            {step === 1 && (
              <Step1Brief onComplete={handleStep1Complete} />
            )}

            {step === 2 && routingResult && (
              <Step2Vendors
                routingResult={routingResult}
                brief={brief}
                selected={selected}
                onToggle={handleToggle}
                onBack={() => setStep(1)}
                onContinue={handleStep2Continue}
              />
            )}

            {step === 3 && (
              <Step3RFQs
                selectedVendors={selectedVendors}
                brief={brief}
                onBack={() => setStep(2)}
                onContinue={handleRFQsSent}
              />
            )}
          </>
        )}

        {/* ─── Dashboard (RFQ tracking) ─── */}
        {page === 'dashboard' && (
          <Dashboard
            brief={brief}
            selectedVendors={selectedVendors}
            onFindBestMatch={handleFindBestMatch}
            onNewEvent={handleNewEvent}
          />
        )}

        {/* ─── Analytics ─── */}
        {page === 'analytics' && (
          <Analytics />
        )}

        {/* ─── Vendor Database ─── */}
        {page === 'vendors' && (
          <VendorSearch />
        )}

        {/* ─── RSVP & Chat ─── */}
        {page === 'rsvp' && (
          <EventRSVP />
        )}

        {/* ─── Shortlist (Best Match) ─── */}
        {page === 'shortlist' && (
          <Step4Shortlist
            brief={brief}
            selectedVendorIds={selectedIds}
            onBack={() => setPage('dashboard')}
            onRestart={handleNewEvent}
          />
        )}
      </div>
    </div>
  )
}
