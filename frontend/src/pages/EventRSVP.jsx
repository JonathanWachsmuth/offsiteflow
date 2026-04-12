import { useState } from 'react'

// ─── Synthetic demo data ───────────────────────────────────

const DEMO_EVENT = {
  name: 'Q2 Strategy Offsite',
  date: '14–15 May 2026',
  location: '20 Cavendish Square, London',
  headcount: 45,
  organiser: 'Sarah Chen',
}

const DEMO_ATTENDEES = [
  { id: 1,  name: 'Sarah Chen',       email: 'sarah@company.com',      role: 'Organiser', status: 'going',   dietaryNotes: '' },
  { id: 2,  name: 'James Wilson',      email: 'james.w@company.com',    role: 'Presenter', status: 'going',   dietaryNotes: 'Vegetarian' },
  { id: 3,  name: 'Emily Zhang',       email: 'emily.z@company.com',    role: 'Attendee',  status: 'going',   dietaryNotes: '' },
  { id: 4,  name: 'Michael Brooks',    email: 'michael.b@company.com',  role: 'Attendee',  status: 'going',   dietaryNotes: 'Gluten-free' },
  { id: 5,  name: 'Rachel Kumar',      email: 'rachel.k@company.com',   role: 'Attendee',  status: 'going',   dietaryNotes: '' },
  { id: 6,  name: 'David Park',        email: 'david.p@company.com',    role: 'Presenter', status: 'going',   dietaryNotes: '' },
  { id: 7,  name: 'Olivia Müller',     email: 'olivia.m@company.com',   role: 'Attendee',  status: 'maybe',   dietaryNotes: 'Vegan' },
  { id: 8,  name: 'Tom Anderson',      email: 'tom.a@company.com',      role: 'Attendee',  status: 'maybe',   dietaryNotes: '' },
  { id: 9,  name: 'Priya Sharma',      email: 'priya.s@company.com',    role: 'Attendee',  status: 'going',   dietaryNotes: 'Nut allergy' },
  { id: 10, name: 'Alex Johnson',      email: 'alex.j@company.com',     role: 'Attendee',  status: 'declined', dietaryNotes: '' },
  { id: 11, name: 'Sophie Martin',     email: 'sophie.m@company.com',   role: 'Attendee',  status: 'going',   dietaryNotes: '' },
  { id: 12, name: 'Lucas Silva',       email: 'lucas.s@company.com',    role: 'Attendee',  status: 'pending',  dietaryNotes: '' },
  { id: 13, name: 'Mia Thompson',      email: 'mia.t@company.com',      role: 'Attendee',  status: 'pending',  dietaryNotes: '' },
  { id: 14, name: 'Nathan Lee',        email: 'nathan.l@company.com',   role: 'Attendee',  status: 'going',   dietaryNotes: 'Halal' },
  { id: 15, name: 'Anna Kowalski',     email: 'anna.k@company.com',     role: 'Attendee',  status: 'pending',  dietaryNotes: '' },
]

const DEMO_MESSAGES = [
  { id: 1, author: 'Sarah Chen',    time: '10 Apr, 14:32', text: 'Hi everyone! Just confirmed the venue — 20 Cavendish Square. Agenda will be shared by Friday.' },
  { id: 2, author: 'James Wilson',  time: '10 Apr, 15:10', text: 'Great choice! Do we have AV sorted for the presentations? I need HDMI and a clicker.' },
  { id: 3, author: 'Sarah Chen',    time: '10 Apr, 15:15', text: 'Yes, AV is included with the venue. They have a 75\" display + projector in the main room. Clickers provided.' },
  { id: 4, author: 'Emily Zhang',   time: '10 Apr, 16:42', text: 'Can we add a 30-min networking break after the morning sessions? Last time felt quite packed.' },
  { id: 5, author: 'David Park',    time: '11 Apr, 09:08', text: 'Quick reminder — please fill in dietary requirements if you haven\'t already. Catering needs final numbers by Friday.' },
  { id: 6, author: 'Olivia Müller', time: '11 Apr, 10:22', text: 'I\'m still trying to sort childcare for that day. Will confirm by tomorrow.' },
  { id: 7, author: 'Rachel Kumar',  time: '11 Apr, 11:45', text: 'Is there a dress code? Smart casual?' },
  { id: 8, author: 'Sarah Chen',    time: '11 Apr, 12:00', text: 'Smart casual is perfect. And yes @Emily, great idea — I\'ll add networking breaks to the agenda.' },
]

const STATUS_CONFIG = {
  going:    { label: 'Going',    bg: '#F0FDF4', color: '#16A34A', border: '#BBF7D0' },
  maybe:    { label: 'Maybe',    bg: '#FFF7ED', color: '#EA580C', border: '#FED7AA' },
  declined: { label: 'Declined', bg: '#FEF2F2', color: '#DC2626', border: '#FECACA' },
  pending:  { label: 'Pending',  bg: '#F3F4F6', color: '#6B7280', border: '#E5E7EB' },
}

// ─── Components ────────────────────────────────────────────

function AttendeeRow({ attendee, onStatusChange }) {
  const s = STATUS_CONFIG[attendee.status]
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '12px 0', borderBottom: '1px solid var(--border)',
      gap: 12, flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--gradient)', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontSize: 14, fontWeight: 700, color: 'white', flexShrink: 0,
        }}>
          {attendee.name.split(' ').map(n => n[0]).join('')}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
            {attendee.name}
            {attendee.role !== 'Attendee' && (
              <span style={{
                marginLeft: 8, fontSize: 11, fontWeight: 600,
                color: 'var(--blue)', background: '#EFF6FF',
                padding: '1px 8px', borderRadius: 6,
              }}>
                {attendee.role}
              </span>
            )}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-light)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {attendee.email}
            {attendee.dietaryNotes && (
              <span style={{ marginLeft: 8, color: 'var(--warning)' }}>
                {attendee.dietaryNotes}
              </span>
            )}
          </div>
        </div>
      </div>
      <select
        value={attendee.status}
        onChange={e => onStatusChange(attendee.id, e.target.value)}
        style={{
          background: s.bg, color: s.color, border: `1px solid ${s.border}`,
          borderRadius: 8, padding: '4px 10px', fontSize: 12, fontWeight: 600,
          fontFamily: 'Inter, sans-serif', cursor: 'pointer', outline: 'none',
        }}
      >
        <option value="going">Going</option>
        <option value="maybe">Maybe</option>
        <option value="declined">Declined</option>
        <option value="pending">Pending</option>
      </select>
    </div>
  )
}

function ChatMessage({ msg }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: 'var(--gradient)', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 700, color: 'white',
        }}>
          {msg.author.split(' ').map(n => n[0]).join('')}
        </div>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>{msg.author}</span>
        <span style={{ fontSize: 11, color: 'var(--text-light)' }}>{msg.time}</span>
      </div>
      <div style={{
        marginLeft: 36, fontSize: 14, color: 'var(--text-dark)',
        lineHeight: 1.6, background: '#F8FAFF', borderRadius: 10,
        padding: '10px 14px', border: '1px solid var(--border)',
      }}>
        {msg.text}
      </div>
    </div>
  )
}

// ─── Main page ─────────────────────────────────────────────

export default function EventRSVP() {
  const [attendees, setAttendees] = useState(DEMO_ATTENDEES)
  const [messages, setMessages]   = useState(DEMO_MESSAGES)
  const [newMsg, setNewMsg]       = useState('')
  const [tab, setTab]             = useState('rsvp') // rsvp | chat
  const [filter, setFilter]       = useState('all')

  const counts = {
    going:    attendees.filter(a => a.status === 'going').length,
    maybe:    attendees.filter(a => a.status === 'maybe').length,
    declined: attendees.filter(a => a.status === 'declined').length,
    pending:  attendees.filter(a => a.status === 'pending').length,
  }

  const filteredAttendees = filter === 'all'
    ? attendees
    : attendees.filter(a => a.status === filter)

  function handleStatusChange(id, newStatus) {
    setAttendees(prev => prev.map(a =>
      a.id === id ? { ...a, status: newStatus } : a
    ))
  }

  function handleSendMessage(e) {
    e.preventDefault()
    if (!newMsg.trim()) return
    const now = new Date()
    const timeStr = `${now.getDate()} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][now.getMonth()]}, ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`
    setMessages(prev => [...prev, {
      id: prev.length + 1,
      author: 'You',
      time: timeStr,
      text: newMsg.trim(),
    }])
    setNewMsg('')
  }

  const dietary = attendees
    .filter(a => a.status === 'going' && a.dietaryNotes)
    .map(a => ({ name: a.name, notes: a.dietaryNotes }))

  return (
    <div className="page-container wide">
      {/* Event header */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1b4b 0%, #2d3a8c 100%)',
        borderRadius: 16, padding: '28px 32px', marginBottom: 24, color: 'white',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 700 }}>{DEMO_EVENT.name}</div>
            <div style={{ fontSize: 14, opacity: 0.8, marginTop: 6 }}>
              {DEMO_EVENT.date} &middot; {DEMO_EVENT.location}
            </div>
            <div style={{ fontSize: 13, opacity: 0.6, marginTop: 4 }}>
              Organised by {DEMO_EVENT.organiser} &middot; {DEMO_EVENT.headcount} expected
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            {Object.entries(counts).map(([key, count]) => {
              const s = STATUS_CONFIG[key]
              return (
                <div key={key} style={{
                  textAlign: 'center', padding: '8px 16px',
                  background: 'rgba(255,255,255,0.12)', borderRadius: 10,
                }}>
                  <div style={{ fontSize: 22, fontWeight: 800 }}>{count}</div>
                  <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>{s.label}</div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Tab switcher */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
        {[
          { key: 'rsvp', label: 'RSVP List' },
          { key: 'chat', label: 'Event Chat' },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '10px 20px', borderRadius: 10, border: 'none',
              fontSize: 14, fontWeight: tab === t.key ? 600 : 400,
              fontFamily: 'Inter, sans-serif', cursor: 'pointer',
              background: tab === t.key ? 'var(--navy)' : '#F3F4F6',
              color: tab === t.key ? 'white' : 'var(--text-mid)',
              transition: 'all 0.15s',
            }}
          >
            {t.label}
            {t.key === 'chat' && (
              <span style={{
                marginLeft: 6, fontSize: 11, fontWeight: 700,
                background: tab === t.key ? 'rgba(255,255,255,0.2)' : '#E5E7EB',
                borderRadius: 8, padding: '1px 7px',
              }}>
                {messages.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* RSVP Tab */}
      {tab === 'rsvp' && (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20 }}>
          {/* Attendee list */}
          <div style={{
            background: 'white', borderRadius: 16, border: '1px solid var(--border)',
            padding: '24px 28px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)' }}>
                {filteredAttendees.length} attendee{filteredAttendees.length !== 1 ? 's' : ''}
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {['all', 'going', 'maybe', 'pending', 'declined'].map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    style={{
                      padding: '4px 10px', borderRadius: 6,
                      border: filter === f ? '1px solid var(--blue)' : '1px solid var(--border)',
                      background: filter === f ? '#EFF6FF' : 'transparent',
                      fontSize: 12, fontWeight: 500, color: filter === f ? 'var(--blue)' : 'var(--text-light)',
                      cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                      textTransform: 'capitalize',
                    }}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            {filteredAttendees.map(a => (
              <AttendeeRow key={a.id} attendee={a} onStatusChange={handleStatusChange} />
            ))}
          </div>

          {/* Sidebar: dietary + quick stats */}
          <div>
            <div style={{
              background: 'white', borderRadius: 16, border: '1px solid var(--border)',
              padding: '24px 28px', marginBottom: 20,
            }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
                Response Rate
              </div>
              <div style={{ height: 8, background: '#F3F4F6', borderRadius: 4, overflow: 'hidden', marginBottom: 8 }}>
                <div style={{
                  height: '100%', borderRadius: 4,
                  background: 'var(--gradient)',
                  width: `${((counts.going + counts.declined) / attendees.length) * 100}%`,
                  transition: 'width 0.4s',
                }} />
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-light)' }}>
                {counts.going + counts.declined + counts.maybe} of {attendees.length} responded
                ({counts.pending} pending)
              </div>
            </div>

            {dietary.length > 0 && (
              <div style={{
                background: 'white', borderRadius: 16, border: '1px solid var(--border)',
                padding: '24px 28px',
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 14 }}>
                  Dietary Requirements
                </div>
                {dietary.map(d => (
                  <div key={d.name} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '8px 0', borderBottom: '1px solid var(--border)',
                    fontSize: 13,
                  }}>
                    <span style={{ color: 'var(--navy)', fontWeight: 500 }}>{d.name}</span>
                    <span style={{ color: 'var(--warning)', fontWeight: 600 }}>{d.notes}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Chat Tab */}
      {tab === 'chat' && (
        <div style={{
          background: 'white', borderRadius: 16, border: '1px solid var(--border)',
          padding: '24px 28px',
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-mid)', marginBottom: 20 }}>
            Event Discussion
          </div>

          <div style={{ maxHeight: 500, overflowY: 'auto', marginBottom: 20 }}>
            {messages.map(m => <ChatMessage key={m.id} msg={m} />)}
          </div>

          <form onSubmit={handleSendMessage} style={{
            display: 'flex', gap: 10, borderTop: '1px solid var(--border)', paddingTop: 16,
          }}>
            <input
              value={newMsg}
              onChange={e => setNewMsg(e.target.value)}
              placeholder="Type a message..."
              style={{
                flex: 1, padding: '12px 16px', borderRadius: 10,
                border: '1px solid var(--border)', fontSize: 14,
                fontFamily: 'Inter, sans-serif', outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={!newMsg.trim()}
              style={{
                background: newMsg.trim() ? 'var(--gradient)' : '#E5E7EB',
                border: 'none', borderRadius: 10, padding: '12px 24px',
                fontSize: 14, fontWeight: 600, color: 'white',
                cursor: newMsg.trim() ? 'pointer' : 'default',
                fontFamily: 'Inter, sans-serif', transition: 'background 0.15s',
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
