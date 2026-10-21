import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from utils.state_manager import init_state, load_css

st.set_page_config(page_title="Segment Analytics", page_icon="📈", layout="wide")
load_css()
init_state()

st.title("📊 Segment Analytics & Trend Overview")

# Load Ledger from CSV / Session State
LEDGER_FILE = Path(__file__).resolve().parent.parent / "master_ledger.csv"
df = st.session_state.get("master_ledger", pd.DataFrame())
if df.empty and LEDGER_FILE.exists():
    df = pd.read_csv(LEDGER_FILE)

if df.empty:
    st.info("No transaction data available yet. Please add entries via the **Data Ingestion** page.")
else:
    # Ensure Date column is datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    
    # --- Top Global KPI Metric Cards ---
    st.subheader("Global Key Performance Indicators")
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    
    total_spend = df["Amount"].sum()
    total_transactions = len(df)
    unique_merchants = df["Merchant_Source"].nunique() if "Merchant_Source" in df.columns else 0
    avg_transaction = df["Amount"].mean() if total_transactions > 0 else 0.0
    
    col_k1.metric("Total Spend", f"₹ {total_spend:,.2f}")
    col_k2.metric("Total Transactions", f"{total_transactions}")
    col_k3.metric("Unique Merchants", f"{unique_merchants}")
    col_k4.metric("Average / Tx", f"₹ {avg_transaction:,.2f}")

    st.markdown("---")

    # --- Custom Gradient KPI Cards for Each Segment ---
    st.subheader("Segment Budget & Share Breakdown")
    if "Segment" in df.columns and not df.empty:
        segment_totals = df.groupby("Segment")["Amount"].sum().reset_index()
        total_global_spend = segment_totals["Amount"].sum()
        
        # Predefined list of gorgeous gradient color schemes matching your reference image
        gradients = [
            "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",  # Blue
            "linear-gradient(135deg, #f97316 0%, #c2410c 100%)",  # Orange
            "linear-gradient(135deg, #14b8a6 0%, #0f766e 100%)",  # Teal
            "linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)",  # Purple
            "linear-gradient(135deg, #ec4899 0%, #be185d 100%)",  # Pink
        ]
        
        # Render cards dynamically in columns
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
                <div style="font-size: 26px; font-weight: 700; margin-top: 8px;">
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

    # --- Timeline & Segment Filters ---
    st.subheader("Filter Timeline & Grouping")
    f_col1, f_col2 = st.columns(2)
    
    with f_col1:
        time_group = st.selectbox("Group Trend By", ["Daily", "Monthly"], key="time_group_select")
        
    with f_col2:
        segments = ["All"] + list(df["Segment"].unique()) if "Segment" in df.columns else ["All"]
        selected_seg = st.selectbox("Filter Segment", segments, key="seg_filter_select")

    # Filter dataframe based on segment selection
    filtered_df = df.copy()
    if selected_seg != "All":
        filtered_df = filtered_df[filtered_df["Segment"] == selected_seg]

    st.markdown("---")

    # --- Multi-Line Chart Section with Optimized Scaling ---
    st.subheader("📈 Multi-Segment Trend Line Chart")
    if not filtered_df.empty:
        # Format timeline period
        if time_group == "Monthly":
            filtered_df["Period"] = filtered_df["Date"].dt.to_period("M").astype(str)
        else:
            filtered_df["Period"] = filtered_df["Date"].dt.strftime("%Y-%m-%d")

        # Group by Period and Segment to create multi-series data
        trend_pivot = filtered_df.groupby(["Period", "Segment"])["Amount"].sum().reset_index()

        # Render interactive multi-line chart with Plotly
        fig = px.line(
            trend_pivot, 
            x="Period", 
            y="Amount", 
            color="Segment", 
            markers=True,
            title=f"Spending Trend ({time_group}) by Segment",
            labels={"Period": "Timeline Date", "Amount": "Total Spend (₹)", "Segment": "Business Segment"}
        )
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#333333"),
            xaxis=dict(showgrid=True, gridcolor="#f0f2f6"),
            yaxis=dict(showgrid=True, gridcolor="#f0f2f6", tickprefix="₹ "),
            legend=dict(title="Segments", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction data available for this timeline filter.")

    st.markdown("---")

    # --- Breakdown Tables & CSV Export ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Segment Breakdown Summary")
        if "Segment" in filtered_df.columns and not filtered_df.empty:
            seg_grouped = filtered_df.groupby("Segment")["Amount"].sum().reset_index()
            seg_grouped = seg_grouped.sort_values(by="Amount", ascending=False)
            st.dataframe(seg_grouped.rename(columns={"Segment": "Category Segment", "Amount": "Total Spend (₹)"}), use_container_width=True, hide_index=True)
        else:
            st.info("No segment distribution data available.")

    with col2:
        st.subheader("Top Merchants in View")
        if "Merchant_Source" in filtered_df.columns and not filtered_df.empty:
            merch_grouped = filtered_df.groupby("Merchant_Source")["Amount"].sum().reset_index()
            merch_grouped = merch_grouped.sort_values(by="Amount", ascending=False).head(5)
            st.dataframe(merch_grouped.rename(columns={"Merchant_Source": "Merchant / Vendor", "Amount": "Total Spend (₹)"}), use_container_width=True, hide_index=True)
        else:
            st.info("No merchant data available.")

    # CSV Download Button for Presentation / Live Demo
    st.markdown("---")
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Segment Analytics (CSV)",
        data=csv_data,
        file_name="segment_analytics_export.csv",
        mime="text/csv",
    )