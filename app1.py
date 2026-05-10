"""
ALENZA REALTOR OS - INSTITUTIONAL APEX (v16.0)
Verified Date: May 9, 2026
Includes: 32/40 Rule Logic, Reserve Land Compliance, and OLS Regression.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from datetime import datetime

# ==========================================
# 1. CORE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Alenza v16 | Institutional Knowledge", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .reportview-container { background: #0E1117; }
    .stMetric { background-color: #161B22; border: 1px solid #30363D; padding: 15px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. THE RIGOROUS FINANCE ENGINE
# ==========================================
class AlenzaFinance:
    @staticmethod
    def calc_canadian_payment(principal, annual_rate, years):
        """Calculates monthly payment using Canadian Semi-Annual Compounding."""
        # Canadian mortgages are compounded semi-annually by law
        if principal <= 0 or annual_rate <= 0: return 0
        i_monthly = ((1 + (annual_rate / 200)) ** (2 / 12)) - 1 #
        n_months = years * 12
        pmt = (principal * i_monthly) / (1 - (1 + i_monthly) ** -n_months)
        return pmt

    @staticmethod
    def get_qualifying_rate(contract_rate):
        """OSFI Stress Test: Higher of Rate + 2% or 5.25% floor."""
        return max(contract_rate + 2.0, 5.25)

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("🏛️ Alenza OS")
    module = st.selectbox("Intelligence Module", [
        "🏡 Buyer Qualification (32/40)",
        "📈 Predictive Risk Modeling",
        "📜 Knowledge Base & History",
        "🪶 Reserve Land Documentation"
    ])
    st.info("Institutional Version 16.0.26")

# ==========================================
# 4. MODULE: BUYER QUALIFICATION (THE 32/40 RULE)
# ==========================================
if module == "🏡 Buyer Qualification (32/40)":
    st.title("GDS / TDS Institutional Qualification")
    st.caption("Applying the 32% GDS and 40% TDS Standard.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Income & Debt")
        gross_inc = st.number_input("Gross Monthly Household Income ($)", value=5000) # [cite: 91]
        car_pmt = st.number_input("Monthly Car Loan/Lease ($)", value=500) # [cite: 88, 102]
        cc_pmt = st.number_input("Monthly Credit Card Min. ($)", value=200) # [cite: 89, 102]
        util = st.number_input("Monthly Cable/Phone/Internet ($)", value=150) # [cite: 87]
        
    with col2:
        st.subheader("Housing Details")
        price = st.number_input("Purchase Price ($)", value=350000)
        down = st.number_input("Down Payment ($)", value= price * 0.05)
        rate = st.number_input("Interest Rate (%)", value=4.5)
        prop_tax = st.number_input("Monthly Property Tax ($)", value=200) # [cite: 78, 93]
        heat = st.number_input("Monthly Heating ($)", value=150) # [cite: 79, 93]

    # CALCULATION
    loan_amt = price - down
    # High-Ratio Check: If down < 20%, insurance is required [cite: 29]
    if (down/price) < 0.20:
        st.caption("⚠️ High-Ratio Mortgage: Default Insurance (CMHC) required.")

    q_rate = AlenzaFinance.get_qualifying_rate(rate)
    pmt = AlenzaFinance.calc_canadian_payment(loan_amt, q_rate, 25)
    
    gds_total = pmt + prop_tax + heat # [cite: 75, 76, 78, 79]
    tds_total = gds_total + car_pmt + cc_pmt + util # [cite: 85, 86, 88, 89, 90]
    
    gds_ratio = (gds_total / gross_inc) * 100
    tds_ratio = (tds_total / gross_inc) * 100
    
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    # GDS Metrics based on Source 71 (32% limit)
    m1.metric("GDS Ratio", f"{gds_ratio:.1f}%", 
              delta="Qualified" if gds_ratio <= 32 else "Exceeds 32% Limit", 
              delta_color="normal" if gds_ratio <= 32 else "inverse")
    
    # TDS Metrics based on Source 82 (40% limit)
    m2.metric("TDS Ratio", f"{tds_ratio:.1f}%", 
              delta="Qualified" if tds_ratio <= 40 else "Exceeds 40% Limit", 
              delta_color="normal" if tds_ratio <= 40 else "inverse")
    
    m3.metric("Qualifying P&I", f"${pmt:,.2f}")

    

# ==========================================
# 5. MODULE: PREDICTIVE RISK MODELING (REGRESSIONS)
# ==========================================
elif module == "📈 Predictive Risk Modeling":
    st.title("Linear Regression Risk Analysis")
    st.caption("Using Ordinary Least Squares (OLS) to model Rate vs. Credit.")
    
    # 
    
    # Regression Model: Y = B0 + B1*X + E
    # Independent Variable: Credit Score (600-850)
    # Dependent Variable: Offered Interest Rate
    
    credit_scores = np.array([600, 650, 700, 750, 800, 850])
    # Higher credit score reduces interest rate
    offered_rates = np.array([6.5, 5.8, 5.2, 4.8, 4.4, 4.2])
    
    z = np.polyfit(credit_scores, offered_rates, 1) # Linear fit
    p = np.poly1d(z)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=credit_scores, y=offered_rates, mode='markers', name='Actual Lenders'))
    fig.add_trace(go.Scatter(x=credit_scores, y=p(credit_scores), name='OLS Regression Line', line=dict(color='#CFB87C')))
    
    fig.update_layout(title="Impact of Credit Score on Interest Rate Modeling", 
                      xaxis_title="Credit Score Index", yaxis_title="Interest Rate (%)",
                      template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 6. MODULE: RESERVE LAND DOCUMENTATION
# ==========================================
elif module == "🪶 Reserve Land Documentation":
    st.title("First Nation Mortgage Accessibility")
    st.caption("Specialized documentation for homes on reserve lands[cite: 132].")
    
    with st.expander("Required Documentation Checklist [cite: 134, 135, 137]"):
        st.checkbox("Proof of land allotment (Certificate of Possession)")
        st.checkbox("Ministerial loan guarantee from ISC")
        st.checkbox("Band Council Resolution (BCR) for housing program approvals")
        st.checkbox("Mortgage loan guarantee documentation approved by Band Council")

# ==========================================
# 7. MODULE: KNOWLEDGE BASE & HISTORY
# ==========================================
elif module == "📜 Knowledge Base & History":
    st.title("Historical Evolution of Mortgages")
    st.markdown("""
    * **Pre-1900s:** Borrowers typically made interest-only payments and repaid principal in one lump sum at the end.
    * **1946:** Creation of the **CMHC** to protect lenders from default.
    * **Pre-1980s:** Fixed rates were often guaranteed for the entire length of the mortgage.
    * **Modern Era:** Introduction of **'Mortgage Terms'** (6 months to 10 years) to protect banks from interest rate inflation.
    """)
