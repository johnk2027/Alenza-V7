import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# ALENZA CAPITAL | V7 9700 ENTERPRISE ENGINE
# ==========================================

st.set_page_config(page_title="Alenza Capital V7 Enterprise", layout="wide")

# Institutional Theme Injection
st.markdown("""
    <style>
    .main { background-color: #0B0F19; color: #F9FAFB; }
    div[data-testid="stMetric"] { background-color: #111827; padding: 20px; border-radius: 10px; border: 1px solid #374151; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #111827; 
        border: 1px solid #374151; 
        border-radius: 5px 5px 0px 0px; 
        padding: 8px 16px;
        color: #9CA3AF;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #3B82F6 !format; 
        color: white !important;
        border-color: #3B82F6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL SIDEBAR INPUT CONTROL ---
st.sidebar.title("🦅 V7 CONTROL CENTER")
with st.sidebar:
    st.subheader("Asset & Borrower")
    borrower = st.text_input("Borrower / Sponsor", "Enterprise Holdings LLC")
    prop_type = st.selectbox("Property Type", ["Multi-Family", "Industrial", "Retail", "Office", "Mixed-Use", "Hospitality"])
    
    st.subheader("Valuation")
    purchase_price = st.number_input("Purchase Price ($)", value=12500000)
    appraised_val = st.number_input("Appraised Value ($)", value=13750000)
    capex = st.number_input("Planned CapEx ($)", value=850000)
    
    st.subheader("Operations")
    gross_income = st.number_input("Gross Potential Income ($)", value=1554600)
    vacancy_pct = st.slider("Vacancy & Credit Loss (%)", 0.0, 15.0, 5.0) / 100
    opex = st.number_input("Operating Expenses ($)", value=350000)
    
    st.subheader("Financing Targets")
    rate = st.slider("Interest Rate (%)", 3.0, 10.0, 5.25, 0.25) / 100
    amort = st.number_input("Amortization (Years)", value=25)
    term = st.number_input("Term (Years)", value=5)
    
    st.divider()
    t_ltv = st.slider("Target Max LTV (%)", 50, 85, 75) / 100
    t_dscr = st.slider("Target Min DSCR (x)", 1.0, 1.6, 1.25, 0.05)
    t_dy = st.slider("Min Debt Yield (%)", 5.0, 15.0, 8.5) / 100

# --- V7 CORE LOGIC ENGINE ---
# NOI Calculation
eff_gross = gross_income * (1 - vacancy_pct)
noi = eff_gross - opex

# Sizing Calculations
loan_ltv = appraised_val * t_ltv
p_rate = rate / 12
n = amort * 12
m_ds_limit = (noi / t_dscr) / 12
loan_dscr = m_ds_limit * ((1 - (1 + p_rate)**-n) / p_rate)
loan_dy = noi / t_dy

# Final Supportable Loan
supportable_loan = min(loan_ltv, loan_dscr, loan_dy)
binding_constraint = "LTV" if supportable_loan == loan_ltv else "DSCR" if supportable_loan == loan_dscr else "Debt Yield"

# Metrics
pmt = (supportable_loan * p_rate) / (1 - (1 + p_rate)**-n)
act_dscr = noi / (pmt * 12)
act_ltv = supportable_loan / appraised_val
act_dy = noi / supportable_loan
total_uses = purchase_price + capex + (supportable_loan * 0.02) + 75000 # Incl. 2% fees + costs
equity_req = total_uses - supportable_loan

# --- MAIN INTERFACE ---
st.title("🦅 ALENZA CAPITAL | BROKER OS V7")
st.caption(f"File: {borrower} | {prop_type} | 9700 Enterprise Series")

tabs = st.tabs(["📊 Dashboard", "💰 Sources & Uses", "🧪 Scenario Manager", "⚖️ Risk & WALT", "💯 Deal Scorecard"])

# 1. DASHBOARD
with tabs[0]:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("SUPPORTABLE LOAN", f"${supportable_loan:,.0f}")
    k2.metric("ACTUAL LTV", f"{act_ltv*100:.1f}%")
    k3.metric("ACTUAL DSCR", f"{act_dscr:.2f}x")
    k4.metric("BINDING GATE", binding_constraint)
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Sizing Constraint Analysis")
        gates_df = pd.DataFrame({
            "Constraint": ["LTV Limit", "DSCR Limit", "Debt Yield Limit"],
            "Max Proceeds": [loan_ltv, loan_dscr, loan_dy]
        })
        st.bar_chart(gates_df, x="Constraint", y="Max Proceeds", color="#3B82F6")
    with c2:
        st.write("### Cash Flow Snapshot")
        st.write(f"**Stabilized NOI:** ${noi:,.0f}")
        st.write(f"**Annual Debt Service:** ${pmt*12:,.0f}")
        st.write(f"**Net Cash Flow:** ${noi - (pmt*12):,.0f}")
        st.progress(act_dscr/2.0 if act_dscr < 2 else 1.0, text=f"DSCR Health: {act_dscr:.2f}x")

# 2. SOURCES & USES
with tabs[1]:
    u1, u2 = st.columns(2)
    with u1:
        st.write("### Project Uses")
        uses_data = {
            "Item": ["Purchase Price", "CapEx", "Financing Fees", "Closing Costs"],
            "Amount": [purchase_price, capex, supportable_loan * 0.02, 75000]
        }
        st.table(pd.DataFrame(uses_data))
        st.subheader(f"Total Uses: ${total_uses:,.0f}")
    with u2:
        st.write("### Project Sources")
        sources_data = {
            "Source": ["Senior Loan", "Borrower Equity"],
            "Amount": [supportable_loan, equity_req]
        }
        st.table(pd.DataFrame(sources_data))
        st.subheader(f"Total Sources: ${supportable_loan + equity_req:,.0f}")

# 3. SCENARIO MANAGER
with tabs[2]:
    st.write("### Base vs. Downside vs. Upside")
    s_col1, s_col2, s_col3 = st.columns(3)
    
    # Simple Downside: -10% NOI, +1% Rate
    d_noi = noi * 0.9
    d_rate = rate + 0.01
    d_loan = ((d_noi/t_dscr)/12) * ((1 - (1 + (d_rate/12))**-n) / (d_rate/12))
    
    # Simple Upside: +5% NOI, -0.5% Rate
    u_noi = noi * 1.05
    u_rate = rate - 0.005
    u_loan = ((u_noi/t_dscr)/12) * ((1 - (1 + (u_rate/12))**-n) / (u_rate/12))
    
    s_col1.metric("Base Case", f"${supportable_loan:,.0f}")
    s_col2.metric("Downside Stress", f"${min(loan_ltv, d_loan):,.0f}", f"-${supportable_loan - min(loan_ltv, d_loan):,.0f}", delta_color="inverse")
    s_col3.metric("Upside Potential", f"${min(loan_ltv, u_loan):,.0f}", f"+${min(loan_ltv, u_loan) - supportable_loan:,.0f}")

# 4. RISK & WALT
with tabs[3]:
    st.write("### OSFI Risk & Lease Durability")
    r1, r2 = st.columns(2)
    with r1:
        st.write("**Regulatory Risk Signal (CAR 2026)**")
        if act_ltv <= 0.65: st.success("Risk Band: Low (Standardized)")
        elif act_ltv <= 0.75: st.warning("Risk Band: Medium")
        else: st.error("Risk Band: High / Elevated")
    with r2:
        walt = st.slider("WALT (Weighted Average Lease Term)", 0.0, 10.0, 4.5)
        if walt < 3: st.error(f"Critical Rollover Risk: {walt} years")
        else: st.success(f"Healthy Lease Profile: {walt} years")

# 5. DEAL SCORECARD
with tabs[4]:
    st.write("### 1,000-Point Algorithmic Triage")
    score = 0
    if act_ltv <= 0.60: score += 300
    elif act_ltv <= 0.75: score += 150
    if act_dscr >= 1.40: score += 400
    elif act_dscr >= 1.25: score += 200
    if act_dy >= 0.09: score += 300
    elif act_dy >= 0.08: score += 150
    
    st.subheader(f"Total Deal Score: {score} / 1,000")
    if score >= 800: st.success("GRADE: A | EXCELLENT")
    elif score >= 600: st.warning("GRADE: B | GOOD")
    else: st.error("GRADE: C/D | RESTRUCTURE REQUIRED")
