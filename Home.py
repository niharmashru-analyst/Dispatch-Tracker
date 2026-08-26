"""
HOME — entry point for the multi-page dashboard project.
Streamlit auto-builds the sidebar page-switcher from every file inside
the pages/ folder next to this one — no manual sidebar code needed.
Deploy with this file (Home.py) set as the app's main file.

IMPORTANT: the "path" for each card below must exactly match the
filename of that page inside your pages/ folder (case-sensitive,
including any leading number you use to control sidebar order, e.g.
"pages/1_Order_Tracking.py"). Update the PAGES list below if your
actual filenames are different.
"""
import streamlit as st

st.set_page_config(page_title="Dashboards Home", layout="wide", page_icon="🏠")

# ================================================================
# PAGES — one card per dashboard. Edit "path" to match your real
# filenames in pages/, and add/remove entries as pages change.
# ================================================================
PAGES = [
    {
        "path": "pages/1_Order_Tracking.py",
        "icon": "📦",
        "title": "Order Tracking",
        "description": "Search and filter live order/delivery data (AWB, courier, "
                        "delivery status, TAT) — reads straight from the live "
                        "SharePoint file, always up to date.",
    },
    {
        "path": "pages/2_Stock_Gap_Dashboard.py",
        "icon": "📉",
        "title": "Stock Gap Dashboard",
        "description": "Matches a live order sheet against live stock and shows "
                        "exactly where orders exceed available stock — Ahmedabad "
                        "(MWH) or Bangalore (Direct Shelf BLR).",
    },
    {
        "path": "pages/3_Cancelled_Orders.py",
        "icon": "🚫",
        "title": "Cancelled Orders",
        "description": "Filtered view of the dispatch tracker showing only rows "
                        "matching configured cancel-reason terms (e.g. \"Order "
                        "below 7k\") — editable on the page itself.",
    },
    {
        "path": "pages/4_Fill_Rate.py",
        "icon": "📶",
        "title": "Fill Rate",
        "description": "Compares Fill Rate (Invoice Qty / Order Qty) across chains "
                        "with a bar chart, then a shop-by-shop breakdown — click a "
                        "shop to see every order behind its numbers.",
    },
]

st.markdown("""
<style>
.stApp { background:#F4F6FA; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background:#fff; border-radius:14px;
    box-shadow:0 1px 3px rgba(0,0,0,.08);
}
div[data-testid="stVerticalBlockBorderWrapper"] h4 { margin-bottom:4px; }
</style>
""", unsafe_allow_html=True)

st.title("🏠 Dashboards")
st.caption("Click a card to open a dashboard.")
st.write("")

cols = st.columns(2)
for i, page in enumerate(PAGES):
    with cols[i % 2]:
        with st.container(border=True):
            st.markdown(f"#### {page['icon']} {page['title']}")
            st.caption(page["description"])
            st.page_link(page["path"], label="Open →", use_container_width=True)
