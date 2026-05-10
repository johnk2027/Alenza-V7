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
# 1. BOOTSTRAP & LIFECYCLE
# ==========================================
st.set_page_config(
    page_title="Alenza Realtor OS | Ultimate Edition",
    page_icon="🏡",
    layout="wide"
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "alenza_broker_secure.db"

def init_broker_db():
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

# --- Authentication ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ Alenza Institutional Login")
    pwd = st.text_input("Enter Brokerage Access Key", type="password")
    if st.button("Log In"):
        if pwd == "alenza2026": 
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("Access Denied.")
    st.stop()

# ==========================================
# 2. PRIVACY & COMPLIANCE ENGINES
# ==========================================
def redact_preview(text: str) -> str:
    text = re.sub(r'\b[A-Za-z]\d[A-Za-z][ -]?\d[A-Za-z]\d\b', '[POSTAL]', text)
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\$?\b\d{3,}(,\d{3})*(\.\d{2})?\b', '[VAL]', text)
    return text[:100]

class ComplianceEngine:
    SEVERITY_RANK = {"CLEAR": 0, "STYLE_CAUTION": 1, "REVIEW_REQUIRED": 2, "PROHIBITED": 3}
    RULES = {
        "PROHIBITED": ["guaranteed profit", "no risk", "guaranteed return"],
        "REVIEW_REQUIRED": ["family friendly", "safe neighbourhood", "walking distance"],
        "STYLE_CAUTION": ["luxury", "best investment"]
    }
    @staticmethod
    def scan(text: str):
        found, max_sev = [], "CLEAR"
        for severity, terms in ComplianceEngine.RULES.items():
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', text.lower()):
                    found.append(f"[{severity}] Flag: '{term}'")
                    if ComplianceEngine.SEVERITY_RANK[severity] > ComplianceEngine.SEVERITY_RANK[max_severity if 'max_severity' in locals() else "CLEAR"]:
                        max_sev = severity
        return found, max_sev

def log_audit(agent, module, inp, out, risks, sev):
    i_hash = hashlib.sha256(inp.encode()).hexdigest()[:12]
    o_hash = hashlib.sha256(out.encode()).hexdigest()[:12]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('INSERT INTO secure_audit (timestamp, agent_name, module, input_hash, output_hash, redacted_preview, risks_found, severity_level) VALUES (?,?,?,?,?,?,?,?)',
                    (datetime.now().isoformat(), agent, module, i_hash, o_hash, redact_preview(inp), str(risks), sev))

# ==========================================
# 3. THE CALCULATOR ENGINES (MORTGAGE/INVEST/TAX)
# ==========================================
class FinancialLogic:
    @staticmethod
    def calc_cmhc(price, down):
        pct = down / price
        if pct >= 0.20 or price >= 1000000: return 0.0
        loan = price - down
        if pct >= 0.15: return loan * 0.028
        if pct >= 0.10: return loan * 0.031
        return loan * 0.04

    @staticmethod
    def calc_payment(principal, rate, amort):
        if principal <= 0 or rate <= 0: return 0
        m_rate = ((1 + (rate / 200)) ** (2 / 12)) - 1
        return (principal * m_rate) / (1 - (1 + m_rate) ** -(amort * 12))

    @staticmethod
    def calc_ontario_ltt(price):
        tax = 0.0
        if price > 55000: tax += (min(price, 250000) - 55000) * 0.01 + 55000 * 0.005
        else: tax += price * 0.005
        if price > 250000: tax += (min(price, 400000) - 250000) * 0.015
        if price > 400000: tax += (min(price, 2000000) - 400000) * 0.02
        if price > 2000000: tax += (price - 2000000) * 0.025
        return tax

    @staticmethod
    def calc_toronto_mltt(price):
        tax = FinancialLogic.calc_ontario_ltt(min(price, 3000000))
        if price > 3000000: # 2026 Luxury Tiers
            tax += (min(price, 4000000) - 3000000) * 0.044
            if price > 4000000: tax += (price - 4000000) * 0.0545 # Simplified upper
        return tax

# ==========================================
# 4. UI WORKSTATION
# ==========================================
st.sidebar.title("🏛️ Alenza OS")
agent = st.sidebar.text_input("Agent", "Agent_01")
module = st.sidebar.selectbox("Toolkit", [
    "📈 Market Intelligence",
    "🏠 Mortgage & Financing",
    "💰 Closing & LTT",
    "📊 Investment Suite",
    "🤝 Seller Net & ROI",
    "🤖 Compliance AI"
])

# --- MARKET INTEL ---
if module == "📈 Market Intelligence":
    st.title("Market Rate Signal")
    on, y2 = 2.25, 2.95 # Fallback benchmarks
    st.metric("BoC Overnight", f"{on}%")
    st.metric("2-Yr Yield", f"{y2}%")
    st.plotly_chart(go.Figure(data=go.Scatter(x=['O/N', '2Y'], y=[on, y2], line=dict(color='#CFB87C', width=4))))

# --- MORTGAGE SUITE ---
elif module == "🏠 Mortgage & Financing":
    st.title("Mortgage Suite")
    c1, c2 = st.columns(2)
    with c1:
        price = st.number_input("Purchase Price", 800000)
        down = st.number_input("Down Payment", 80000)
        rate = st.number_input("Rate (%)", 4.99)
        amort = st.selectbox("Amortization", [25, 30])
    with c2:
        cmhc = FinancialLogic.calc_cmhc(price, down)
        total_loan = (price - down) + cmhc
        pmt = FinancialLogic.calc_payment(total_loan, rate, amort)
        st.metric("Monthly Payment", f"${pmt:,.2f}")
        st.metric("CMHC Premium", f"${cmhc:,.2f}")
        st.write(f"Total Loan: ${total_loan:,.2f}")

# --- CLOSING & LTT ---
elif module == "💰 Closing & LTT":
    st.title("Closing Cost Breakdown")
    price = st.number_input("Price", 1200000)
    is_to = st.checkbox("Toronto Proper?")
    fthb = st.checkbox("First Time Buyer?")
    
    ltt_p = FinancialLogic.calc_ontario_ltt(price)
    ltt_m = FinancialLogic.calc_toronto_mltt(price) if is_to else 0
    reb_p = min(ltt_p, 4000) if fthb else 0
    reb_m = min(ltt_m, 4475) if fthb and is_to else 0
    
    st.metric("Net LTT Payable", f"${(ltt_p + ltt_m - reb_p - reb_m):,.2f}")
    st.table({"Provincial LTT": ltt_p, "Toronto MLTT": ltt_m, "Rebates": -(reb_p + reb_m)})

# --- INVESTMENT SUITE ---
elif module == "📊 Investment Suite":
    st.title("Investment Analyzer")
    price = st.number_input("Investment Price", 1000000)
    rent = st.number_input("Monthly Rent", 5000)
    opex = st.number_input("Monthly Expenses", 1200)
    
    noi = (rent - opex) * 12
    cap = (noi / price) * 100
    st.metric("Cap Rate", f"{cap:.2f}%")
    st.metric("Annual NOI", f"${noi:,.2f}")

# --- SELLER NET ---
elif module == "🤝 Seller Net & ROI":
    st.title("Seller Net & Agent ROI")
    sale = st.number_input("Sale Price", 1000000)
    mortgage = st.number_input("Mortgage Balance", 500000)
    comm = st.slider("Total Commission %", 1.0, 6.0, 5.0)
    
    gross_comm = sale * (comm/100)
    net = sale - mortgage - gross_comm - 2000 # Misc fees
    st.metric("Net to Seller", f"${net:,.2f}")
    st.metric("Agent Gross (2.5% side)", f"${sale * 0.025:,.2f}")

# --- COMPLIANCE AI ---
elif module == "🤖 Compliance AI":
    st.title("AI Content Scanner")
    inp = st.text_area("Draft Content")
    if st.button("Scan"):
        risks, sev = ComplianceEngine.scan(inp)
        log_audit(agent, "AI_COPILOT", inp, "Drafted content...", risks, sev)
        if sev != "CLEAR": st.warning(f"Status: {sev}")
        for r in risks: st.write(r)
        st.success("Log recorded in Broker Audit.")
