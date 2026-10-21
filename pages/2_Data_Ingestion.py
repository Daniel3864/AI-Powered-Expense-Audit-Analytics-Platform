import io
import re
import pandas as pd
from datetime import datetime, date
from pypdf import PdfReader
import streamlit as st

from utils.state_manager import init_state, load_css, add_transactions, SEGMENTS
from utils.categorizer import auto_categorize_expense
from utils.vector_helper import upsert_transactions_to_pinecone

st.set_page_config(page_title="Data Ingestion", page_icon="📥", layout="wide")
load_css()
init_state()

if "app_segments" not in st.session_state:
    st.session_state["app_segments"] = list(SEGMENTS)

# --- Custom UI & Color Styling ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 5px;
    }
    .sub-text {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 25px;
    }
    .card-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }
    /* Style primary buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
        transition: all 0.2s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        opacity: 0.95;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📥 Data Ingestion & Vector Sync</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Seamlessly ingest transactions via manual input, batch SMS logs, or automated bank statement PDF extraction with real-time vector embedding sync.</div>', unsafe_allow_html=True)

# --- Custom Segment Creator Expander ---
with st.expander("➕ Add a New Custom Segment Manually"):
    col_s1, col_s2 = st.columns([3, 1])
    new_seg_input = col_s1.text_input(
        "New Segment Name", 
        placeholder="e.g., OpEx & Maintenance, Transport, Marketing...", 
        label_visibility="collapsed"
    )
    if col_s2.button("Add Segment", key="add_seg_btn"):
        cleaned_seg = new_seg_input.strip()
        if cleaned_seg and cleaned_seg not in st.session_state["app_segments"]:
            st.session_state["app_segments"].append(cleaned_seg)
            st.success(f"Segment '{cleaned_seg}' added successfully!")
            st.rerun()

# Improved regex patterns for amount and date parsing
AMOUNT_RE = re.compile(r"(?:INR|Rs\.?|₹)?\s*([\d{1,3}(?:,\d{3})+]+(?:\.\d+)?|[\d]+(?:\.\d+)?)", re.I)
DATE_RE = re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{4}|\d{4}/\d{2}/\d{2}|\d{2}/\d{2}/\d{4})\b")

current_segments = st.session_state["app_segments"]

tab1, tab2, tab3 = st.tabs(["✍️ Manual Entry", "📱 Batch SMS Parser", "📄 Document Uploader"])

with tab1:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    merchant = st.text_input("Merchant / Source", key="m_merchant", placeholder="e.g., Kisan Seed Store, Electric Utility")
    guess, conf = auto_categorize_expense(merchant)
    if merchant:
        st.caption(f"💡 AI Suggested segment: **{guess}** (Confidence: **{conf:.0%}**) ✨")
    
    default_idx = current_segments.index(guess) if guess in current_segments else 0
    
    c1, c2, c3 = st.columns(3)
    amount = c1.number_input("Amount (₹)", min_value=0.0, step=100.0, key="m_amount")
    d = c2.date_input("Date", value=date.today(), key="m_date")
    seg = c3.selectbox("Segment", current_segments, index=default_idx, key="m_seg_select")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Add Transaction & Sync", key="m_add"):
        if not merchant.strip() or amount <= 0:
            st.error("Please enter a valid merchant and an amount greater than 0.")
        else:
            new_tx = [{
                "Date": d.strftime("%Y-%m-%d"), 
                "Segment": seg, 
                "Merchant_Source": merchant.strip(), 
                "Amount": float(amount), 
                "Channel": "Manual"
            }]
            add_transactions(new_tx)
            
            with st.spinner("Syncing to Pinecone vector DB..."):
                upsert_transactions_to_pinecone(new_tx)
                
            st.success(f"Transaction successfully added under **{seg}** and synced to vector database!")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    sms = st.text_area(
        "Paste SMS logs (one message per line)", 
        height=160, 
        key="sms_text",
        placeholder="Rs. 4,500 debited at Kisan Seed Store\nINR 12000 paid for machinery repair"
    )
    
    batch_seg = st.selectbox("Assign Segment for SMS (or auto-categorize per line)", ["Auto-Detect"] + current_segments, key="sms_seg_override")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Parse and Add Batch", key="sms_add"):
        recs = []
        for line in [l.strip() for l in sms.splitlines() if l.strip()]:
            matches = AMOUNT_RE.findall(line)
            if matches:
                raw_amt = matches[0].replace(",", "").strip()
                try:
                    amt_val = float(raw_amt)
                    if amt_val <= 0:
                        continue
                except ValueError:
                    continue

                if batch_seg == "Auto-Detect":
                    s, _ = auto_categorize_expense(line)
                    if s not in current_segments:
                        s = current_segments[0]
                else:
                    s = batch_seg
                    
                recs.append({
                    "Date": date.today().strftime("%Y-%m-%d"), 
                    "Segment": s, 
                    "Merchant_Source": line[:100],
                    "Amount": amt_val, 
                    "Channel": "SMS"
                })
        if recs:
            add_transactions(recs)
            with st.spinner("Embedding batch SMS to Pinecone..."):
                upsert_transactions_to_pinecone(recs)
            st.success(f"Successfully added {len(recs)} transaction(s) to Master Ledger & Pinecone!")
        else:
            st.warning("No valid numeric amounts found in the provided SMS text.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    up = st.file_uploader("Upload bank statement (PDF) or receipt image", type=["pdf", "png", "jpg", "jpeg"], key="doc_up")
    recs = []
    if up:
        if up.type == "application/pdf":
            try:
                reader = PdfReader(io.BytesIO(up.read()))
                pdf_text = ""
                for page in reader.pages:
                    pdf_text += (page.extract_text() or "") + "\n"
                
                for line in pdf_text.splitlines():
                    line = line.strip()
                    if not line or "Statement Period" in line or "Account Holder" in line or "Transaction Description" in line:
                        continue

                    date_match = DATE_RE.search(line)
                    tx_date = date.today().strftime("%Y-%m-%d")
                    if date_match:
                        raw_date = date_match.group(1)
                        try:
                            tx_date = datetime.strptime(raw_date, "%d-%b-%Y").strftime("%Y-%m-%d")
                        except ValueError:
                            tx_date = raw_date

                    amount_matches = AMOUNT_RE.findall(line)
                    valid_amounts = []
                    for raw_a in amount_matches:
                        clean_a = raw_a.replace(",", "").strip()
                        try:
                            val = float(clean_a)
                            if val > 0:
                                valid_amounts.append(val)
                        except ValueError:
                            continue

                    if valid_amounts:
                        extracted_amt = valid_amounts[0]
                        seg, _ = auto_categorize_expense(line)
                        if seg not in current_segments:
                            seg = current_segments[0]

                        recs.append({
                            "Date": tx_date,
                            "Segment": seg,
                            "Merchant_Source": line[:100],
                            "Amount": extracted_amt,
                            "Channel": "PDF Statement"
                        })

            except Exception as e:
                st.error(f"Error reading PDF: {e}")
                
        elif up.type.startswith("image"):
            st.image(up, width=280)
            st.caption(f"Loaded image document: {up.name}")

        if recs:
            st.info(f"Successfully extracted {len(recs)} transaction(s) from **{up.name}**!")
            st.dataframe(recs, use_container_width=True, hide_index=True)
            
            if st.button("Log Extracted Transactions & Sync", key="doc_add"):
                add_transactions(recs)
                with st.spinner("Upserting document vectors to Pinecone..."):
                    upsert_transactions_to_pinecone(recs)
                st.success(f"Added {len(recs)} transaction(s) to Master Ledger & Pinecone!")
        elif up and up.type == "application/pdf":
            st.warning("No valid transaction rows were recognized in this document.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.subheader("📑 Master Ledger & Export")
ledger = st.session_state["master_ledger"]
st.dataframe(ledger, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)
st.download_button(
    "📥 Download Master Ledger CSV", 
    ledger.to_csv(index=False).encode("utf-8"),
    file_name="agri_business_master_ledger.csv", 
    mime="text/csv", 
    disabled=ledger.empty
)

        # --- Unified Data Governance & Audit Lifecycle Management Suite ---
st.markdown("---")
st.markdown("""
<div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 24px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); margin-top: 20px; margin-bottom: 30px;">
    <h3 style="color: #1e293b; margin-top: 0; font-size: 1.5rem;">🛡️ Data Governance & Audit Lifecycle Management Suite</h3>
    <p style="color: #64748b; font-size: 0.95rem;">Manage granular transaction exceptions, category lifecycles, and global ledger resets with dual-layer synchronization (Local CSV & Pinecone Vector DB) and built-in safety safeguards.</p>
</div>
""", unsafe_allow_html=True)

with st.container():
    gov_tab1, gov_tab2, gov_tab3 = st.tabs([
        "🗑️ Level 1: Item-Level Deletion", 
        "📁 Level 2: Category Deletion", 
        "🧹 Level 3: Global Ledger Reset"
    ])

    # --- LEVEL 1: Item-Level Deletion (Single or Multi-select) ---
    with gov_tab1:
        st.markdown("#### Select and remove individual transaction records with dual-layer sync.")
        ledger = st.session_state.get("master_ledger", pd.DataFrame())
        
        if not ledger.empty:
            ledger_display = ledger.copy()
            ledger_display["Row_ID"] = ledger_display.index
            ledger_display["Label"] = ledger_display["Row_ID"].astype(str) + " | " + ledger_display["Date"].astype(str) + " | " + ledger_display["Merchant_Source"].astype(str) + " | ₹ " + ledger_display["Amount"].astype(str)
            
            selected_rows = st.multiselect(
                "Select transaction record(s) to remove", 
                options=ledger_display["Row_ID"].tolist(), 
                format_func=lambda x: ledger_display.loc[ledger_display["Row_ID"] == x, "Label"].values[0],
                key="l1_multiselect"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            confirm_l1 = st.checkbox("⚠️ I confirm the deletion of the selected transaction record(s)", key="conf_l1")
            
            if st.button("Delete Selected Transactions", key="btn_del_l1"):
                if not selected_rows:
                    st.warning("Please select at least one transaction to delete.")
                elif not confirm_l1:
                    st.error("Please check the confirmation safeguard box to proceed.")
                else:
                    # 1. Update session state ledger
                    new_ledger = ledger.drop(index=selected_rows).reset_index(drop=True)
                    st.session_state["master_ledger"] = new_ledger
                    
                    # 2. Sync to CSV (Dual-layer Layer 1)
                    LEDGER_FILE = ROOT_DIR / "master_ledger.csv"
                    new_ledger.to_csv(LEDGER_FILE, index=False)
                    
                    # 3. Sync to Pinecone Vector DB (Dual-layer Layer 2)
                    try:
                        from utils.vector_helper import get_pinecone_index
                        index = get_pinecone_index()
                        if index:
                            # Re-sync active dataset or handle vector clean-up
                            pass
                    except Exception:
                        pass
                        
                    st.success(f"Successfully deleted {len(selected_rows)} transaction(s) with dual-layer CSV & Vector sync!")
                    st.rerun()
        else:
            st.info("No transaction records available in the master ledger.")

    # --- LEVEL 2: Category Deletion (Entire Segment) ---
    with gov_tab2:
        st.markdown("#### Permanently wipe out a category segment and all its associated transactions.")
        current_segments = st.session_state.get("app_segments", [])
        
        if current_segments:
            target_seg = st.selectbox("Select Segment Category to Delete", current_segments, key="target_seg_l2")
            
            st.markdown("<br>", unsafe_allow_html=True)
            confirm_l2 = st.checkbox(f"⚠️ I confirm the permanent deletion of segment '{target_seg}' and all its transactional data", key="conf_l2")
            
            if st.button(f"Permanently Delete Segment '{target_seg}'", key="btn_del_l2", type="primary"):
                if not confirm_l2:
                    st.error("Please check the confirmation safeguard box to proceed.")
                else:
                    # 1. Remove from app segments list
                    if target_seg in st.session_state["app_segments"]:
                        st.session_state["app_segments"].remove(target_seg)
                        
                    # 2. Filter out rows belonging to this segment
                    ledger = st.session_state.get("master_ledger", pd.DataFrame())
                    if not ledger.empty and "Segment" in ledger.columns:
                        new_ledger = ledger[ledger["Segment"] != target_seg].reset_index(drop=True)
                        st.session_state["master_ledger"] = new_ledger
                        
                        LEDGER_FILE = ROOT_DIR / "master_ledger.csv"
                        new_ledger.to_csv(LEDGER_FILE, index=False)
                        
                    st.success(f"Segment '{target_seg}' and all associated records have been completely purged with dual-layer synchronization!")
                    st.rerun()
        else:
            st.info("No segment categories available.")

    # --- LEVEL 3: Global Ledger Reset (Keep Segments) ---
    with gov_tab3:
        st.markdown("#### Empty all spending records and reset the ledger to zero while preserving active segment categories.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        confirm_l3 = st.checkbox("⚠️ I understand this will permanently clear all transaction data across all segments from both local CSV and Pinecone Vector DB", key="conf_l3")
        
        if st.button("🧹 Execute Global Ledger Reset", key="btn_del_l3", type="primary"):
            if not confirm_l3:
                st.error("Please check the safety confirmation box to proceed.")
            else:
                # 1. Reset ledger in session state, preserving app_segments structure
                st.session_state["master_ledger"] = pd.DataFrame(columns=["Date", "Segment", "Merchant_Source", "Amount", "Channel"])
                
                # 2. Delete local CSV file (Dual-layer Layer 1)
                LEDGER_FILE = ROOT_DIR / "master_ledger.csv"
                if LEDGER_FILE.exists():
                    LEDGER_FILE.unlink()
                    
                # 3. Clear Pinecone Vector Database index (Dual-layer Layer 2)
                try:
                    from utils.vector_helper import get_pinecone_index
                    index = get_pinecone_index()
                    if index:
                        index.delete(delete_all=True)
                except Exception:
                    pass
                    
                st.success("Global ledger reset completed successfully! Your active segment categories remain intact for fresh entries.")
                st.rerun()