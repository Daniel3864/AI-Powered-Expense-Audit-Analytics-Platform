import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from utils.state_manager import init_state, load_css

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
load_css()
init_state()

# --- Custom Page Styling Theme ---
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #334155;
        margin-top: 25px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌾 Financial Audit Dashboard</div>', unsafe_allow_html=True)

# Load Ledger from CSV / Session State
LEDGER_FILE = ROOT_DIR / "master_ledger.csv"
ledger = st.session_state.get("master_ledger", pd.DataFrame())
if ledger.empty and LEDGER_FILE.exists():
    ledger = pd.read_csv(LEDGER_FILE)

if not ledger.empty:
    total_spent = ledger["Amount"].sum()
    total_transactions = len(ledger)
    
    # --- Global Summary Metrics ---
    col_g1, col_g2 = st.columns(2)
    col_g1.metric("Total Consolidated Spend", f"₹ {total_spent:,.2f}")
    col_g2.metric("Total Recorded Transactions", f"{total_transactions}")
    
    st.markdown("---")
    st.markdown('<div class="section-header">📁 Segment Budget & Share Breakdown</div>', unsafe_allow_html=True)
    
    # --- Dynamic Gradient KPI Cards for Each Segment ---
    if "Segment" in ledger.columns:
        segment_totals = ledger.groupby("Segment")["Amount"].sum().reset_index()
        total_global_spend = segment_totals["Amount"].sum()
        
        # Gorgeous cohesive color gradients
        gradients = [
            "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",  # Blue
            "linear-gradient(135deg, #f97316 0%, #c2410c 100%)",  # Orange
            "linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)",  # Teal
            "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)",  # Purple
            "linear-gradient(135deg, #ec4899 0%, #be185d 100%)",  # Pink
        ]
        
        cols = st.columns(max(len(segment_totals), 1))
        
        for idx, row in segment_totals.iterrows():
            seg_name = row["Segment"]
            seg_spend = row["Amount"]
            seg_percentage = (seg_spend / total_global_spend * 100) if total_global_spend > 0 else 0.0
            bg_gradient = gradients[idx % len(gradients)]
            
            card_html = f"""
            <div style="
                background: {bg_gradient};
                border-radius: 12px;
                padding: 20px;
                color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 10px;
                font-family: sans-serif;
            ">
                <div style="font-size: 14px; font-weight: 500; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px;">
                    {seg_name}
                </div>
                <div style="font-size: 24px; font-weight: 700; margin-top: 8px;">
                    ₹ {seg_spend:,.2f}
                </div>
                <div style="font-size: 13px; margin-top: 6px; opacity: 0.95; background: rgba(255, 255, 255, 0.2); display: inline-block; padding: 2px 8px; border-radius: 6px;">
                    📊 {seg_percentage:.1f}% of total budget
                </div>
            </div>
            """
            
            with cols[idx % len(cols)]:
                st.markdown(card_html, unsafe_allow_html=True)
                
    st.markdown("---")
    st.markdown('<div class="section-header">📈 Spend by Segment Chart</div>', unsafe_allow_html=True)
    
    segment_summary = ledger.groupby("Segment")["Amount"].sum().reset_index()
    st.bar_chart(segment_summary.set_index("Segment"))
    
    st.markdown("---")
    st.markdown('<div class="section-header">📑 Master Transaction Ledger</div>', unsafe_allow_html=True)
    st.dataframe(ledger, use_container_width=True, hide_index=True)
else:
    st.info("No transaction data available yet. Go to **Data Ingestion** to add statements, manual entries, or batch SMS records.")