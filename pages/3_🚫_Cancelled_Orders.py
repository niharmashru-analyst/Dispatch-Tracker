"""
CANCELLED ORDERS — filtered view of the dispatch tracker
------------------------------------------------------------
Reads the same live dispatch tracker file used by the Order Tracking
page (SHAREPOINT_EXCEL_URL secret) and shows only the rows whose
remarks column matches one of a small set of "cancelled" phrases —
e.g. "Order below 7k". Edit CANCEL_COLUMN / CANCEL_TERMS below, or
use the "Manage cancel terms" box on the page itself, whenever the
exact wording changes.

Drop this file into the same pages/ folder as the other dashboard
pages so Streamlit's sidebar picks it up automatically. Rename it
with a leading number (e.g. 3_Cancelled_Orders.py) to control where
it sits in the sidebar relative to the other pages.
------------------------------------------------------------
"""

import io
import re
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Cancelled Orders", layout="wide", page_icon="🚫")

# ================================================================
# CONFIG — edit any time the remarks wording or column changes.
# ================================================================
CONFIG = {
    # Column in the dispatch tracker that holds the cancellation reason.
    # Change this if your sheet uses a different header.
    "cancel_column": "Wh. Remarks",

    # Phrases that mark a row as cancelled. Matching is a
    # case-insensitive substring match, so "order below 7k" also
    # catches "Order Below 7K - customer declined", etc.
    # This is a starting guess for the 4-5 terms you mentioned —
    # edit this list, or just adjust it live on the page below.
    "cancel_terms": [
        "Order below 7k",
        "Below 7k Value Cancel",
        "Cancel Under 5K Value",
        "Low Qty Not Processed",
        "Out Of Stock",
    ],

    # Columns shown by default in the results table.
    "default_visible_columns": [
        "Order Id", "Customer Name", "Order Received Date", "Order Qty",
        "Order Value", "AWB NUMBER", "COURIER", "Final Remarks",
    ],
}

DATE_COL_HINTS = ["date"]
CURRENCY_COL_HINTS = ["value", "lacs", "sale loss"]
PERCENT_COL_HINTS = ["%"]

C_BG = "#F4F6FA"


def _looks_like(col, hints):
    c = col.lower()
    return any(h in c for h in hints)


def _sharepoint_download_url(url: str) -> str:
    if "download=1" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}download=1"


@st.cache_data(ttl=300, show_spinner="Fetching latest data…")
def load_data(url: str) -> pd.DataFrame:
    resp = requests.get(_sharepoint_download_url(url), timeout=30)
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "")
    if "html" in ctype.lower():
        raise ValueError(
            "Got a login/redirect page instead of the Excel file — "
            "the share link likely needs broader access (set it to "
            "'Anyone with the link can view')."
        )

    df = pd.read_excel(io.BytesIO(resp.content), sheet_name=None)
    if isinstance(df, dict):  # multiple tabs -> take the first one
        df = next(iter(df.values()))
    df.columns = [str(c).strip() for c in df.columns]

    for col in df.columns:
        if _looks_like(col, DATE_COL_HINTS):
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        elif _looks_like(col, CURRENCY_COL_HINTS):
            cleaned = (
                df[col].astype(str)
                .str.replace("₹", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(cleaned, errors="coerce")
        elif _looks_like(col, PERCENT_COL_HINTS):
            cleaned = df[col].astype(str).str.replace("%", "", regex=False).str.strip()
            df[col] = pd.to_numeric(cleaned, errors="coerce")

    return df


st.markdown(f"""
<style>
.stApp {{ background: {C_BG}; }}
div[data-testid="stMetric"] {{
    background:#fff; border-radius:14px; padding:14px 16px;
    box-shadow:0 1px 3px rgba(0,0,0,.08);
}}
</style>
""", unsafe_allow_html=True)

st.title("🚫 Cancelled Orders")
st.caption("Rows from the dispatch tracker whose remarks match a configured cancel reason.")

sp_url = st.secrets.get("SHAREPOINT_EXCEL_URL", "")
if not sp_url:
    st.error(
        "No SharePoint link configured. Add SHAREPOINT_EXCEL_URL to this app's "
        "Secrets (the same link used by the Order Tracking page)."
    )
    st.stop()

top_l, top_r = st.columns([5, 1])
with top_r:
    if st.button("🔄 Refresh Now", use_container_width=True):
        load_data.clear()
        st.rerun()

try:
    df = load_data(sp_url)
except Exception as e:
    st.error(f"Could not load the live file: {e}")
    st.stop()

cancel_col = CONFIG["cancel_column"]
if cancel_col not in df.columns:
    st.error(
        f"Column '{cancel_col}' not found in the dispatch tracker. "
        f"Available columns: {', '.join(df.columns)}. "
        "Update CONFIG['cancel_column'] at the top of this file to match."
    )
    st.stop()

# ------------------------------------------------------------
# TERMS — editable on the page, seeded from CONFIG above.
# ------------------------------------------------------------
with st.expander("Manage cancel terms", expanded=False):
    active_terms = st.multiselect(
        "Terms that mark a row as cancelled (substring match, case-insensitive)",
        options=CONFIG["cancel_terms"],
        default=CONFIG["cancel_terms"],
        key="active_cancel_terms",
    )
    extra_terms_raw = st.text_input(
        "Add extra terms (comma-separated)", key="extra_cancel_terms"
    )
    extra_terms = [t.strip() for t in extra_terms_raw.split(",") if t.strip()]

all_terms = [t for t in (active_terms + extra_terms) if t]

if not all_terms:
    st.warning("No cancel terms selected — pick at least one above to see results.")
    st.stop()

pattern = "|".join(re.escape(t) for t in all_terms)
mask = df[cancel_col].astype(str).str.contains(pattern, case=False, na=False, regex=True)
cancelled = df[mask].copy()

st.caption(f"Matching terms: {', '.join(all_terms)}")

# ------------------------------------------------------------
# METRICS
# ------------------------------------------------------------
m1, m2 = st.columns(2)
m1.metric("Cancelled Orders", f"{len(cancelled):,}")
value_col = next(
    (c for c in cancelled.columns if "order" in c.lower() and _looks_like(c, ["value"])), None
)
if value_col:
    m2.metric("Cancelled Value", f"₹ {cancelled[value_col].fillna(0).sum():,.0f}")

# ------------------------------------------------------------
# RESULTS TABLE
# ------------------------------------------------------------
all_cols = list(df.columns)
default_cols = [c for c in CONFIG["default_visible_columns"] if c in all_cols] or all_cols[:8]
with st.expander("Columns to show"):
    visible_cols = st.multiselect(
        "Columns to show", all_cols, default=default_cols,
        key="visible_cols", label_visibility="collapsed",
    )
if not visible_cols:
    visible_cols = default_cols

search_term = st.text_input("🔍 Search within cancelled orders", placeholder="Order Id, Customer Name…")
view = cancelled
if search_term:
    s = search_term.lower()
    mask2 = pd.Series(False, index=view.index)
    for c in visible_cols:
        mask2 |= view[c].astype(str).str.lower().str.contains(s, na=False)
    view = view[mask2]

st.markdown(f"**{len(view):,} of {len(cancelled):,} cancelled orders**")

display_df = view[visible_cols].copy()
column_config = {}
for c in visible_cols:
    if _looks_like(c, DATE_COL_HINTS):
        column_config[c] = st.column_config.DateColumn(c, format="DD-MM-YYYY")
    elif _looks_like(c, CURRENCY_COL_HINTS):
        column_config[c] = st.column_config.NumberColumn(c, format="₹ %.2f")
    elif _looks_like(c, PERCENT_COL_HINTS):
        column_config[c] = st.column_config.NumberColumn(c, format="%.1f%%")

st.dataframe(
    display_df, use_container_width=True, hide_index=True, height=560, column_config=column_config,
)

csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export CSV", csv, file_name="cancelled_orders.csv", mime="text/csv")
