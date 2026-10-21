import streamlit as st
import pandas as pd
from pathlib import Path
from utils.state_manager import init_state, load_css

st.set_page_config(
    page_title="AI-Powered Expense Audit & Compliance Platform",
    page_icon="💳",
    layout="wide"
)
load_css()
init_state()

# --- Hero Header ---
st.title("💳 AI-Powered Expense Audit & Compliance Platform")
st.markdown("### Intelligent Multi-Channel Financial Tracking, Vector Search, and Automated Auditing")

st.markdown("---")

# --- Quick System Overview Metrics ---
col1, col2, col3 = st.columns(3)

# Load Ledger data to show live stats on the home page
LEDGER_FILE = Path(__file__).resolve().parent / "master_ledger.csv"
df = st.session_state.get("master_ledger", pd.DataFrame())
if df.empty and LEDGER_FILE.exists():
    df = pd.read_csv(LEDGER_FILE)

total_records = len(df)
total_spend = df["Amount"].sum() if not df.empty else 0.0
unique_segments = df["Segment"].nunique() if "Segment" in df.columns and not df.empty else 0

col1.metric("Total Master Records", f"{total_records}")
col2.metric("Consolidated Spend Tracked", f"₹ {total_spend:,.2f}")
col3.metric("Active Business Segments", f"{unique_segments}")

st.markdown("---")

# --- Navigation & Feature Overview Cards ---
st.subheader("🧭 Platform Navigation & Capabilities")

c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    #### 📊 1. Overview Dashboard
    * View executive summaries and global spend metrics.
    * Track segment-wise budget distribution percentages with interactive gradient KPI cards.
    """)
    
    st.markdown("""
    #### 📥 2. Data Ingestion
    * Seamlessly upload bank statement PDFs or batch SMS transaction logs.
    * Parse dates, amounts, and merchants using automated RegEx extraction and auto-categorization.
    """)

with c2:
    st.markdown("""
    #### 📈 3. Segment Analytics
    * Multidimensional spend analysis with custom timeline filtering (**Daily / Monthly**).
    * Interactive multi-segment trend lines and vendor breakdown tables.
    """)
    
    st.markdown("""
    #### 🤖 4. AI RAG Assistant
    * Query historical transaction precedents and compliance rules using natural language.
    * Powered by OpenAI embeddings (`text-embedding-3-small`) and Pinecone vector search (`expense-audit-index`)[cite: 3].
    """)

st.markdown("---")
st.info("💡 **Tip:** Use the sidebar navigation menu on the left to switch between pages (`Overview`, `Data Ingestion`, `Segment Analytics`, and `Assistant`) and begin exploring your audit platform!")