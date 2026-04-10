# OffsiteFlow — Product Roadmap

## Architecture
- **Frontend**: React 19 + Vite → deployed on Vercel
- **Backend**: FastAPI (Python) → deployed on Railway
- **Database**: Supabase (Postgres) — replaces local SQLite
- **AI**: Claude claude-sonnet-4-20250514 for brief parsing, vendor ranking, RFQ generation, quote extraction

---

## Core Pipeline (5-stage)

```
Brief text
  → [1] parse_brief()        LLM: free text → structured JSON
  → [2] prefilter()          SQL: filter vendors by city + category
  → [3] rank_vendors()       LLM: semantic ranking of candidates
  → [4] generate_rfq()       LLM: branded email per vendor (preview only, no send)
  → [5] parse_quote()        Template: synthetic response → structured quote
  → [6] normalise_quotes()   Rule-based: VAT, per-head, completeness
  → [7] rank_quotes()        Scoring: budget fit, completeness, confidence, value
  → [8] generate_recommendation() LLM: 2-3 sentence planner summary
```

---

## Status by Feature

### ✅ Done
- [x] Step 1 — Brief input with demo brief button
- [x] Step 2 — Vendor selection grid (per category)
- [x] Step 3 — RFQ email previews (LLM, parallel, no sending)
- [x] Step 4 — Per-category winner cards (brand colors, no emojis)
- [x] Budget bar with remaining/over-budget indicator
- [x] AI recommendation block
- [x] Per-vendor synthetic quotes using real DB fields
- [x] Supabase migration (schema + 2042 vendors)
- [x] Supabase client replacing SQLite throughout pipeline

### 🔧 In Progress
- [ ] Shortlist speed fix — bypass LLM for synthetic quote parsing
- [ ] Vercel deployment (frontend)
- [ ] Railway deployment (FastAPI backend)

### 📋 Planned — Phase 2: Events + RSVP

#### Event Booking Summary
After the user confirms vendors at Step 4, create an "event confirmed" state:
- Summary card: event name, dates, headcount, city
- Selected winners per category (venue, catering, activity, transport)
- Total budget vs. spend
- Status: "Planning in progress"

#### RSVP Module
Route: `/events/:id/rsvp`
- Attendee list with RSVP status (Attending / Declined / Awaiting)
- Dietary preferences breakdown (synthetic seed for demo)
- Invite link (copyable)
- Synthetic seed: 45 attendees, ~80% accepted, dietary split realistic
- Data stored in Supabase `rsvp` table

#### Event Planning Chat
Route: `/events/:id/chat`
- Message thread per event (Supabase realtime)
- For demo: pre-seeded messages from synthetic team members
- Topics: dietary confirmations, logistics questions, schedule
- New messages stored in Supabase `messages` table

### 📋 Planned — Phase 3: Analytics Dashboard

Route: `/dashboard`
Accessible from NavBar "Dashboard" link.

#### Company Event Analytics (synthetic seed for demo)
- Events planned this year — bar chart by month (12 months)
- Average spend per head — trend line (rolling 6 months)
- Top vendor categories — donut chart
- Budget utilisation — gauge (actual vs. planned)
- Upcoming events list — 3-4 cards with dates + status
- Most used vendors — ranked list with repeat booking count

All data seeded synthetically in `analytics_seed.js` for presentation.
Replace with real Supabase queries once real events exist.

### 📋 Planned — Phase 4: Polish + Auth

- Supabase Auth (magic link / Google OAuth)
- Organisation setup flow (name, size, industry, budget rules)
- Multi-user: planner + approver roles
- Event approval workflow
- Vendor review submission
- Email sending (when approved by user, via SMTP)
- PDF export of shortlist

---

## Infrastructure Cost Guide

| Service | Free Tier | When to upgrade |
|---|---|---|
| Supabase | 500MB DB, 2 projects, 50k MAU | When DB > 500MB or need >2 projects (Pro: $25/mo) |
| Vercel | Unlimited deploys, 100GB bandwidth | Only if enterprise SSO needed (free is plenty) |
| Railway | $5 credit free, then ~$5/mo hobby | Immediately — free credit runs out in days |
| Anthropic | Pay-per-use | No tier needed, charged per token |

**Bottom line**: Free everywhere except Railway ($5/mo). No premium needed for demo.

---

## Environment Variables

### Backend (.env)
```
ANTHROPIC_API_KEY=...
SUPABASE_URL=https://kyrodpcviaximcbuzykf.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
TALLY_FORM_URL=https://tally.so/r/PdY7Je
SMTP_EMAIL=...
SMTP_PASSWORD=...
```

### Frontend (.env)
```
VITE_SUPABASE_URL=https://kyrodpcviaximcbuzykf.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=https://your-railway-app.railway.app
```
