import streamlit as st
import pandas as pd
from database.db_helper import save_transactions_to_db, fetch_transactions

SEGMENTS = ["Agri Inputs", "Business Shop", "Household", "Loans & Debt"]

def init_state():
    if "master_ledger" not in st.session_state or st.session_state["master_ledger"].empty:
        # Load existing stored records from SQLite database on app start
        df_db = fetch_transactions()
        if not df_db.empty:
            st.session_state["master_ledger"] = df_db
        else:
            st.session_state["master_ledger"] = pd.DataFrame(columns=[
                "Date", "Segment", "Merchant_Source", "Amount", "Channel"
            ])
            
    if "app_segments" not in st.session_state:
        st.session_state["app_segments"] = list(SEGMENTS)

def add_transactions(new_recs):
    init_state()
    df_new = pd.DataFrame(new_recs)
    
    # 1. Update in-memory session state
    st.session_state["master_ledger"] = pd.concat(
        [st.session_state["master_ledger"], df_new], ignore_index=True
    )
    
    # 2. Persist directly to SQLite database file
    save_transactions_to_db(df_new)

def load_css():
    st.markdown("""
        <style>
            .stApp { background-color: #f9fbf9; }
        </style>
    """, unsafe_allow_html=True)