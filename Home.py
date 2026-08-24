"""
HOME — entry point for the multi-page dashboard project.

Streamlit auto-builds the sidebar page-switcher from every file inside
the pages/ folder next to this one — no manual sidebar code needed.
Deploy with this file (Home.py) set as the app's main file.
"""

import streamlit as st

st.set_page_config(page_title="Dashboards Home", layout="wide", page_icon="🏠")

st.title("🏠 Dashboards")
st.caption("Pick a dashboard from the sidebar.")

st.markdown("""
### 📦 Order Tracking
Search and filter live order/delivery data (AWB, courier, delivery status, TAT) —
reads straight from the live SharePoint file, always up to date.

### 📉 Stock Gap Dashboard
Matches a live order sheet against live stock and shows exactly where
orders exceed available stock — Ahmedabad (MWH) or Bangalore (Direct Shelf BLR).
""")

st.info("👈 Use the sidebar to switch between dashboards.")
