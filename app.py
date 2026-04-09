# app.py
# ─────────────────────────────────────────────────────────────
# OffsiteFlow — Streamlit UI (redesigned)
# Run: streamlit run app.py
# ─────────────────────────────────────────────────────────────

import re
import streamlit as st

st.set_page_config(
    page_title="OffsiteFlow",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* Reset */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    line-height: 1.6;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Page background */
.stApp {
    background: #EEF0F5;
}

/* Hide default Streamlit button styles and override */
.stButton > button {
    background: linear-gradient(135deg, #6366F1, #1565C0) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 10px 24px !important;
    cursor: pointer !important;
    transition: opacity 0.2s !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    opacity: 0.92 !important;
    color: white !important;
}
.stButton > button:focus {
    box-shadow: none !important;
    color: white !important;
}

/* Back / ghost button override via key */
.back-btn .stButton > button {
    background: transparent !important;
    color: #4B5563 !important;
    border: 1px solid #E2E6F0 !important;
    font-weight: 500 !important;
}

/* Start Over button */
.start-over-btn .stButton > button {
    background: white !important;
    color: #374151 !important;
    border: 1px solid #E2E6F0 !important;
    font-weight: 500 !important;
}

/* Hide checkbox labels completely where we use custom cards */
.stCheckbox { margin: 0; }

/* Animated loading bar */
@keyframes loading {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

/* Card base */
.of-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #E2E6F0;
    box-shadow: 0 2px 12px rgba(13,27,62,0.06);
    padding: 20px 24px;
    margin-bottom: 12px;
}

/* Textarea override */
.stTextArea textarea {
    border: none !important;
    box-shadow: none !important;
    font-size: 16px !important;
    font-family: 'Inter', sans-serif !important;
    color: #0D1B3E !important;
    resize: none !important;
    background: transparent !important;
}
.stTextArea textarea:focus {
    border: none !important;
    box-shadow: none !important;
}
.stTextArea > div {
    border: none !important;
    box-shadow: none !important;
}
.stTextArea > div > div {
    border: none !important;
}

/* Remove red borders on focus */
.stTextArea > div:focus-within {
    border: none !important;
    box-shadow: none !important;
}

/* Vendor checkbox cards */
.vendor-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #E2E6F0;
    box-shadow: 0 2px 12px rgba(13,27,62,0.06);
    padding: 20px 24px;
    margin-bottom: 12px;
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s;
}
.vendor-card.selected {
    border: 2px solid #1565C0;
    box-shadow: 0 0 0 3px rgba(21,101,192,0.08);
}
.vendor-card.no-email {
    opacity: 0.75;
}

/* Pill badges */
.pill {
    display: inline-block;
    background: #F3F4F6;
    border: 1px solid #E2E6F0;
    border-radius: 20px;
    padding: 5px 13px;
    font-size: 13px;
    color: #4B5563;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 4px;
}
.pill-gradient {
    display: inline-block;
    background: linear-gradient(135deg, #6366F1, #1565C0);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: white;
    font-weight: 700;
}
.pill-received {
    display: inline-block;
    background: #DCFCE7;
    border: 1px solid #BBF7D0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 13px;
    color: #16A34A;
    font-weight: 600;
}
.pill-pending {
    display: inline-block;
    background: #FEF3C7;
    border: 1px solid #FDE68A;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 13px;
    color: #D97706;
    font-weight: 600;
}
.pill-no-email {
    display: inline-block;
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 11px;
    color: #DC2626;
    font-weight: 500;
}

/* Stat box */
.stat-box {
    background: #F5F7FF;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    flex: 1;
}

/* Selection circle */
.sel-circle {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: 2px solid #D1D5DB;
    background: white;
    display: inline-block;
}
.sel-circle.checked {
    background: linear-gradient(135deg, #6366F1, #1565C0);
    border: none;
    color: white;
    text-align: center;
    line-height: 24px;
    font-size: 12px;
}

/* Loading bar */
.loading-bar {
    height: 4px;
    border-radius: 2px;
    margin-top: 16px;
    background: linear-gradient(90deg, #6366F1, #1565C0, #7EB3FF, #6366F1);
    background-size: 200% 100%;
    animation: loading 1.8s linear infinite;
}

/* Check circle for inclusions */
.check-circle {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366F1, #1565C0);
    color: white;
    font-size: 11px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    vertical-align: middle;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "step":            1,
        "brief":           {},
        "routing_result":  None,
        "selected":        {},   # vendor_id -> bool
        "shortlist":       None,
        "brief_text":      "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────
# BRIEF PILL PARSER (regex, no LLM)
# ─────────────────────────────────────────────────────────────

def parse_brief_pills(text: str) -> list[str]:
    pills = []
    if not text.strip():
        return pills

    # Headcount
    m = re.search(r'(\d+)\s*(?:people|persons?|guests?|delegates?|attendees?)', text, re.I)
    if m:
        pills.append(f"{m.group(1)} people")

    # Duration
    m = re.search(r'(\d+)\s*(?:-\s*day|day)', text, re.I)
    if m:
        pills.append(f"{m.group(1)} day{'s' if int(m.group(1)) > 1 else ''}")

    # Location — cities or regions
    locations = [
        "London", "Manchester", "Edinburgh", "Birmingham", "Bristol",
        "Leeds", "Glasgow", "Liverpool", "Paris", "Barcelona", "Berlin",
        "Amsterdam", "Lisbon", "Europe", "UK", "Scotland"
    ]
    for loc in locations:
        if re.search(rf'\b{loc}\b', text, re.I):
            pills.append(loc)
            break

    # Budget
    m = re.search(r'[£€\$](\d[\d,]*(?:k)?)', text, re.I)
    if m:
        raw = m.group(1).replace(",", "")
        if raw.lower().endswith("k"):
            val = int(raw[:-1]) * 1000
        else:
            val = int(raw)
        if val >= 50000:
            pills.append("Large budget")
        elif val >= 15000:
            pills.append("Mid-range budget")
        else:
            pills.append("Smaller budget")

    return pills


# ─────────────────────────────────────────────────────────────
# NAV BAR
# ─────────────────────────────────────────────────────────────

def render_nav():
    st.markdown("""
    <div style="background:white; border-bottom:1px solid #E2E6F0;
                padding:16px 40px; display:flex; align-items:center;
                justify-content:space-between;">
        <span style="font-size:14px; font-weight:700; color:#0D1B3E;
                     letter-spacing:-0.3px;">OffsiteFlow</span>
        <div style="display:flex; align-items:center; gap:24px;">
            <span style="color:#9CA3AF; font-size:14px;">Dashboard</span>
            <span style="color:#9CA3AF; font-size:14px;">Events</span>
            <span style="color:#9CA3AF; font-size:14px;">Vendors</span>
            <div style="width:36px; height:36px; border-radius:50%;
                        background:linear-gradient(135deg,#6366F1,#1565C0);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PROGRESS STEPPER
# ─────────────────────────────────────────────────────────────

def render_stepper(current_step: int):
    steps = ["Describe Event", "Select Vendors", "Review RFQs", "Best Match"]

    circles = ""
    for i, label in enumerate(steps, 1):
        if i < current_step:
            circle = (
                f'<div style="width:40px;height:40px;border-radius:50%;'
                f'background:linear-gradient(135deg,#6366F1,#1565C0);'
                f'display:flex;align-items:center;justify-content:center;'
                f'color:white;font-weight:700;font-size:15px;flex-shrink:0;">&#10003;</div>'
            )
            label_color = "#0D1B3E"
            line_bg = "linear-gradient(90deg,#6366F1,#1565C0)"
        elif i == current_step:
            circle = (
                f'<div style="width:40px;height:40px;border-radius:50%;'
                f'background:linear-gradient(135deg,#6366F1,#1565C0);'
                f'display:flex;align-items:center;justify-content:center;'
                f'color:white;font-weight:700;font-size:15px;flex-shrink:0;">{i}</div>'
            )
            label_color = "#0D1B3E"
            line_bg = "#E2E6F0"
        else:
            circle = (
                f'<div style="width:40px;height:40px;border-radius:50%;'
                f'background:#E2E6F0;display:flex;align-items:center;'
                f'justify-content:center;color:#9CA3AF;font-weight:700;'
                f'font-size:15px;flex-shrink:0;">{i}</div>'
            )
            label_color = "#9CA3AF"
            line_bg = "#E2E6F0"

        step_html = (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px;">'
            f'{circle}'
            f'<span style="font-size:13px;font-weight:500;color:{label_color};'
            f'white-space:nowrap;">{label}</span></div>'
        )

        if i < len(steps):
            line_color = "linear-gradient(90deg,#6366F1,#1565C0)" if i < current_step else "#E2E6F0"
            circles += step_html
            circles += (
                f'<div style="flex:1;height:2px;background:{line_color};'
                f'margin:0 8px;margin-bottom:20px;"></div>'
            )
        else:
            circles += step_html

    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:center;'
        f'padding:32px 0 24px;max-width:600px;margin:0 auto;">'
        f'{circles}</div>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────
# STEP 1 — DESCRIBE EVENT
# ─────────────────────────────────────────────────────────────

def render_step1():
    st.markdown("""
    <div style="max-width:680px;margin:0 auto;padding:0 24px 48px;text-align:center;">
        <div style="display:inline-block;background:rgba(99,102,241,0.1);
                    border:1px solid rgba(99,102,241,0.2);border-radius:20px;
                    padding:6px 16px;font-size:13px;font-weight:500;color:#6366F1;
                    margin-bottom:20px;">
            * AI-Powered Event Planning
        </div>
        <h1 style="font-size:40px;font-weight:800;color:#0D1B3E;margin:0 0 12px;
                   line-height:1.15;">
            Describe your
            <span style="background:linear-gradient(135deg,#6366F1,#1565C0);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         background-clip:text;">perfect event</span>
        </h1>
        <p style="font-size:17px;color:#4B5563;margin:0 0 32px;">
            Tell us everything about your company event &mdash;
            we'll find the ideal vendors for you.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Card wrapper
    st.markdown("""
    <div style="max-width:680px;margin:0 auto;padding:0 24px;">
        <div style="background:white;border-radius:20px;padding:28px;
                    box-shadow:0 4px 24px rgba(13,27,62,0.08);">
    """, unsafe_allow_html=True)

    brief_text = st.text_area(
        label="Brief",
        label_visibility="collapsed",
        placeholder=(
            "e.g. We're planning a 3-day team offsite for 50 people somewhere in "
            "southern Europe. We need a venue with meeting rooms, outdoor team-building "
            "activities, catering for various dietary needs, and evening entertainment. "
            "Budget is around £30,000..."
        ),
        height=160,
        key="brief_textarea",
        value=st.session_state.brief_text,
    )
    st.session_state.brief_text = brief_text

    # Divider
    st.markdown('<hr style="border:none;border-top:1px solid #E2E6F0;margin:16px 0;">', unsafe_allow_html=True)

    # Pills + button row
    pills = parse_brief_pills(brief_text)
    pills_html = "".join(
        f'<span class="pill">{p}</span>' for p in pills
    ) if pills else '<span style="color:#9CA3AF;font-size:13px;">Start typing your brief above...</span>'

    col_pills, col_btn = st.columns([3, 1])
    with col_pills:
        st.markdown(f'<div style="padding-top:4px;">{pills_html}</div>', unsafe_allow_html=True)
    with col_btn:
        find_clicked = st.button("Find Vendors  →", key="find_vendors_btn", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    if find_clicked:
        if not brief_text.strip():
            st.warning("Please enter an event brief first.")
            return
        with st.spinner("Parsing your brief and matching vendors..."):
            from pipeline.match.llm_router import route
            try:
                result = route(brief_text)
                st.session_state.routing_result = result
                st.session_state.brief = result["brief"]
                st.session_state.brief["brief_text"] = brief_text
                # Default: select all vendors that have email
                for cat, vendors in result["matches"].items():
                    for v in vendors:
                        st.session_state.selected[v["id"]] = bool(v.get("email"))
                st.session_state.step = 2
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to match vendors: {exc}")


# ─────────────────────────────────────────────────────────────
# STEP 2 — SELECT VENDORS
# ─────────────────────────────────────────────────────────────

def render_step2():
    st.markdown("""
    <div style="text-align:center;padding:0 24px 24px;">
        <h2 style="font-size:32px;font-weight:700;color:#0D1B3E;margin:0 0 8px;">
            Matching vendors found
        </h2>
        <p style="font-size:16px;color:#4B5563;margin:0;">
            Select the vendors you'd like to send RFQs to.
            We ranked them by match score.
        </p>
    </div>
    """, unsafe_allow_html=True)

    result  = st.session_state.routing_result
    matches = result["matches"]

    # Count selected
    selected_count = sum(1 for v_id, v in st.session_state.selected.items() if v)

    # Render each category
    for category, vendors in matches.items():
        if not vendors:
            continue

        st.markdown(
            f'<div style="font-size:11px;font-weight:700;letter-spacing:1.5px;'
            f'color:#9CA3AF;text-transform:uppercase;margin:28px 0 12px;'
            f'padding:0 24px;max-width:900px;margin-left:auto;margin-right:auto;">'
            f'{category}S</div>',
            unsafe_allow_html=True
        )

        # 2-column grid via columns
        cols = st.columns(2)
        for idx, v in enumerate(vendors):
            col = cols[idx % 2]
            vendor_id  = v["id"]
            is_selected = st.session_state.selected.get(vendor_id, False)
            has_email  = bool(v.get("email"))

            score = int(round(v.get("score", 0.8) * 100))

            # Build tags
            tags_raw = []
            if v.get("tags"):
                tags_raw = [t.strip() for t in v["tags"].split(",") if t.strip()][:3]
            elif v.get("amenities"):
                tags_raw = [t.strip() for t in v["amenities"].split(",") if t.strip()][:3]

            tags_html = "".join(
                f'<span style="background:#F3F4F6;border:1px solid #E2E6F0;'
                f'border-radius:8px;padding:4px 10px;font-size:12px;color:#4B5563;'
                f'display:inline-block;margin-right:6px;margin-top:4px;">{t}</span>'
                for t in tags_raw
            )

            no_email_badge = (
                '<span class="pill-no-email" style="margin-left:8px;">no email</span>'
                if not has_email else ""
            )

            border_style = (
                "border:2px solid #1565C0;box-shadow:0 0 0 3px rgba(21,101,192,0.08);"
                if is_selected
                else "border:1px solid #E2E6F0;"
            )

            circle_html = (
                '<div style="width:24px;height:24px;border-radius:50%;'
                'background:linear-gradient(135deg,#6366F1,#1565C0);'
                'color:white;text-align:center;line-height:24px;font-size:12px;'
                'flex-shrink:0;">&#10003;</div>'
                if is_selected else
                '<div style="width:24px;height:24px;border-radius:50%;'
                'border:2px solid #D1D5DB;background:white;flex-shrink:0;"></div>'
            )

            capacity_str = ""
            if v.get("capacity_min") and v.get("capacity_max"):
                capacity_str = f'{v["capacity_min"]}–{v["capacity_max"]}'
            elif v.get("capacity_max"):
                capacity_str = f'Up to {v["capacity_max"]}'

            price_tier = ""
            if v.get("price_from"):
                p = int(v["price_from"])
                price_tier = "£" if p < 2000 else "££" if p < 5000 else "£££"

            rating_str = f'  ★ {v["rating_external"]}' if v.get("rating_external") else ""

            with col:
                st.markdown(f"""
                <div style="background:white;border-radius:16px;{border_style}
                     padding:20px 24px;margin-bottom:12px;">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;">
                        <span class="pill-gradient">{score}% match</span>
                        {circle_html}
                    </div>
                    <div style="margin-top:12px;">
                        <span style="font-size:16px;font-weight:700;color:#0D1B3E;">
                            {v['name']}
                        </span>
                        {no_email_badge}
                    </div>
                    <div style="font-size:13px;color:#6B7280;margin-top:4px;">
                        {v.get('city','')}{rating_str}
                    </div>
                    <div style="font-size:13px;color:#6B7280;margin-top:2px;">
                        {capacity_str}{' &nbsp;&middot;&nbsp; ' + price_tier if capacity_str and price_tier else price_tier}
                    </div>
                    <div style="margin-top:10px;">{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)

                # Toggle button (invisible label, rendered over card)
                toggle_label = "Deselect" if is_selected else "Select"
                if st.button(
                    toggle_label,
                    key=f"toggle_{vendor_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected[vendor_id] = not is_selected
                    st.rerun()

    # Bottom bar
    st.markdown('<div style="height:80px;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:white;border-top:1px solid #E2E6F0;
                padding:16px 24px;position:fixed;bottom:0;left:0;right:0;
                display:flex;justify-content:space-between;align-items:center;
                z-index:100;">
    </div>
    """, unsafe_allow_html=True)

    col_back, col_space, col_send = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back", key="back_2"):
            st.session_state.step = 1
            st.rerun()
    with col_send:
        selected_count = sum(1 for v, sel in st.session_state.selected.items() if sel)
        if st.button(
            f"Send RFQs ({selected_count})  →",
            key="send_rfqs_btn",
            use_container_width=True,
        ):
            if selected_count == 0:
                st.warning("Select at least one vendor first.")
            else:
                st.session_state.step = 3
                st.rerun()


# ─────────────────────────────────────────────────────────────
# STEP 3 — REVIEW RFQs (synthetic responses)
# ─────────────────────────────────────────────────────────────

# Hardcoded synthetic response data for the demo
DEMO_RESPONSES = [
    {
        "vendor_name": "Mediterranean Retreat Co.",
        "sent_ago":    "2h ago",
        "status":      "received",
        "price":       "£28,500",
        "inclusions":  ["Beachfront venue with sea views", "Private meeting rooms", "Airport transfers"],
        "category":    "venue",
        "extracted": {
            "base_price": 28500, "vat_rate": 0.0, "availability": 1,
            "capacity_offered": 100, "price_unit": "flat",
            "inclusions": ["venue", "av_equipment", "staffing", "transport"],
            "exclusions": [],
        },
    },
    {
        "vendor_name": "Alpine Events Group",
        "sent_ago":    "4h ago",
        "status":      "received",
        "price":       "£22,800",
        "inclusions":  ["Mountain hiking included", "Spa access", "Flexible schedule"],
        "category":    "activity",
        "extracted": {
            "base_price": 22800, "vat_rate": 0.0, "availability": 1,
            "capacity_offered": 80, "price_unit": "flat",
            "inclusions": ["activities", "staffing"],
            "exclusions": ["catering"],
        },
    },
    {
        "vendor_name": "Tuscan Villa Experiences",
        "sent_ago":    "Sent 6h ago",
        "status":      "pending",
        "price":       None,
        "inclusions":  [],
        "category":    "catering",
        "extracted":   None,
    },
]


def render_step3():
    st.markdown("""
    <div style="text-align:center;padding:0 24px 24px;">
        <h2 style="font-size:32px;font-weight:700;color:#0D1B3E;margin:0 0 8px;">
            RFQ Responses
        </h2>
        <p style="font-size:16px;color:#4B5563;margin:0;">
            Track responses from your selected vendors in real-time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="max-width:720px;margin:0 auto;padding:0 24px;">', unsafe_allow_html=True)

    for resp in DEMO_RESPONSES:
        if resp["status"] == "received":
            status_badge = '<span class="pill-received">&#10003; Received</span>'
            price_html   = (
                f'<span style="font-size:28px;font-weight:800;color:#0D1B3E;'
                f'margin-right:10px;">{resp["price"]}</span>'
            )
            tags_html = "".join(
                f'<span style="background:#F3F4F6;border:1px solid #E2E6F0;'
                f'border-radius:8px;padding:4px 10px;font-size:12px;color:#4B5563;'
                f'display:inline-block;margin-right:6px;margin-top:8px;">'
                f'&#128196; {inc}</span>'
                for inc in resp["inclusions"]
            )
            extra_html = f'<div style="margin-top:4px;">{tags_html}</div>'
        else:
            status_badge = '<span class="pill-pending">Pending</span>'
            price_html   = ""
            extra_html   = '<div class="loading-bar"></div>'

        st.markdown(f"""
        <div class="of-card">
            <div style="display:flex;justify-content:space-between;
                        align-items:flex-start;flex-wrap:wrap;gap:8px;">
                <div>
                    <div style="font-size:18px;font-weight:700;color:#0D1B3E;">
                        {resp['vendor_name']}
                    </div>
                    <div style="font-size:13px;color:#9CA3AF;margin-top:2px;">
                        {resp['sent_ago']}
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                    {price_html}
                    {status_badge}
                </div>
            </div>
            {extra_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:80px;"></div>', unsafe_allow_html=True)

    col_back, col_space, col_next = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back", key="back_3"):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("Show Best Match  →", key="show_best_match", use_container_width=True):
            # Run the pipeline on synthetic responses
            with st.spinner("Analysing responses..."):
                try:
                    _build_shortlist()
                    st.session_state.step = 4
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to build shortlist: {exc}")


def _build_shortlist():
    """Runs parse → normalise → rank on the demo responses."""
    from pipeline.extract.quote_parser import parse_quote
    from pipeline.normalise.normaliser import normalise_quotes
    from pipeline.normalise.ranker     import rank_quotes

    brief    = st.session_state.brief
    event_id = "demo-event"

    parsed = []
    for resp in DEMO_RESPONSES:
        if resp["status"] != "received" or resp["extracted"] is None:
            continue
        parsed.append({
            "quote_id":         None,
            "extracted":        resp["extracted"],
            "confidence_score": 0.85,
            "warnings":         [],
            "extraction_notes": "demo",
            "response_type":    "email",
            "vendor_id":        resp["vendor_name"].lower().replace(" ", "_"),
            "vendor_name":      resp["vendor_name"],
            "category":         resp["category"],
        })

    normalised = normalise_quotes(
        quotes=[
            {
                "quote_id":         q["quote_id"],
                "vendor_id":        q["vendor_id"],
                "vendor_name":      q["vendor_name"],
                "category":         q["category"],
                "confidence_score": q["confidence_score"],
                **q["extracted"],
            }
            for q in parsed
        ],
        brief      = brief,
        save_to_db = False,
    )

    ranked = rank_quotes(
        normalised_quotes = normalised["normalised_quotes"],
        brief             = brief,
        event_id          = event_id,
        save_to_db        = False,
    )
    st.session_state.shortlist = ranked


# ─────────────────────────────────────────────────────────────
# STEP 4 — BEST MATCH
# ─────────────────────────────────────────────────────────────

def render_step4():
    ranked = st.session_state.shortlist

    # Pick the overall top vendor (rank 1 across all categories)
    top = None
    if ranked and ranked.get("ranked"):
        top = ranked["ranked"][0]

    st.markdown("""
    <div style="text-align:center;padding:0 24px 24px;">
        <div style="display:inline-block;background:rgba(234,179,8,0.1);
                    border:1px solid rgba(234,179,8,0.3);border-radius:20px;
                    padding:6px 16px;font-size:13px;font-weight:500;color:#D97706;
                    margin-bottom:20px;">
            Best Match Found
        </div>
        <h2 style="font-size:36px;font-weight:800;color:#0D1B3E;margin:0 0 10px;">
            Your ideal event package
        </h2>
        <p style="font-size:16px;color:#4B5563;margin:0 0 32px;">
            Based on your requirements and vendor responses,
            here's our top recommendation.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not top:
        st.warning("No shortlist available. Go back and run the pipeline.")
        return

    n             = top.get("normalised", {})
    vendor_name   = top.get("vendor_name", "—")
    match_score   = int(round(top.get("rank_score", 0) * 100))
    total_vat     = n.get("total_inc_vat")
    per_head      = n.get("total_per_head")
    headcount     = st.session_state.brief.get("headcount", "—")
    brief         = st.session_state.brief

    price_str     = f"£{total_vat:,.0f}" if total_vat else "—"
    per_head_str  = f"£{per_head:,.0f}" if per_head else "—"

    # Build inclusions list
    components    = top.get("components", {})
    included_list = [c.replace("_", " ").title() for c, s in components.items() if s == "included"]

    # Recommendation text
    recommendation = ranked.get("recommendation", "Top-ranked vendor based on your brief.")

    st.markdown(f"""
    <div style="max-width:720px;margin:0 auto;padding:0 24px;">
        <div style="background:white;border-radius:20px;padding:32px;
                    box-shadow:0 4px 32px rgba(13,27,62,0.10);">

            <!-- Top row -->
            <div style="display:flex;justify-content:space-between;
                        align-items:flex-start;flex-wrap:wrap;gap:16px;">
                <div>
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        <span style="font-size:24px;font-weight:800;color:#0D1B3E;">
                            {vendor_name}
                        </span>
                        <span class="pill-gradient">{match_score}% match</span>
                    </div>
                    <div style="font-size:14px;color:#6B7280;margin-top:6px;">
                        {brief.get('city','—')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:36px;font-weight:800;color:#0D1B3E;
                                line-height:1.1;">{price_str}</div>
                    <div style="font-size:13px;color:#9CA3AF;">total estimate</div>
                </div>
            </div>

            <!-- Stat boxes -->
            <div style="display:flex;gap:12px;margin-top:20px;flex-wrap:wrap;">
                <div style="background:#F5F7FF;border-radius:12px;padding:16px 20px;
                            flex:1;text-align:center;min-width:140px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                         style="color:#6366F1;">
                        <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"
                              fill="#6366F1"/>
                    </svg>
                    <div style="font-size:13px;color:#6B7280;margin-top:4px;">Capacity</div>
                    <div style="font-size:18px;font-weight:700;color:#0D1B3E;margin-top:2px;">
                        {headcount} guests
                    </div>
                </div>
                <div style="background:#F5F7FF;border-radius:12px;padding:16px 20px;
                            flex:1;text-align:center;min-width:140px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11zM7 11h5v5H7z"
                              fill="#6366F1"/>
                    </svg>
                    <div style="font-size:13px;color:#6B7280;margin-top:4px;">Duration</div>
                    <div style="font-size:18px;font-weight:700;color:#0D1B3E;margin-top:2px;">
                        {brief.get('date_start','—')}
                    </div>
                </div>
                <div style="background:#F5F7FF;border-radius:12px;padding:16px 20px;
                            flex:1;text-align:center;min-width:140px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"
                              fill="#6366F1"/>
                    </svg>
                    <div style="font-size:13px;color:#6B7280;margin-top:4px;">Per person</div>
                    <div style="font-size:18px;font-weight:700;color:#0D1B3E;margin-top:2px;">
                        {per_head_str}
                    </div>
                </div>
            </div>

            <!-- What's included -->
            <div style="margin-top:24px;">
                <div style="font-size:15px;font-weight:600;color:#0D1B3E;margin-bottom:12px;">
                    * What's included
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    {''.join(
                        f"""<div style="display:flex;align-items:center;gap:8px;">
                            <div style="width:18px;height:18px;border-radius:50%;
                                        background:linear-gradient(135deg,#6366F1,#1565C0);
                                        color:white;font-size:11px;display:inline-flex;
                                        align-items:center;justify-content:center;
                                        flex-shrink:0;">&#10003;</div>
                            <span style="font-size:14px;color:#374151;">{item}</span>
                        </div>"""
                        for item in included_list
                    ) if included_list else '<span style="color:#9CA3AF;font-size:14px;">Details pending vendor confirmation</span>'}
                </div>
            </div>

            <!-- Recommendation -->
            <div style="margin-top:20px;padding:14px 18px;background:#F5F7FF;
                        border-radius:10px;font-size:14px;color:#374151;">
                {recommendation}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    col_confirm, col_start = st.columns([3, 1])
    with col_confirm:
        st.button("Confirm & Book Event", key="confirm_book", use_container_width=True)
    with col_start:
        st.markdown('<div class="start-over-btn">', unsafe_allow_html=True)
        if st.button("Start Over", key="start_over", use_container_width=True):
            for k in ["step", "brief", "routing_result", "selected",
                      "shortlist", "brief_text"]:
                del st.session_state[k]
            init_state()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────

render_nav()
render_stepper(st.session_state.step)

step = st.session_state.step
if step == 1:
    render_step1()
elif step == 2:
    render_step2()
elif step == 3:
    render_step3()
elif step == 4:
    render_step4()
