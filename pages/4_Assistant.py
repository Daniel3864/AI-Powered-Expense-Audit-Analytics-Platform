import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.db_helper import fetch_transactions
from utils.vector_helper import (
    get_pinecone_index,
    query_pinecone_transactions,
)

st.set_page_config(
    page_title="AI RAG Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        .hero {
            padding: 1.5rem;
            border-radius: 14px;
            background: linear-gradient(120deg, #14213d, #263f66);
            color: white;
            margin-bottom: 1.5rem;
        }

        .hero h1 {
            margin-bottom: 0.4rem;
            color: white;
        }

        .hero p {
            margin-bottom: 0;
            color: #e1e8f5;
        }

        div[data-testid="stMetric"] {
            background: var(--secondary-background-color);
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }

        .section-note {
            color: #808a99;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🤖 AI RAG Assistant</h1>
        <p>
            Search company spending, retrieve transaction precedents,
            and review audit findings from one place.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Search
# --------------------------------------------------
st.subheader("🔎 Search & Audit")

st.caption(
    "Search your master ledger and retrieve semantically related "
    "records from Pinecone."
)

with st.form("audit_search_form"):
    query = st.text_input(
        "Policy, merchant, or audit query",
        placeholder="e.g., Fertilizers, Seed, SBI Loan",
        help="Enter a merchant name, spending category, or policy-related question.",
    )

    col1, col2 = st.columns([1, 5])

    with col1:
        submitted = st.form_submit_button(
            "🔍 Search & Audit",
            type="primary",
            use_container_width=True,
        )

    with col2:
        st.markdown(
            '<p class="section-note">'
            "Examples: Fertilizers · Seed · SBI Loan · "
            "Unusual expenditure"
            "</p>",
            unsafe_allow_html=True,
        )

# Keep the most recent search visible across Streamlit reruns.
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None

if submitted:
    if not query.strip():
        st.warning("Please enter a query before starting your audit.")
    else:
        search_query = query.strip()

        # Load the master ledger.
        with st.spinner("Loading master ledger..."):
            try:
                df = st.session_state.get("master_ledger")

                if not isinstance(df, pd.DataFrame) or df.empty:
                    df = fetch_transactions()

                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame()

            except Exception as e:
                df = pd.DataFrame()
                st.error(f"Unable to load the transaction ledger: {e}")

        # --------------------------------------------------
        # Local ledger search
        # --------------------------------------------------
        local_matches = pd.DataFrame()
        merchant_col = next(
            (
                col
                for col in [
                    "Merchant_Source",
                    "Merchant",
                    "Merchant/Source",
                ]
                if not df.empty and col in df.columns
            ),
            None,
        )

        if not df.empty and merchant_col:
            # Retain the original substring-based merchant search.
            # Also try a basic plural variation.
            q_lower = search_query.casefold()
            search_terms = {q_lower}

            if len(q_lower) > 3 and q_lower.endswith("s"):
                search_terms.add(q_lower[:-1])
            elif len(q_lower) > 2:
                search_terms.add(q_lower + "s")

            merchant_values = (
                df[merchant_col]
                .fillna("")
                .astype(str)
                .str.casefold()
            )

            mask = merchant_values.apply(
                lambda value: any(
                    term in value for term in search_terms if term
                )
            )

            local_matches = df.loc[mask].copy()

        # --------------------------------------------------
        # Amount calculation
        # --------------------------------------------------
        amount_col = (
            "Amount"
            if not local_matches.empty and "Amount" in local_matches.columns
            else None
        )

        total_matched = 0.0

        if amount_col:
            # Handle values such as "₹ 1,250.00".
            amounts = (
                local_matches[amount_col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.strip()
            )

            amounts = pd.to_numeric(amounts, errors="coerce")
            total_matched = float(amounts.sum())

        # --------------------------------------------------
        # Pinecone semantic search
        # --------------------------------------------------
        matched_records = []
        pinecone_error = None

        with st.spinner(
            "Searching Pinecone for semantically related transactions..."
        ):
            try:
                get_pinecone_index()
                matched_records = query_pinecone_transactions(
                    search_query,
                    top_k=3,
                ) or []
            except Exception as e:
                pinecone_error = str(e)

        # Save results so they remain visible after subsequent reruns.
        st.session_state.audit_results = {
            "query": search_query,
            "ledger": df,
            "matches": local_matches,
            "amount_col": amount_col,
            "total": total_matched,
            "records": matched_records,
            "pinecone_error": pinecone_error,
            "merchant_col": merchant_col,
        }

# --------------------------------------------------
# Display most recent results
# --------------------------------------------------
results = st.session_state.audit_results

if results:
    search_query = results["query"]
    local_matches = results["matches"]
    matched_records = results["records"]
    total_matched = results["total"]
    pinecone_error = results["pinecone_error"]

    st.divider()

    st.subheader("📊 Audit Overview")
    st.caption(f"Showing results for: **{search_query}**")

    # Metrics
    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Ledger Matches",
            f"{len(local_matches):,}",
        )

    with metric2:
        st.metric(
            "Matched Expenditure",
            f"₹ {total_matched:,.2f}",
            help=(
                "Sum of the matched Amount column. "
                "Check the underlying records before using this for reporting."
            ),
        )

    with metric3:
        st.metric(
            "Semantic Results",
            f"{len(matched_records):,}",
        )

    # --------------------------------------------------
    # Ledger results
    # --------------------------------------------------
    st.subheader("📒 Master Ledger Transactions")

    if not local_matches.empty:
        st.success(
            f"Found {len(local_matches):,} direct ledger match(es)."
        )

        st.dataframe(
            local_matches,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = local_matches.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇️ Download Matching Transactions (CSV)",
            data=csv_data,
            file_name="audit_matching_transactions.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "No direct merchant-name matches were found in the master ledger."
        )

        if results["ledger"].empty:
            st.caption(
                "The ledger is empty or unavailable. "
                "Check your database connection or Data Ingestion page."
            )
        elif not results["merchant_col"]:
            st.caption(
                "A recognized merchant column was not found. "
                "Expected Merchant_Source, Merchant, or Merchant/Source."
            )

    # --------------------------------------------------
    # Semantic results
    # --------------------------------------------------
    st.subheader("🧠 Retrieved Semantic Precedents")

    if pinecone_error:
        st.warning(
            "Pinecone search could not be completed. "
            "Ledger results are still available.\n\n"
            f"Details: {pinecone_error}"
        )
    elif matched_records:
        st.caption(
            "These records were retrieved by vector search. "
            "They may be relevant even if the merchant names differ."
        )

        for i, rec in enumerate(matched_records, start=1):
            with st.container(border=True):
                st.markdown(
                    f"**Precedent {i}** · "
                    f"{rec.get('merchant') or 'Unknown merchant'}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.caption("Date")
                    st.write(rec.get("date") or "Not available")

                with col2:
                    st.caption("Segment")
                    st.write(rec.get("segment") or "Not available")

                with col3:
                    st.caption("Amount")
                    amount = rec.get("amount")

                    if amount is not None:
                        try:
                            st.write(f"₹ {float(amount):,.2f}")
                        except (TypeError, ValueError):
                            st.write(str(amount))
                    else:
                        st.write("Not available")
    else:
        st.info("No semantic precedents were returned by Pinecone.")

    # --------------------------------------------------
    # Audit summary
    # --------------------------------------------------
    st.divider()
    st.subheader("💡 Assistant Audit Summary")

    if not local_matches.empty:
        st.markdown(
            f"""
            - **Query evaluated:** {search_query}
            - **Direct ledger matches:** {len(local_matches):,}
            - **Matched expenditure:** ₹ {total_matched:,.2f}
            - **Semantic precedents retrieved:** {len(matched_records):,}
            - **Status:** Direct ledger records were found.
            """
        )

        if pinecone_error:
            st.warning(
                "The semantic search was unavailable. "
                "The audit summary reflects ledger results only."
            )

        st.caption(
            "This is a search summary, not an independent verification "
            "of policy compliance or fraud. Review the underlying "
            "transactions and applicable policy before making an audit decision."
        )

    elif matched_records:
        st.markdown(
            f"""
            - **Query evaluated:** {search_query}
            - **Direct ledger matches:** 0
            - **Semantic precedents:** {len(matched_records)}
            - **Status:** Related records were retrieved, but no direct
              merchant-name matches were found.
            """
        )

        st.info(
            "Review the retrieved precedents manually. Semantic similarity "
            "does not establish that a transaction violates policy."
        )

    else:
        st.markdown(
            f"""
            - **Query evaluated:** {search_query}
            - **Direct ledger matches:** 0
            - **Semantic precedents:** 0
            - **Status:** No results were found by the available searches.
            """
        )

        st.info(
            "Check the query spelling, verify that transactions have been "
            "ingested, and confirm that the Pinecone index contains the "
            "expected records."
        )

else:
    # Initial empty state
    st.divider()

    st.subheader("🚀 Get Started")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📒 Ledger Search")
        st.write(
            "Find transactions using merchant names and inspect matching records."
        )

    with col2:
        st.markdown("#### 🧠 Semantic Retrieval")
        st.write(
            "Retrieve related transaction precedents from your Pinecone index."
        )

    with col3:
        st.markdown("#### 💡 Audit Insights")
        st.write(
            "Review matched expenditure, result counts, and suggested next steps."
        )
