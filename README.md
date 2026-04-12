# OffsiteFlow

AI-powered corporate event planning platform. Automates vendor discovery, RFQ generation, response tracking, and shortlist recommendations — from event brief to booked vendors.

**Live:** Deployed on Vercel (frontend) + Render (API) + Supabase (database)

---

## Features

- **AI Brief Parsing** — Describe your event in natural language; Claude extracts structured requirements (headcount, budget, city, categories)
- **Smart Vendor Matching** — Matches your brief against 2,000+ vendors across venue, catering, activity, and transport categories
- **RFQ Generation** — AI-generated personalised email drafts for each vendor, editable before sending
- **Dashboard** — Track RFQ status (sent, opened, replied) per vendor with category grouping
- **Vendor Database** — Full searchable vendor directory with filters (category, city, rating, email availability)
- **Cmd+K Search** — Global vendor search overlay accessible from anywhere
- **Vendor Profiles** — Detailed vendor pages with contact info, capacity, pricing, and personal notes
- **RSVP & Event Chat** — Internal event organisation with attendee management and team discussion
- **Analytics** — Company-wide event insights with KPIs, spend breakdowns, and vendor performance
- **Best Match** — AI-powered shortlist ranking vendors by budget fit, completeness, and value

---

## Tech Stack

| Layer     | Technology                         |
|-----------|------------------------------------|
| Frontend  | React 19, Vite, Vercel             |
| Backend   | Python, FastAPI, Render            |
| Database  | Supabase (PostgreSQL)              |
| AI        | Claude Sonnet 4 (Anthropic API)    |
| Email     | Gmail SMTP                         |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (free tier works)
- Anthropic API key

### 1. Clone and install

```bash
git clone https://github.com/JonathanWachsmuth/offsiteflow.git
cd offsiteflow

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure environment

Copy `.env.example` to `.env` and add your keys:

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...

SMTP_EMAIL=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

For the frontend, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run locally

```bash
# Backend (terminal 1)
uvicorn api:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm run dev
```

The app opens at `http://localhost:5173`.

---

## API Endpoints

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/api/health`           | Health check                         |
| POST   | `/api/route`            | Parse brief, match vendors           |
| POST   | `/api/preview-rfqs`     | Generate RFQ email previews (LLM)    |
| POST   | `/api/shortlist`        | Rank vendors and build shortlist     |
| GET    | `/api/vendors`          | Search vendors with filters          |
| GET    | `/api/vendors/search`   | Quick search for Cmd+K palette       |
| GET    | `/api/vendors/{id}`     | Single vendor detail                 |

---

## Project Structure

```
offsiteflow/
├── api.py                        # FastAPI backend (all endpoints)
├── app.py                        # Legacy Streamlit UI
├── config/
│   └── settings.py               # Environment config
├── db/
│   ├── supabase_client.py        # Supabase connection singleton
│   ├── schema.sql                # Full database schema
│   └── migrations/               # SQL migrations
├── pipeline/
│   ├── match/
│   │   └── llm_router.py         # Brief parsing + vendor matching
│   ├── outreach/
│   │   ├── rfq_generator.py      # RFQ email generation (LLM)
│   │   └── email_sender.py       # SMTP sending
│   ├── extract/
│   │   └── quote_parser.py       # Response extraction
│   └── normalise/
│       ├── normaliser.py         # Price normalisation
│       └── ranker.py             # Scoring and ranking
├── frontend/
│   ├── index.html
│   ├── src/
│   │   ├── App.jsx               # Root — page routing and state
│   │   ├── api.js                # Axios instance (configurable baseURL)
│   │   ├── components/
│   │   │   ├── NavBar.jsx        # Navigation bar
│   │   │   ├── Stepper.jsx       # 3-step progress indicator
│   │   │   └── CommandPalette.jsx # Cmd+K vendor search overlay
│   │   └── pages/
│   │       ├── Step1Brief.jsx    # Event description input
│   │       ├── Step2Vendors.jsx  # Vendor selection grid
│   │       ├── Step3RFQs.jsx     # RFQ preview and editing
│   │       ├── Step4Shortlist.jsx # AI-ranked best match
│   │       ├── Dashboard.jsx     # RFQ tracking hub
│   │       ├── Analytics.jsx     # Company-wide analytics
│   │       ├── VendorSearch.jsx  # Vendor database browser
│   │       ├── VendorDetail.jsx  # Individual vendor profile
│   │       └── EventRSVP.jsx     # RSVP and event chat
│   └── public/
│       ├── logo.png
│       └── favicon.svg
├── experiments/                   # Validation experiments (A1–A12)
├── tests/                         # Unit tests (pytest)
├── vercel.json                    # Vercel deployment config
└── requirements.txt               # Python dependencies
```

---

## Deployment

**Frontend** — Auto-deploys to Vercel on push to `main`
- Build command: `cd frontend && npm install && npm run build`
- Output directory: `frontend/dist`
- Environment variable: `VITE_API_URL` pointing to Render backend

**Backend** — Auto-deploys to Render on push to `main`
- Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Environment variables: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `SMTP_EMAIL`, `SMTP_PASSWORD`

---

## Tests

```bash
pytest tests/
```

Tests mock all external calls (LLM, SMTP, database) — no credentials needed.

---

## License

Private repository. All rights reserved.
