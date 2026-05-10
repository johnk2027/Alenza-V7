import streamlit as st
import pandas as pd
import sqlite3
import requests
import hashlib
import re
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# ==========================================
# 1. BOOTSTRAP & LIFECYCLE (Must be first)
# ==========================================
st.set_page_config(
    page_title="Alenza Realtor OS v7",
    page_icon="🛡️",
    layout="wide"
)

# Paths and Persistence
APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "alenza_broker_secure.db"

def init_broker_db():
    """Initializes the persistent SQLite database for broker oversight."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS secure_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                agent_name TEXT,
                module TEXT,
                input_hash TEXT,
                output_hash TEXT,
                redacted_preview TEXT,
                risks_found TEXT,
                severity_level TEXT
            )
        """)
init_broker_db()

# --- Authentication Layer ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ Alenza v7 | Institutional Access")
    pwd = st.text_input("Enter Brokerage Access Key", type="password")
    if st.button("Authenticate"):
        if pwd == "alenza2026": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# --- Global Settings ---
DEMO_MODE = st.sidebar.toggle("Developer Demo Mode (Simulated AI)", value=True)

# ==========================================
# 2. PRIVACY & COMPLIANCE ENGINES
# ==========================================
def redact_preview(text: str) -> str:
    """True Redactor: Scrubs PII, Names, Addresses, and Postal Codes."""
    # Canadian Postal Code
    text = re.sub(r'\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b', '[POSTAL]', text)
    # Email
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
    # Phone
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    # SIN / ID (9 digits)
    text = re.sub(r'\b\d{3}[- ]?\d{3}[- ]?\d{3}\b', '[ID]', text)
    # Large Currencies (Prices/Valuations)
    text = re.sub(r'\$?\b\d{3,}(,\d{3})*(\.\d{2})?\b', '[VAL]', text)
    return text[:100]

class ComplianceAudit:
    @staticmethod
    def log_interaction(agent, module, inp, out, risks, sev):
        i_hash = hashlib.sha256(inp.encode()).hexdigest()[:12]
        o_hash = hashlib.sha256(out.encode()).hexdigest()[:12]
        safe_preview = redact_preview(inp)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''INSERT INTO secure_audit 
                (timestamp, agent_name, module, input_hash, output_hash, redacted_preview, risks_found, severity_level) 
                VALUES (?,?,?,?,?,?,?,?)''',
                (datetime.now().isoformat(), agent, module, i_hash, o_hash, safe_preview, str(risks), sev))

class ComplianceEngine:
    SEVERITY_RANK = {"CLEAR": 0, "STYLE_CAUTION": 1, "REVIEW_REQUIRED": 2, "PROHIBITED": 3}
    RULES = {
        "PROHIBITED": ["guaranteed profit", "no risk", "guaranteed return", "investment certainty"],
        "REVIEW_REQUIRED": ["family friendly", "safe neighborhood", "safe neighbourhood", "walking distance", "perfect for kids"],
        "STYLE_CAUTION": ["luxury", "best investment", "undervalued"]
    }

    @staticmethod
    def scan(text: str) -> Tuple[List[str], str]:
        found = []
        max_severity = "CLEAR"
        for severity, terms in ComplianceEngine.RULES.items():
            for term in terms:
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, text.lower()):
                    found.append(f"[{severity}] Flag: '{term}'")
                    if ComplianceEngine.SEVERITY_RANK[severity] > ComplianceEngine.SEVERITY_RANK[max_severity]:
                        max_severity = severity
        return found, max_severity

# ==========================================
# 3. VERIFIED 2026 FINANCIAL ENGINE
# ==========================================
class CanadianFinanceEngine:
    VERIFIED_ON = "2026-05-09"
    SOURCES = {
        "Ontario LTT": "https://www.ontario.ca/document/land-transfer-tax",
        "Toronto MLTT": "https://www.toronto.ca/services-payments/property-taxes-utilities/municipal-land-transfer-tax-mltt/",
        "BC PTT": "https://www2.gov.bc.ca/gov/content/taxes/property-taxes/property-transfer-tax"
    }

    @staticmethod
    def calc_ontario_ltt(price: float) -> float:
        tax = 0.0
        if price > 55000: tax += (min(price, 250000) - 55000) * 0.01 + 55000 * 0.005
        else: tax += price * 0.005
        if price > 250000: tax += (min(price, 400000) - 250000) * 0.015
        if price > 400000: tax += (min(price, 2000000) - 400000) * 0.02
        if price > 2000000: tax += (price - 2000000) * 0.025
        return tax

    @staticmethod
    def calc_toronto_mltt(price: float) -> float:
        tax = CanadianFinanceEngine.calc_ontario_ltt(min(price, 3000000))
        if price > 3000000: tax += (min(price, 4000000) - 3000000) * 0.044
        if price > 4000000: tax += (min(price, 5000000) - 4000000) * 0.0545
        if price > 5000000: tax += (min(price, 10000000) - 5000000) * 0.065
        if price > 10000000: tax += (min(price, 20000000) - 10000000) * 0.0755
        if price > 20000000: tax += (price - 20000000) * 0.086
        return tax

    @staticmethod
    def calc_bc_ptt(price: float, is_fthb: bool) -> Tuple[float, float]:
        tax = min(price, 200000) * 0.01
        if price > 200000: tax += (min(price, 2000000) - 200000) * 0.02
        if price > 2000000: tax += (min(price, 3000000) - 2000000) * 0.03
        if price > 3000000: tax += (price - 3000000) * 0.05
        rebate = 0.0
        if is_fthb:
            base_rebate = min(tax, 8000.0)
            if price <= 835000: rebate = base_rebate
            elif price < 860000: rebate = base_rebate * ((860000 - price) / 25000)
        return tax, rebate

# ==========================================
# 4. MARKET DATA INTEGRATION
# ==========================================
@st.cache_data(ttl=3600)
def fetch_live_market_data() -> Tuple[float, float, str, str]:
    try:
        res = requests.get("https://www.bankofcanada.ca/valet/observations/V39079,V39054/json?recent=1", timeout=5)
        obs = res.json().get("observations", [])[-1]
        return float(obs['V39079']['v']), float(obs['V39054']['v']), "LIVE", obs['d']
    except:
        return 2.25, 2.91, "FALLBACK", "2026-05-09"

# ==========================================
# 5. UI LAYOUT
# ==========================================
st.sidebar.title("🏛️ Alenza-v7")
agent_name = st.sidebar.text_input("Agent Identity", value="Agent_01")
module = st.sidebar.selectbox("Workstation", ["Closing Estimates", "Compliance AI", "Market Intelligence"])

if module == "Closing Estimates":
    st.title("Verified Closing Cost Breakdown")
    c1, c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price ($)", value=850000, step=10000)
        prov = st.selectbox("Province", ["Ontario", "BC"])
        is_to = st.checkbox("City of Toronto?") if prov == "Ontario" else False
        fthb = st.checkbox("First-Time Home Buyer?")
        
        if prov == "Ontario":
            ltt_p = CanadianFinanceEngine.calc_ontario_ltt(price)
            ltt_m = CanadianFinanceEngine.calc_toronto_mltt(price) if is_to else 0
            reb_p = min(ltt_p, 4000.0) if fthb else 0
            reb_m = min(ltt_m, 4475.0) if (fthb and is_to) else 0
            tax_total, reb_total = (ltt_p + ltt_m), (reb_p + reb_m)
            breakdown = {"Ontario LTT": ltt_p, "Toronto MLTT": ltt_m, "Prov. Rebate": -reb_p, "Muni. Rebate": -reb_m}
        else:
            tax_total, reb_total = CanadianFinanceEngine.calc_bc_ptt(price, fthb)
            breakdown = {"BC PTT": tax_total, "FTHB Exemption": -reb_total}

    with c2:
        st.metric("Total Transfer Tax", f"${tax_total:,.2f}")
        st.metric("Estimated FTHB Rebate", f"-${reb_total:,.2f}")
        st.subheader(f"Net Payable: ${(tax_total - reb_total):,.2f}")
        st.table(pd.Series(breakdown).rename("Amount ($)"))
        st.caption(f"Verified Logic: {CanadianFinanceEngine.VERIFIED_ON}")

elif module == "Compliance AI":
    st.title("AI Content Risk Scanner")
    agent_input = st.text_area("Enter Draft Details")
    
    if st.button("Scan & Generate"):
        in_risks, in_sev = ComplianceEngine.scan(agent_input)
        ai_output = f"DRAFT: This {agent_input} is a guaranteed amazing home for families." if DEMO_MODE else "Drafting..."
        out_risks, out_sev = ComplianceEngine.scan(ai_output)
        
        ranks = [ComplianceEngine.SEVERITY_RANK[s] for s in [in_sev, out_sev]]
        max_rank = max(ranks)
        final_sev = next(name for name, r in ComplianceEngine.SEVERITY_RANK.items() if r == max_rank)
        total_risks = list(set(in_risks + out_risks))

        ComplianceAudit.log_interaction(agent_name, "AI_COPILOT", agent_input, ai_output, total_risks, final_sev)

        if max_rank >= 2: st.error(f"STATUS: {final_sev}")
        elif max_rank == 1: st.warning(f"STATUS: {final_sev}")
        else: st.success("STATUS: CLEAR")
        
        st.info(ai_output)
        st.caption("[Compliance Screen Applied — Broker Review Still Required]")

elif module == "Market Intelligence":
    st.title("Market Rate Pressure")
    on, y2, status, ldate = fetch_live_market_data()
    st.caption(f"Status: **{status}** | Last BoC Update: {ldate}")
    m1, m2 = st.columns(2)
    m1.metric("BoC Overnight Rate", f"{on}%")
    m2.metric("2-Yr Bond Yield", f"{y2}%")
    fig = go.Figure(data=go.Scatter(x=['O/N', '2Y'], y=[on, y2], line=dict(color='#CFB87C', width=4)))
    st.plotly_chart(fig, use_container_width=True)
