import { useState } from 'react'
import NavBar from './components/NavBar'
import Stepper from './components/Stepper'
import Step1Brief from './pages/Step1Brief'
import Step2Vendors from './pages/Step2Vendors'
import Step3RFQs from './pages/Step3RFQs'
import Step4Shortlist from './pages/Step4Shortlist'

export default function App() {
  const [step,           setStep]           = useState(1)
  const [brief,          setBrief]          = useState(null)
  const [routingResult,  setRoutingResult]  = useState(null)
  const [selected,       setSelected]       = useState({})   // vendorId -> bool
  const [selectedIds,    setSelectedIds]    = useState([])
  const [selectedVendors, setSelectedVendors] = useState([])

  // Flatten all vendors from routingResult for lookup
  function getAllVendors(result) {
    if (!result?.matches) return []
    return Object.values(result.matches).flat()
  }

  function handleStep1Complete(result, parsedBrief) {
    setRoutingResult(result)
    setBrief(parsedBrief)
    // Default: select vendors that have an email
    const init = {}
    getAllVendors(result).forEach(v => {
      init[v.id] = Boolean(v.email)
    })
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

  function handleRestart() {
    setStep(1)
    setBrief(null)
    setRoutingResult(null)
    setSelected({})
    setSelectedIds([])
    setSelectedVendors([])
  }

  return (
    <div>
      <NavBar />
      <div style={{ paddingTop: 64 }}>
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
            onContinue={() => setStep(4)}
          />
        )}

        {step === 4 && (
          <Step4Shortlist
            brief={brief}
            selectedVendorIds={selectedIds}
            onBack={() => setStep(3)}
            onRestart={handleRestart}
          />
        )}
      </div>
    </div>
  )
}
