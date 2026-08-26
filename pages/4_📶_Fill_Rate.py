"""
FILL RATE — chain comparison + shop-level drill-down
------------------------------------------------------------
Reads the same live dispatch tracker used by the other pages
(SHAREPOINT_EXCEL_URL secret). Shows:

  1. A bar chart comparing Fill Rate (Invoice Qty / Order Qty) across
     chains ("Name" column).
  2. Filters (Name / InvoiceNumber / Order Id / Final Remarks) — sit
     between the chart and the table, and narrow both the chart and
     the shop table below.
  3. A summary table, one row per shop ("Customer Name"), with total
     Order Qty / Invoice Qty / Fill Rate / Sale Loss / TAT (avg) for
     that shop. Click any column in the "Sort by" control to sort by
     it (toggle Ascending to flip direction). Click a shop's name (a
     plain button — no checkboxes) to open a detail popup with every
     individual order row for that shop, including DB Code, Category
     and TAT (shown as the very last column).

Drop this file into the same pages/ folder as the other dashboard
pages. Rename with a leading number (e.g. 4_Fill_Rate.py) to control
where it sits in the sidebar.

NOTE ON ASSUMPTIONS (edit CONFIG below if any of these are wrong):
  - "Order Id" / "InvoiceNumber" in the shop SUMMARY table are shown
    as a COUNT of distinct orders/invoices for that shop (a shop
    usually has many of each) — not a single ID. The full IDs are
    all visible in the per-shop detail popup.
  - "Wh Receiving Date", "Invoice Date", "Delivery Date",
    "Actual Deli. Days", "Variance", "DB Code", "Category" are
    assumed to already exist as columns in the dispatch tracker
    (same naming as the sheet).
  - "TAT" is assumed to be its own column already in (or being added
    to) the dispatch tracker sheet, holding a number (days). We don't
    rename/relabel it — whatever header you give it in the sheet is
    what shows up here. In the shop detail popup it's placed as the
    LAST column. In the shop summary table it's shown as an average
    ("TAT (avg)") and is a selectable/sortable metric like the rest.
    If the actual column name in your sheet differs from "TAT",
    update CONFIG["tat_column"] below.
------------------------------------------------------------
"""

import io
import requests
import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Fill Rate", layout="wide", page_icon="📶")

# ================================================================
# CONFIG — edit any time a column name changes in the source sheet.
# ================================================================
CONFIG = {
    "chain_column": "Name",
    "shop_column": "Customer Name",
    "order_id_column": "Order Id",
    "invoice_number_column": "InvoiceNumber",
    "order_qty_column": "Order Qty",
    "invoice_qty_column": "Invoice Qty",
    "sale_loss_column": "Sale Loss",
    "wh_receiving_date_column": "Wh Receiving Date",
    "invoice_date_column": "Invoice Date",
    "delivery_date_column": "Delivery Date",
    "actual_delivery_days_column": "Actual Deli. Days",
    "variance_column": "Variance",
    "db_code_column": "DB Code",
    "category_column": "Category",
    "tat_column": "TAT",
}

FILTER_COLUMNS = [
    CONFIG["chain_column"], CONFIG["invoice_number_column"],
    CONFIG["order_id_column"], "Final Remarks",
]

DEFAULT_SORT_KEY = "fill_rate"
DEFAULT_SORT_ASC = True  # worst fill rate first

DATE_COL_HINTS = ["date"]
CURRENCY_COL_HINTS = ["value", "lacs", "sale loss"]
PERCENT_COL_HINTS = ["%"]
# Order Qty / Invoice Qty / TAT aren't caught by the hints above, but
# Excel often leaves numeric-looking columns as text (stray spaces,
# commas, a blank cell forcing the whole column to object dtype) —
# which makes pandas' groupby(...).sum()/.mean() raise a TypeError.
# Force these to numeric explicitly.
QTY_COL_HINTS = ["qty", "quantity", "tat"]

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
        elif _looks_like(col, QTY_COL_HINTS):
            cleaned = df[col].astype(str).str.replace(",", "", regex=False).str.strip()
            df[col] = pd.to_numeric(cleaned, errors="coerce")

    return df


def _fill_rate(invoice_qty, order_qty):
    order_qty = order_qty.replace(0, pd.NA)
    return (pd.to_numeric(invoice_qty, errors="coerce") / pd.to_numeric(order_qty, errors="coerce") * 100).round(1)


def _right(container, text):
    container.markdown(
        f'<div style="text-align:right; padding-top:6px; white-space:nowrap;">{text}</div>',
        unsafe_allow_html=True,
    )


st.markdown(f"""
<style>
.stApp {{ background: {C_BG}; }}
div[data-testid="stMetric"] {{
    background:#fff; border-radius:14px; padding:14px 16px;
    box-shadow:0 1px 3px rgba(0,0,0,.08);
}}
/* Compact, table-row-style buttons instead of big default pills */
div.stButton > button {{
    width:100%;
    text-align:left;
    padding:0.3rem 0.75rem;
    border-radius:6px;
    border:1px solid #E4E7ED;
    background:#fff;
    font-weight:500;
    font-size:0.9rem;
    color:#1F2937;
    box-shadow:none;
}}
div.stButton > button:hover {{
    border-color:#4C6FFF;
    color:#4C6FFF;
}}

/* Bordered "grid" look for the main shop table — outer box border,
   a divider line under every row, and a divider between every
   column so it reads like a real bordered table. */
.fillrate-grid {{
    border:1px solid #E4E7ED;
    border-radius:10px;
    overflow:hidden;
    background:#fff;
}}
.fillrate-grid [data-testid="stHorizontalBlock"] {{
    border-bottom:1px solid #E4E7ED;
    padding:2px 6px;
}}
.fillrate-grid [data-testid="stHorizontalBlock"]:last-child {{
    border-bottom:none;
}}
.fillrate-grid [data-testid="stHorizontalBlock"] > div:not(:last-child) {{
    border-right:1px solid #E4E7ED;
}}
/* Header row (the first row inside the grid) — clickable sort
   buttons, styled to look like a header rather than a data row. */
.fillrate-grid [data-testid="stHorizontalBlock"]:first-child {{
    background:#F8F9FC;
}}
.fillrate-grid [data-testid="stHorizontalBlock"]:first-child div.stButton > button {{
    font-weight:700;
    color:#1F2937;
    background:transparent;
    border:none;
    box-shadow:none;
}}
.fillrate-grid div.stButton > button {{
    border:none;
    border-radius:0;
    box-shadow:none;
}}
</style>
""", unsafe_allow_html=True)

st.title("📶 Fill Rate")
st.caption("Chain comparison, then a shop-by-shop breakdown — click a shop to see every order behind its numbers.")

sp_url = st.secrets.get("SHAREPOINT_EXCEL_URL", "")
if not sp_url:
    st.error(
        "No SharePoint link configured. Add SHAREPOINT_EXCEL_URL to this app's "
        "Secrets (the same link used by the other pages)."
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

# Reserved here so it renders above the chain chart, but it's filled
# in further down once filters have been applied (so it always
# reflects the current filtered view, same as the chart and table).
total_metrics_slot = st.empty()

required_cols = [
    CONFIG["chain_column"], CONFIG["shop_column"],
    CONFIG["order_qty_column"], CONFIG["invoice_qty_column"],
]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(
        f"Missing required column(s): {', '.join(missing)}. "
        f"Available columns: {', '.join(df.columns)}. "
        "Update CONFIG at the top of this file to match your sheet."
    )
    st.stop()

has_sale_loss = CONFIG["sale_loss_column"] in df.columns
has_order_id = CONFIG["order_id_column"] in df.columns
has_invoice_no = CONFIG["invoice_number_column"] in df.columns
has_tat = CONFIG["tat_column"] in df.columns

chain_col = CONFIG["chain_column"]
shop_col = CONFIG["shop_column"]
oid_col = CONFIG["order_id_column"]
inv_col = CONFIG["invoice_number_column"]
oqty_col = CONFIG["order_qty_column"]
iqty_col = CONFIG["invoice_qty_column"]
sloss_col = CONFIG["sale_loss_column"]
tat_col = CONFIG["tat_column"]

# ------------------------------------------------------------
# CHAIN FILL RATE — bar chart (drawn later, after Filters below,
# but the placeholder is reserved here so it appears first).
# ------------------------------------------------------------
st.markdown("### Fill Rate by Chain")
chart_slot = st.empty()

st.markdown("---")

# ------------------------------------------------------------
# FILTERS — Name (chain), InvoiceNumber, Order Id, Final Remarks.
# Sits below the chart, above the table, and drives both.
# ------------------------------------------------------------
with st.expander("Filters", expanded=False):
    fcols = st.columns(3)
    active_filters = {}
    filter_cols_present = [c for c in FILTER_COLUMNS if c in df.columns]
    for i, col in enumerate(filter_cols_present):
        with fcols[i % 3]:
            options = sorted(df[col].dropna().astype(str).unique().tolist())
            picked = st.multiselect(col, options, key=f"fillrate_filter_{col}")
            if picked:
                active_filters[col] = picked

filtered = df.copy()
for col, vals in active_filters.items():
    filtered = filtered[filtered[col].astype(str).isin(vals)]

if filtered.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# ------------------------------------------------------------
# OVERALL TOTAL FILL RATE — sum of every Order Qty / sum of every
# Invoice Qty across the (filtered) data, not an average of each
# shop's or chain's individual fill rate. Rendered into the slot
# reserved right after the page caption, so it sits above everything
# else and always reflects whatever filters are active.
# ------------------------------------------------------------
total_order_qty = pd.to_numeric(filtered[oqty_col], errors="coerce").sum()
total_invoice_qty = pd.to_numeric(filtered[iqty_col], errors="coerce").sum()
overall_fill_rate = (total_invoice_qty / total_order_qty * 100) if total_order_qty else None

with total_metrics_slot.container():
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Order Qty", f"{total_order_qty:,.0f}")
    m2.metric("Total Invoice Qty", f"{total_invoice_qty:,.0f}")
    m3.metric(
        "Overall Fill Rate",
        "—" if overall_fill_rate is None else f"{overall_fill_rate:.1f}%",
    )

# Now that filters are known, build and draw the chart into the slot
# reserved above the Filters section.
chain_agg = (
    filtered.groupby(chain_col, dropna=False)
    .agg(order_qty=(oqty_col, "sum"), invoice_qty=(iqty_col, "sum"))
    .reset_index()
)
chain_agg["fill_rate"] = _fill_rate(chain_agg["invoice_qty"], chain_agg["order_qty"])
chain_agg = chain_agg.sort_values("fill_rate", ascending=DEFAULT_SORT_ASC)

bars = alt.Chart(chain_agg).mark_bar(color="#4C6FFF", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    x=alt.X(
        f"{chain_col}:N", sort=None, title="Chain",
        axis=alt.Axis(labelAngle=-40, labelAlign="right", labelPadding=6),
    ),
    y=alt.Y("fill_rate:Q", title="Fill Rate (%)"),
    tooltip=[
        alt.Tooltip(f"{chain_col}:N", title="Chain"),
        alt.Tooltip("order_qty:Q", title="Order Qty", format=",.0f"),
        alt.Tooltip("invoice_qty:Q", title="Invoice Qty", format=",.0f"),
        alt.Tooltip("fill_rate:Q", title="Fill Rate %", format=".1f"),
    ],
).properties(height=380)

labels = bars.mark_text(dy=-8, color="#1F2937").encode(text=alt.Text("fill_rate:Q", format=".1f"))

chart_slot.altair_chart(bars + labels, use_container_width=True)

# ------------------------------------------------------------
# SHOP SUMMARY TABLE
# ------------------------------------------------------------
st.markdown("### Shops")

agg_kwargs = {"order_qty": (oqty_col, "sum"), "invoice_qty": (iqty_col, "sum")}
if has_order_id:
    agg_kwargs["order_count"] = (oid_col, "nunique")
if has_invoice_no:
    agg_kwargs["invoice_count"] = (inv_col, "nunique")
if has_sale_loss:
    agg_kwargs["sale_loss"] = (sloss_col, "sum")
if has_tat:
    agg_kwargs["tat_avg"] = (tat_col, "mean")

shop_agg = filtered.groupby(shop_col, dropna=False).agg(**agg_kwargs).reset_index()
shop_agg["fill_rate"] = _fill_rate(shop_agg["invoice_qty"], shop_agg["order_qty"])

# Columns to show — same pattern as the Order Tracking page's picker,
# scoped to this table's fixed set of metric columns (shop name is
# always shown, since it's the clickable row key).
metric_options = ["Order Qty", "Invoice Qty", "Fill Rate"]
if has_order_id:
    metric_options.insert(0, "Order Id (count)")
if has_invoice_no:
    metric_options.insert(1 if has_order_id else 0, "InvoiceNumber (count)")
if has_sale_loss:
    metric_options.append("Sale Loss (In Lacs)")
if has_tat:
    metric_options.append("TAT (avg)")

with st.expander("Columns to show", expanded=False):
    visible_metrics = st.multiselect(
        "Columns to show", metric_options, default=metric_options,
        key="fillrate_visible_cols", label_visibility="collapsed",
    )
if not visible_metrics:
    visible_metrics = metric_options

# Maps each display label to the underlying shop_agg column used for
# both sorting and rendering.
SORT_KEY_MAP = {
    "Order Id (count)": "order_count",
    "InvoiceNumber (count)": "invoice_count",
    "Order Qty": "order_qty",
    "Invoice Qty": "invoice_qty",
    "Fill Rate": "fill_rate",
    "Sale Loss (In Lacs)": "sale_loss",
    "TAT (avg)": "tat_avg",
}

shop_search = st.text_input("🔍 Search shop name", key="fillrate_shop_search")
shop_view = shop_agg
if shop_search:
    shop_view = shop_view[shop_view[shop_col].astype(str).str.contains(shop_search, case=False, na=False)]

st.caption(f"{len(shop_view):,} of {len(shop_agg):,} shops")


@st.dialog("Shop Order Details", width="large")
def show_shop_details(shop_name):
    rows = filtered[filtered[shop_col].astype(str) == str(shop_name)].copy()
    if rows.empty:
        st.warning("No matching order rows found.")
        return
    rows["Fill Rate"] = _fill_rate(rows[iqty_col], rows[oqty_col])

    # TAT stays at the very end of the row — whatever header this
    # column has in the source sheet is what will display, since we
    # don't relabel it below.
    pref_cols = [
        CONFIG["wh_receiving_date_column"], shop_col,
        CONFIG["db_code_column"], CONFIG["category_column"], oid_col,
        CONFIG["invoice_date_column"], inv_col, oqty_col, iqty_col,
        "Fill Rate", sloss_col, CONFIG["delivery_date_column"],
        CONFIG["actual_delivery_days_column"], CONFIG["variance_column"],
        tat_col,
    ]
    cols_present = [c for c in pref_cols if c == "Fill Rate" or c in rows.columns]

    st.caption(f"{len(rows):,} order rows for **{shop_name}**")

    sort_col = CONFIG["wh_receiving_date_column"] if CONFIG["wh_receiving_date_column"] in rows.columns else cols_present[0]
    display = rows[cols_present].sort_values(by=sort_col, ascending=False)

    column_config = {}
    for c in cols_present:
        if c == "Fill Rate":
            column_config[c] = st.column_config.NumberColumn(c, format="%.1f%%")
        elif c == sloss_col:
            column_config[c] = st.column_config.NumberColumn("Sale Loss (In Lacs)", format="₹ %.2f")
        elif c == tat_col:
            column_config[c] = st.column_config.NumberColumn(format="%.1f")
        elif _looks_like(c, DATE_COL_HINTS):
            column_config[c] = st.column_config.DateColumn(c, format="DD-MM-YYYY")
        elif _looks_like(c, CURRENCY_COL_HINTS):
            column_config[c] = st.column_config.NumberColumn(c, format="₹ %.2f")

    st.dataframe(display, use_container_width=True, hide_index=True, height=460, column_config=column_config)


# ------------------------------------------------------------
# SORT — click a column header itself to sort by it (no separate
# selectbox anymore). Each header cycles through 3 states on
# repeated clicks, in this order: Ascending -> Descending -> Normal
# (back to the default, unsorted view).
# ------------------------------------------------------------
if "fillrate_sort_col" not in st.session_state:
    st.session_state["fillrate_sort_col"] = None       # "__shop__" or a SORT_KEY_MAP value
    st.session_state["fillrate_sort_dir"] = None        # "asc" | "desc" | None


def _cycle_sort(col_key: str):
    cur_col = st.session_state["fillrate_sort_col"]
    cur_dir = st.session_state["fillrate_sort_dir"]
    if cur_col != col_key:
        st.session_state["fillrate_sort_col"] = col_key
        st.session_state["fillrate_sort_dir"] = "asc"
    elif cur_dir == "asc":
        st.session_state["fillrate_sort_dir"] = "desc"
    else:  # was "desc" -> third click resets to Normal
        st.session_state["fillrate_sort_col"] = None
        st.session_state["fillrate_sort_dir"] = None


def _arrow_for(col_key: str) -> str:
    if st.session_state["fillrate_sort_col"] != col_key:
        return ""
    return " ▲" if st.session_state["fillrate_sort_dir"] == "asc" else " ▼"


header_widths = [3] + [1] * len(visible_metrics)

# Everything from here to the closing </div> renders inside the
# bordered grid box (outer border + row/column divider lines).
st.markdown('<div class="fillrate-grid">', unsafe_allow_html=True)

header_cols = st.columns(header_widths)
if header_cols[0].button(f"{shop_col}{_arrow_for('__shop__')}", key="fillrate_header___shop__", use_container_width=True):
    _cycle_sort("__shop__")
for hc, label in zip(header_cols[1:], visible_metrics):
    key = SORT_KEY_MAP[label]
    if hc.button(f"{label}{_arrow_for(key)}", key=f"fillrate_header_{key}", use_container_width=True):
        _cycle_sort(key)

# Apply whatever sort state the header click above (or a prior run)
# left us with. "Normal" (col=None) leaves shop_view in its default
# groupby order.
active_col = st.session_state["fillrate_sort_col"]
active_dir = st.session_state["fillrate_sort_dir"]
if active_col:
    sort_col = shop_col if active_col == "__shop__" else active_col
    shop_view = shop_view.sort_values(sort_col, ascending=(active_dir == "asc"), na_position="last")

for row_idx, row in shop_view.reset_index(drop=True).iterrows():
    row_cols = st.columns(header_widths)
    if row_cols[0].button(str(row[shop_col]), key=f"shop_btn_{row_idx}_{row[shop_col]}", use_container_width=True):
        show_shop_details(row[shop_col])
    for rc, label in zip(row_cols[1:], visible_metrics):
        if label == "Order Id (count)":
            _right(rc, f"{int(row['order_count']):,}")
        elif label == "InvoiceNumber (count)":
            _right(rc, f"{int(row['invoice_count']):,}")
        elif label == "Order Qty":
            _right(rc, f"{row['order_qty']:,.0f}")
        elif label == "Invoice Qty":
            _right(rc, f"{row['invoice_qty']:,.0f}")
        elif label == "Fill Rate":
            val = row["fill_rate"]
            _right(rc, "—" if pd.isna(val) else f"{val:.1f}%")
        elif label == "Sale Loss (In Lacs)":
            val = row.get("sale_loss")
            _right(rc, "—" if val is None or pd.isna(val) else f"₹ {val:,.2f}")
        elif label == "TAT (avg)":
            val = row.get("tat_avg")
            _right(rc, "—" if val is None or pd.isna(val) else f"{val:.1f}")

st.markdown('</div>', unsafe_allow_html=True)
