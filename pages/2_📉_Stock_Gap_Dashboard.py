"""
STOCK GAP DASHBOARD
------------------------------------------------------------
Matches a live Order sheet against a live Stock workbook — both read
straight from SharePoint/OneDrive share links (no file uploads) — and
shows exactly where orders exceed available stock.

Ported from the original browser-only HTML tool. That version needed
someone to manually upload the stock file each time and "publish" it
for the team; since both files are now live links, that admin/publish
step is gone — this page just always reads the current file.

SETUP: add two links to this app's Secrets —
    STOCK_EXCEL_URL       -> the stock workbook (multi-sheet)
    STOCK_ORDER_EXCEL_URL -> the order sheet to check against stock

CONFIG below controls sheet names / column mapping for the STOCK
workbook — edit this block directly if sheet names or columns ever
change; nothing else in the file needs to change. The ORDER sheet's
columns are picked from dropdowns on the page itself (its layout
varies more than the stock workbook does), with a best-guess default.
------------------------------------------------------------
"""

import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Stock Gap Dashboard", layout="wide", page_icon="📉")

# ================================================================
# CONFIG — edit any time the STOCK workbook's sheet names or
# columns change. Nothing else in the script needs to change.
# ================================================================
CONFIG = {
    # Row number (1-indexed) where the real column headers sit in
    # every stock sheet.
    "stock_header_row": 1,

    # Which sheets to read from the stock workbook, and which column
    # LETTER holds EAN / Product Name in each one.
    "stock_sheets": [
        {"name": "Sheet1", "ean_col": "A", "name_col": "B"},
    ],

    # Header TEXT (not column letter) for each stock quantity type —
    # matched by searching each sheet's header row, so it still works
    # even if the column position shifts between sheets.
    "qty_headers": {
        "mwh": "MWH Stock",         # used for Ahmedabad comparison
        "blr": "Direct Shelf BLR",  # used for Bangalore comparison
        "uc": "UC INVENTORY",       # shown alongside for Ahmedabad only
    },

    # When the same EAN appears in more than one sheet above, its
    # quantities are summed together across all of them.
    "order_header_row": 1,
    "order_ean_col_guess": ["ean", "barcode", "upc"],
    "order_name_col_guess": ["product", "name", "description", "item"],
    "order_qty_col_guess": ["order", "qty", "quantity", "demand"],
}


def _col_letter_to_index(letter: str) -> int:
    letter = letter.strip().upper()
    idx = 0
    for ch in letter:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _direct_download_url(url: str) -> str:
    """SharePoint/OneDrive 'view' share link -> direct download link."""
    if "download=1" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}download=1"


def _fetch_bytes(url: str) -> bytes:
    resp = requests.get(_direct_download_url(url), timeout=30)
    resp.raise_for_status()
    if "html" in resp.headers.get("Content-Type", "").lower():
        raise ValueError(
            "Got a login/redirect page instead of the file — the share "
            "link likely needs broader access ('Anyone with the link can view')."
        )
    return resp.content


def _find_header_col(columns, header_text):
    target = header_text.strip().lower()
    for c in columns:
        if str(c).strip().lower() == target:
            return c
    return None


def _guess_col(columns, hints):
    cols_lower = {str(c).lower(): c for c in columns}
    for hint in hints:
        for cl, orig in cols_lower.items():
            if hint in cl:
                return orig
    return columns[0] if len(columns) else None


@st.cache_data(ttl=300, show_spinner="Fetching latest stock…")
def load_stock(url: str) -> pd.DataFrame:
    raw = _fetch_bytes(url)
    hdr_idx = CONFIG["stock_header_row"] - 1
    combined = {}
    skipped_sheets = []

    for sheet_cfg in CONFIG["stock_sheets"]:
        try:
            sdf = pd.read_excel(io.BytesIO(raw), sheet_name=sheet_cfg["name"], header=hdr_idx)
        except Exception:
            skipped_sheets.append(sheet_cfg["name"])
            continue
        sdf.columns = [str(c).strip() for c in sdf.columns]

        ean_idx = _col_letter_to_index(sheet_cfg["ean_col"])
        name_idx = _col_letter_to_index(sheet_cfg["name_col"])
        if ean_idx >= len(sdf.columns) or name_idx >= len(sdf.columns):
            skipped_sheets.append(sheet_cfg["name"])
            continue

        mwh_col = _find_header_col(sdf.columns, CONFIG["qty_headers"]["mwh"])
        blr_col = _find_header_col(sdf.columns, CONFIG["qty_headers"]["blr"])
        uc_col = _find_header_col(sdf.columns, CONFIG["qty_headers"]["uc"])

        ean_series = sdf.iloc[:, ean_idx]
        name_series = sdf.iloc[:, name_idx]
        mwh_series = pd.to_numeric(sdf[mwh_col], errors="coerce") if mwh_col else None
        blr_series = pd.to_numeric(sdf[blr_col], errors="coerce") if blr_col else None
        uc_series = pd.to_numeric(sdf[uc_col], errors="coerce") if uc_col else None

        for i in range(len(sdf)):
            if pd.isna(ean_series.iloc[i]):
                continue
            ean = str(ean_series.iloc[i]).strip()
            if not ean:
                continue
            key = ean.lower()
            name = str(name_series.iloc[i]).strip() if pd.notna(name_series.iloc[i]) else ""
            mwh = float(mwh_series.iloc[i]) if mwh_series is not None and pd.notna(mwh_series.iloc[i]) else 0.0
            blr = float(blr_series.iloc[i]) if blr_series is not None and pd.notna(blr_series.iloc[i]) else 0.0
            uc = float(uc_series.iloc[i]) if uc_series is not None and pd.notna(uc_series.iloc[i]) else 0.0

            if key not in combined:
                combined[key] = {"ean": ean, "product": name, "mwh": 0.0, "blr": 0.0, "uc": 0.0}
            row = combined[key]
            if not row["product"] and name:
                row["product"] = name
            row["mwh"] += mwh
            row["blr"] += blr
            row["uc"] += uc

    result = pd.DataFrame(list(combined.values()))
    result.attrs["skipped_sheets"] = skipped_sheets
    return result


@st.cache_data(ttl=300, show_spinner="Fetching latest orders…")
def load_orders(url: str) -> pd.DataFrame:
    raw = _fetch_bytes(url)
    odf = pd.read_excel(io.BytesIO(raw), header=CONFIG["order_header_row"] - 1)
    odf.columns = [str(c).strip() for c in odf.columns]
    return odf


def parse_uploaded_orders(file_bytes: bytes, filename: str, header_row: int) -> pd.DataFrame:
    """Parse an uploaded order file (.xlsx/.xls/.csv) using a user-chosen header row."""
    hdr_idx = header_row - 1
    if filename.lower().endswith(".csv"):
        odf = pd.read_csv(io.BytesIO(file_bytes), header=hdr_idx)
    else:
        odf = pd.read_excel(io.BytesIO(file_bytes), header=hdr_idx)
    odf.columns = [str(c).strip() for c in odf.columns]
    return odf


st.markdown("""
<style>
.stApp { background: #12151A; color: #E9EBEF; }
h1, h2, h3 { color: #E9EBEF; }
div[data-testid="stMetric"] {
    background:#1B1F27; border:1px solid #2C313C; border-radius:10px; padding:16px 18px;
}
div[data-testid="stMetricValue"] { font-family:'IBM Plex Mono', monospace; }
</style>
""", unsafe_allow_html=True)

st.title("📉 Stock Gap Dashboard")
st.caption("Matches an order sheet against live stock. Order sheet can be read live or uploaded.")

stock_url = st.secrets.get("STOCK_EXCEL_URL", "")

if not stock_url:
    st.error("Missing link. Add **STOCK_EXCEL_URL** to this app's Secrets.")
    st.stop()

top_l, top_r = st.columns([5, 1])
with top_r:
    if st.button("🔄 Refresh Now", use_container_width=True):
        load_stock.clear()
        load_orders.clear()
        st.rerun()

try:
    stock_df = load_stock(stock_url)
except Exception as e:
    st.error(f"Could not load the live stock file: {e}")
    st.stop()

# ------------------------------------------------------------
# ORDER SHEET SOURCE — live link (reads the configured
# STOCK_ORDER_EXCEL_URL) or a one-off upload with a chosen header row.
# ------------------------------------------------------------
st.markdown("#### Order Sheet")
order_source = st.radio(
    "Order sheet source", ["Live Link", "Upload File"], horizontal=True, label_visibility="collapsed"
)

order_df = None

if order_source == "Live Link":
    order_url = st.secrets.get("STOCK_ORDER_EXCEL_URL", "")
    if not order_url:
        st.error(
            "No live order link configured. Add **STOCK_ORDER_EXCEL_URL** to this "
            "app's Secrets, or switch to **Upload File** above."
        )
        st.stop()
    try:
        order_df = load_orders(order_url)
    except Exception as e:
        st.error(f"Could not load the live order file: {e}")
        st.stop()
else:
    up_col1, up_col2 = st.columns([3, 1])
    with up_col1:
        uploaded_order_file = st.file_uploader(
            "Choose order file (.xlsx / .xls / .csv)", type=["xlsx", "xls", "csv"], key="order_upload"
        )
    with up_col2:
        header_row = st.number_input(
            "Header row #", min_value=1, value=CONFIG["order_header_row"], step=1, key="order_header_row_input"
        )

    if uploaded_order_file is None:
        st.info("Upload an order sheet to continue.")
        st.stop()

    try:
        order_df = parse_uploaded_orders(uploaded_order_file.getvalue(), uploaded_order_file.name, int(header_row))
    except Exception as e:
        st.error(f"Could not parse the uploaded order file: {e}")
        st.stop()

if stock_df.empty:
    st.warning("No stock rows loaded — check CONFIG sheet names/columns still match the live workbook.")
    st.stop()

skipped = stock_df.attrs.get("skipped_sheets", [])
if skipped:
    st.caption(f"⚠️ Skipped sheet(s) not found in the workbook: {', '.join(skipped)} — check CONFIG.")

# ------------------------------------------------------------
# SETUP CONTROLS
# ------------------------------------------------------------
c1, c2, c3 = st.columns(3)
with c1:
    match_mode = st.radio("Match by", ["EAN", "Product Name"], horizontal=True)
with c2:
    order_cols = list(order_df.columns)
    default_key_col = (
        _guess_col(order_cols, CONFIG["order_ean_col_guess"]) if match_mode == "EAN"
        else _guess_col(order_cols, CONFIG["order_name_col_guess"])
    )
    key_label = "Order sheet's EAN column" if match_mode == "EAN" else "Order sheet's Product Name column"
    key_col = st.selectbox(
        key_label, order_cols,
        index=order_cols.index(default_key_col) if default_key_col in order_cols else 0,
    )
with c3:
    default_qty_col = _guess_col(order_cols, CONFIG["order_qty_col_guess"])
    qty_col = st.selectbox(
        "Order Qty column", order_cols,
        index=order_cols.index(default_qty_col) if default_qty_col in order_cols else 0,
    )

location = st.radio("Warehouse Location", ["Ahmedabad", "Bangalore"], horizontal=True)
st.caption(
    "Ahmedabad compares against **MWH Stock** (UC Inventory shown alongside). "
    "Bangalore compares against **Direct Shelf BLR** only."
)

# ------------------------------------------------------------
# MATCH
# ------------------------------------------------------------
stock_map = {}
for _, r in stock_df.iterrows():
    key = str(r["ean"]).strip().lower() if match_mode == "EAN" else str(r["product"]).strip().lower()
    stock_map[key] = r


def _compute_row(order_row):
    raw_key = order_row[key_col]
    key = str(raw_key).strip().lower() if pd.notna(raw_key) else ""
    order_qty = pd.to_numeric(order_row[qty_col], errors="coerce")
    order_qty = 0.0 if pd.isna(order_qty) else float(order_qty)

    stock_row = stock_map.get(key)
    if stock_row is None:
        return pd.Series({
            "product": raw_key if match_mode != "EAN" else "(unknown)",
            "ean": raw_key if match_mode == "EAN" else "",
            "stock": None, "uc": None, "order": order_qty, "short": None, "status": "missing",
        })

    available = stock_row["mwh"] if location == "Ahmedabad" else stock_row["blr"]
    uc_val = stock_row["uc"] if location == "Ahmedabad" else None
    short = max(order_qty - available, 0)
    if short > 0:
        status = "stockout"
    elif available > 0 and order_qty > 0 and (available - order_qty) <= available * 0.15:
        status = "low"
    else:
        status = "ok"
    return pd.Series({
        "product": stock_row["product"] or raw_key, "ean": stock_row["ean"],
        "stock": available, "uc": uc_val, "order": order_qty, "short": short, "status": status,
    })


if st.button("Match & Build Dashboard", type="primary"):
    st.session_state["gap_results"] = order_df.apply(_compute_row, axis=1)
    st.session_state["gap_location"] = location

results = st.session_state.get("gap_results")

if results is not None and len(results):
    total_skus = len(results)
    short_skus = int((results["status"] == "stockout").sum())
    units_short = float(results["short"].fillna(0).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("SKUs Ordered", f"{total_skus:,}")
    m2.metric("SKUs Short / Out", f"{short_skus:,}")
    m3.metric("Units Short", f"{units_short:,.0f}")

    fcol, scol = st.columns([2, 1])
    with fcol:
        status_filter = st.radio("Filter", ["All", "Stockout", "Low", "Not Found"], horizontal=True, key="gap_status_filter")
    with scol:
        gap_search = st.text_input("Search product / EAN", key="gap_search")

    view = results.copy()
    status_map = {"Stockout": "stockout", "Low": "low", "Not Found": "missing"}
    if status_filter != "All":
        view = view[view["status"] == status_map[status_filter]]
    if gap_search:
        s = gap_search.lower()
        view = view[
            view["product"].astype(str).str.lower().str.contains(s, na=False)
            | view["ean"].astype(str).str.lower().str.contains(s, na=False)
        ]

    view = view.sort_values("short", ascending=False, na_position="last")

    show_cols = ["product", "ean", "stock", "order", "short", "status"]
    if st.session_state.get("gap_location") == "Ahmedabad":
        show_cols.insert(3, "uc")

    label_map = {
        "product": "Product", "ean": "EAN", "stock": "Available", "uc": "UC Inventory",
        "order": "Ordered", "short": "Short", "status": "Status",
    }
    display = view[show_cols].rename(columns=label_map)

    column_config = {
        "Available": st.column_config.NumberColumn(format="localized"),
        "UC Inventory": st.column_config.NumberColumn(format="localized"),
        "Ordered": st.column_config.NumberColumn(format="localized"),
        "Short": st.column_config.NumberColumn(format="localized"),
    }
    st.dataframe(display, use_container_width=True, hide_index=True, height=560, column_config=column_config)

    csv_cols = list(label_map.values())
    csv = view.rename(columns=label_map)[csv_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export CSV", csv,
        file_name=f"stock_gap_results_{(st.session_state.get('gap_location') or '').lower()}.csv",
        mime="text/csv",
    )
else:
    st.info("Set the columns above and click **Match & Build Dashboard** to see the gap analysis.")
