import io
import re
from datetime import datetime

import requests
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="MOM Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# THEME / CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------- GLOBAL ---------- */

    .stApp {
        background: #0B0F14;
        color: #F3F4F6;
    }

    section[data-testid="stSidebar"] {
        background: #080B10;
        border-right: 1px solid #20252D;
    }

    section[data-testid="stSidebar"] * {
        color: #E5E7EB;
    }

    h1, h2, h3 {
        color: #F9FAFB !important;
    }

    p, label, span {
        color: #D1D5DB;
    }


    /* ---------- METRIC CARDS ---------- */

    div[data-testid="stMetric"] {
        background: #11161D;
        border: 1px solid #252B34;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,.18);
    }

    div[data-testid="stMetricLabel"] {
        color: #9CA3AF !important;
    }

    div[data-testid="stMetricValue"] {
        color: #F9FAFB !important;
    }

    div[data-testid="stMetricDelta"] {
        color: #D1D5DB !important;
    }


    /* ---------- CONTAINERS ---------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #11161D;
        border: 1px solid #252B34;
        border-radius: 14px;
    }


    /* ---------- BUTTONS ---------- */

    .stButton > button {
        border-radius: 8px;
        border: 1px solid #303743;
        background: #151B23;
        color: #F3F4F6;
        font-weight: 600;
    }

    .stButton > button:hover {
        border-color: #6366F1;
        color: #FFFFFF;
    }


    /* ---------- TABLE ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid #252B34;
        border-radius: 10px;
        overflow: hidden;
    }


    /* ---------- TABS ---------- */

    button[data-baseweb="tab"] {
        color: #9CA3AF;
        font-weight: 600;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF;
    }


    /* ---------- EXPANDER ---------- */

    details {
        background: #11161D;
        border: 1px solid #252B34;
        border-radius: 10px;
    }


    /* ---------- INFO ---------- */

    .dashboard-subtitle {
        color: #9CA3AF;
        font-size: 14px;
        margin-top: -10px;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #F9FAFB;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .small-muted {
        color: #6B7280;
        font-size: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIG
# ============================================================

CONFIG = {

    # Excel source
    "sharepoint_secret": "SHAREPOINT_ORDER_ITEMS_URL",

    # Main dimensions
    "chain": "Gen. Bus. Posting Group",
    "customer": "Customer Name",
    "location": "Location Code",
    "customer_no": "Sell-to Customer No.",
    "sku": "No.",
    "gtin": "GTIN",
    "description": "Description",

    # Order identifiers
    "order_key": "Order SKU Key",
    "document_no": "Document No.",

    # Quantities
    "order_qty": "Order Qty",
    "invoice_qty": "Invoice Qty",
    "balance_qty": "Balance Qty",

    # Values
    "order_value": "Order Amt. Exc. GST",
    "invoice_value": "Invoice Amt. Exc. GST",
    "balance_value": "Balance Amt",

    # Invoice
    "invoice_no": "Invoice No.",
    "invoice_status": "Invoice Status",

    # Dates
    "order_date": "Order Date",
    "invoice_date": "Invoice Date",

    # Inventory
    "amd_inventory": "AMD WH Inventory",
    "blr_inventory": "DS_BLR Inv",
    "nh_inventory": "NH WH Inv",
}


# ============================================================
# MONTH ORDER
# ============================================================

MONTH_ORDER = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_column_name(value):
    return str(value).strip()


def clean_numeric(series):
    """
    Converts Excel numeric-looking columns to numeric.
    Handles commas, currency symbols, blanks, etc.
    """
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace(
            {
                "": np.nan,
                "nan": np.nan,
                "None": np.nan,
                "NaN": np.nan,
            }
        ),
        errors="coerce",
    )


def format_number(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def format_value(value):
    if value is None or pd.isna(value):
        return "—"

    abs_value = abs(value)

    if abs_value >= 10_000_000:
        return f"₹ {value / 10_000_000:.2f} Cr"

    if abs_value >= 100_000:
        return f"₹ {value / 100_000:.2f} L"

    return f"₹ {value:,.0f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "—"

    return f"{value:.1f}%"


def safe_pct(numerator, denominator):
    if denominator == 0 or pd.isna(denominator):
        return np.nan

    return numerator / denominator * 100


def mom_delta(current, previous):
    if previous is None or pd.isna(previous):
        return np.nan

    return current - previous


def resolve_column(target, columns):
    """
    Case/space tolerant column resolver.
    """

    if target in columns:
        return target

    target_key = str(target).strip().lower()

    for col in columns:
        if str(col).strip().lower() == target_key:
            return col

    return None


def clean_sheet_name(sheet_name):
    return str(sheet_name).strip()


def month_sort_key(month):
    try:
        return MONTH_ORDER.index(month)
    except ValueError:
        return 999


# ============================================================
# LOAD EXCEL
# ============================================================

def get_download_url(url):

    if not url:
        return url

    if "download=1" in url.lower():
        return url

    separator = "&" if "?" in url else "?"

    return f"{url}{separator}download=1"


@st.cache_data(
    ttl=300,
    show_spinner="Loading monthly Excel data..."
)
def load_workbook(url):

    download_url = get_download_url(url)

    response = requests.get(
        download_url,
        timeout=60,
        allow_redirects=True,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    if "html" in content_type.lower():

        raise ValueError(
            "SharePoint returned a login/HTML page instead of "
            "the Excel workbook. Check the SharePoint sharing "
            "permission and make sure the link can download the file."
        )

    workbook = pd.read_excel(
        io.BytesIO(response.content),
        sheet_name=None,
        engine="openpyxl",
    )

    return workbook


# ============================================================
# COMBINE MONTHLY SHEETS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner="Preparing MOM dataset..."
)
def prepare_data(url):

    workbook = load_workbook(url)

    frames = []

    for sheet_name, sheet_df in workbook.items():

        sheet_name = clean_sheet_name(sheet_name)

        # Only process sheets that look like month names.
        if sheet_name not in MONTH_ORDER:
            continue

        df = sheet_df.copy()

        if df.empty:
            continue

        df.columns = [
            normalize_column_name(c)
            for c in df.columns
        ]

        # Add month from sheet
        df["Month"] = sheet_name

        # Numeric columns
        numeric_columns = [
            CONFIG["order_qty"],
            CONFIG["invoice_qty"],
            CONFIG["balance_qty"],
            CONFIG["order_value"],
            CONFIG["invoice_value"],
            CONFIG["balance_value"],
            CONFIG["amd_inventory"],
            CONFIG["blr_inventory"],
            CONFIG["nh_inventory"],
        ]

        for col in numeric_columns:

            actual = resolve_column(
                col,
                df.columns,
            )

            if actual is not None:
                df[actual] = clean_numeric(
                    df[actual]
                )

        # Dates
        date_columns = [
            CONFIG["order_date"],
            CONFIG["invoice_date"],
        ]

        for col in date_columns:

            actual = resolve_column(
                col,
                df.columns,
            )

            if actual is not None:

                df[actual] = pd.to_datetime(
                    df[actual],
                    errors="coerce",
                    dayfirst=True,
                )

        frames.append(df)

    if not frames:
        raise ValueError(
            "No monthly sheets were found. "
            "Expected sheets such as Apr, May, Jun, Jul, Aug."
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
    )

    # Sort month correctly
    combined["_month_sort"] = combined["Month"].apply(
        month_sort_key
    )

    combined = combined.sort_values(
        "_month_sort"
    ).drop(
        columns=["_month_sort"]
    )

    # --------------------------------------------------------
    # DERIVED METRICS
    # --------------------------------------------------------

    order_qty = clean_numeric(
        combined[CONFIG["order_qty"]]
    )

    invoice_qty = clean_numeric(
        combined[CONFIG["invoice_qty"]]
    )

    balance_qty = clean_numeric(
        combined[CONFIG["balance_qty"]]
    )

    order_value = clean_numeric(
        combined[CONFIG["order_value"]]
    )

    invoice_value = clean_numeric(
        combined[CONFIG["invoice_value"]]
    )

    balance_value = clean_numeric(
        combined[CONFIG["balance_value"]]
    )

    combined["Fill Rate"] = np.where(
        order_qty > 0,
        invoice_qty / order_qty * 100,
        np.nan,
    )

    combined["Value Fulfilment"] = np.where(
        order_value > 0,
        invoice_value / order_value * 100,
        np.nan,
    )

    # Pending % based on quantity
    combined["Pending %"] = np.where(
        order_qty > 0,
        balance_qty / order_qty * 100,
        np.nan,
    )

    # Inventory total
    combined["Total WH Inventory"] = (
        clean_numeric(combined[CONFIG["amd_inventory"]]).fillna(0)
        + clean_numeric(combined[CONFIG["blr_inventory"]]).fillna(0)
        + clean_numeric(combined[CONFIG["nh_inventory"]]).fillna(0)
    )

    return combined


# ============================================================
# AGGREGATION
# ============================================================

def aggregate_metrics(df, group_columns):

    result = (
        df.groupby(
            group_columns,
            dropna=False,
        )
        .agg(
            order_qty=(
                CONFIG["order_qty"],
                "sum",
            ),

            invoice_qty=(
                CONFIG["invoice_qty"],
                "sum",
            ),

            balance_qty=(
                CONFIG["balance_qty"],
                "sum",
            ),

            order_value=(
                CONFIG["order_value"],
                "sum",
            ),

            invoice_value=(
                CONFIG["invoice_value"],
                "sum",
            ),

            balance_value=(
                CONFIG["balance_value"],
                "sum",
            ),

            order_count=(
                CONFIG["document_no"],
                "nunique",
            ),

            invoice_count=(
                CONFIG["invoice_no"],
                lambda x: x.dropna().astype(str).nunique(),
            ),

            sku_count=(
                CONFIG["sku"],
                "nunique",
            ),

            customer_count=(
                CONFIG["customer"],
                "nunique",
            ),

        )
        .reset_index()
    )

    result["fill_rate"] = np.where(
        result["order_qty"] > 0,
        result["invoice_qty"]
        / result["order_qty"]
        * 100,
        np.nan,
    )

    result["value_fulfilment"] = np.where(
        result["order_value"] > 0,
        result["invoice_value"]
        / result["order_value"]
        * 100,
        np.nan,
    )

    result["pending_pct"] = np.where(
        result["order_qty"] > 0,
        result["balance_qty"]
        / result["order_qty"]
        * 100,
        np.nan,
    )

    return result


# ============================================================
# KPI CARD
# ============================================================

def show_kpi_row(df):

    order_qty = df[CONFIG["order_qty"]].sum()
    invoice_qty = df[CONFIG["invoice_qty"]].sum()
    balance_qty = df[CONFIG["balance_qty"]].sum()

    order_value = df[CONFIG["order_value"]].sum()
    invoice_value = df[CONFIG["invoice_value"]].sum()
    balance_value = df[CONFIG["balance_value"]].sum()

    fill_rate = safe_pct(
        invoice_qty,
        order_qty,
    )

    value_fulfilment = safe_pct(
        invoice_value,
        order_value,
    )

    pending_pct = safe_pct(
        balance_qty,
        order_qty,
    )

    orders = df[CONFIG["document_no"]].nunique()

    customers = df[CONFIG["customer"]].nunique()

    skus = df[CONFIG["sku"]].nunique()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Order Qty",
        format_number(order_qty),
    )

    c2.metric(
        "Invoice Qty",
        format_number(invoice_qty),
    )

    c3.metric(
        "Fill Rate",
        format_percent(fill_rate),
    )

    c4.metric(
        "Pending Qty",
        format_number(balance_qty),
    )

    c5, c6, c7, c8 = st.columns(4)

    c5.metric(
        "Order Value",
        format_value(order_value),
    )

    c6.metric(
        "Invoice Value",
        format_value(invoice_value),
    )

    c7.metric(
        "Value Fulfilment",
        format_percent(value_fulfilment),
    )

    c8.metric(
        "Balance Value",
        format_value(balance_value),
    )

    c9, c10, c11 = st.columns(3)

    c9.metric(
        "Orders",
        format_number(orders),
    )

    c10.metric(
        "Customers",
        format_number(customers),
    )

    c11.metric(
        "SKUs",
        format_number(skus),
    )


# ============================================================
# MOM TREND DATA
# ============================================================

def create_mom_summary(df):

    grouped = aggregate_metrics(
        df,
        ["Month"],
    )

    grouped["_sort"] = grouped["Month"].apply(
        month_sort_key
    )

    grouped = grouped.sort_values(
        "_sort"
    ).drop(
        columns=["_sort"]
    )

    return grouped


# ============================================================
# MAIN
# ============================================================

st.title("📊 MOM Operations Dashboard")

st.markdown(
    """
    <div class="dashboard-subtitle">
        Month-on-Month Order, Invoice, Fill Rate, Balance,
        Customer, SKU and Warehouse Performance
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SHAREPOINT URL
# ============================================================

sharepoint_url = st.secrets.get(
    CONFIG["sharepoint_secret"],
    "",
)

if not sharepoint_url:

    st.error(
        "SharePoint Excel URL is not configured."
    )

    st.info(
        "Add SHAREPOINT_EXCEL_URL to Streamlit Secrets."
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🎛 Dashboard Filters")

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True,
    ):

        load_workbook.clear()
        prepare_data.clear()

        st.rerun()


# ============================================================
# LOAD DATA
# ============================================================

try:

    df = prepare_data(
        sharepoint_url
    )

except Exception as e:

    st.error(
        f"Unable to load the Excel workbook: {e}"
    )

    st.stop()


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

required_columns = [

    CONFIG["chain"],
    CONFIG["customer"],
    CONFIG["document_no"],
    CONFIG["sku"],

    CONFIG["order_qty"],
    CONFIG["invoice_qty"],
    CONFIG["balance_qty"],

    CONFIG["order_value"],
    CONFIG["invoice_value"],
    CONFIG["balance_value"],

    CONFIG["invoice_no"],

]


missing_columns = [
    c
    for c in required_columns
    if resolve_column(c, df.columns) is None
]


if missing_columns:

    st.error(
        "Required columns are missing: "
        + ", ".join(missing_columns)
    )

    st.stop()


# ============================================================
# AVAILABLE MONTHS
# ============================================================

available_months = sorted(
    df["Month"].dropna().unique(),
    key=month_sort_key,
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

with st.sidebar:

    selected_months = st.multiselect(
        "Month",
        options=available_months,
        default=available_months,
    )

    chain_options = sorted(
        df[CONFIG["chain"]]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_chains = st.multiselect(
        "Business Group",
        options=chain_options,
    )

    customer_options = sorted(
        df[CONFIG["customer"]]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_customers = st.multiselect(
        "Customer",
        options=customer_options,
    )

    location_options = sorted(
        df[CONFIG["location"]]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_locations = st.multiselect(
        "Location",
        options=location_options,
    )

    status_options = sorted(
        df[CONFIG["invoice_status"]]
        .dropna()
        .astype(str)
        .unique()
    )

    selected_status = st.multiselect(
        "Invoice Status",
        options=status_options,
    )

    st.markdown("---")

    st.caption(
        f"Rows loaded: {len(df):,}"
    )

    st.caption(
        f"Sheets detected: {', '.join(available_months)}"
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = df.copy()


if selected_months:

    filtered = filtered[
        filtered["Month"].isin(
            selected_months
        )
    ]


if selected_chains:

    filtered = filtered[
        filtered[CONFIG["chain"]]
        .astype(str)
        .isin(selected_chains)
    ]


if selected_customers:

    filtered = filtered[
        filtered[CONFIG["customer"]]
        .astype(str)
        .isin(selected_customers)
    ]


if selected_locations:

    filtered = filtered[
        filtered[CONFIG["location"]]
        .astype(str)
        .isin(selected_locations)
    ]


if selected_status:

    filtered = filtered[
        filtered[CONFIG["invoice_status"]]
        .astype(str)
        .isin(selected_status)
    ]


if filtered.empty:

    st.warning(
        "No data matches the selected filters."
    )

    st.stop()


# ============================================================
# HEADER INFO
# ============================================================

st.caption(
    f"Showing {len(filtered):,} rows "
    f"from {filtered['Month'].nunique()} month(s)"
)


# ============================================================
# KPI
# ============================================================

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True,
)

show_kpi_row(filtered)


# ============================================================
# MOM TAB
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 MOM Overview",
        "🏢 Business Group",
        "🏪 Customer",
        "📦 SKU / Product",
        "🔎 Detailed Orders",
    ]
)


# ============================================================
# TAB 1 — MOM
# ============================================================

with tab1:

    st.markdown(
        '<div class="section-title">Month-on-Month Trend</div>',
        unsafe_allow_html=True,
    )

    mom = create_mom_summary(
        filtered
    )

    # --------------------------------------------
    # MOM TABLE
    # --------------------------------------------

    display_mom = mom.copy()

    display_mom["Order Qty"] = display_mom[
        "order_qty"
    ].map(lambda x: f"{x:,.0f}")

    display_mom["Invoice Qty"] = display_mom[
        "invoice_qty"
    ].map(lambda x: f"{x:,.0f}")

    display_mom["Balance Qty"] = display_mom[
        "balance_qty"
    ].map(lambda x: f"{x:,.0f}")

    display_mom["Fill Rate"] = display_mom[
        "fill_rate"
    ].map(lambda x: f"{x:.1f}%")

    display_mom["Order Value"] = display_mom[
        "order_value"
    ].map(format_value)

    display_mom["Invoice Value"] = display_mom[
        "invoice_value"
    ].map(format_value)

    display_mom["Balance Value"] = display_mom[
        "balance_value"
    ].map(format_value)

    display_mom["Value Fulfilment"] = display_mom[
        "value_fulfilment"
    ].map(lambda x: f"{x:.1f}%")

    display_mom = display_mom[
        [
            "Month",
            "Order Qty",
            "Invoice Qty",
            "Fill Rate",
            "Balance Qty",
            "Order Value",
            "Invoice Value",
            "Value Fulfilment",
            "Balance Value",
            "order_count",
            "customer_count",
            "sku_count",
        ]
    ].rename(
        columns={
            "order_count": "Orders",
            "customer_count": "Customers",
            "sku_count": "SKUs",
        }
    )

    st.dataframe(
        display_mom,
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------
    # FILL RATE TREND
    # --------------------------------------------

    st.markdown(
        '<div class="section-title">Fill Rate Trend</div>',
        unsafe_allow_html=True,
    )

    chart_fill = mom[
        [
            "Month",
            "fill_rate",
        ]
    ].copy()

    fill_chart = (
        alt.Chart(chart_fill)
        .mark_line(
            point=alt.OverlayMarkDef(
                filled=True,
                size=80,
            ),
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
                title="Month",
            ),
            y=alt.Y(
                "fill_rate:Q",
                title="Fill Rate (%)",
                scale=alt.Scale(
                    zero=False
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "Month:N",
                    title="Month",
                ),
                alt.Tooltip(
                    "fill_rate:Q",
                    title="Fill Rate",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=350
        )
    )

    st.altair_chart(
        fill_chart,
        use_container_width=True,
    )


    # --------------------------------------------
    # VALUE TREND
    # --------------------------------------------

    st.markdown(
        '<div class="section-title">Order vs Invoice Value</div>',
        unsafe_allow_html=True,
    )

    value_chart_data = mom[
        [
            "Month",
            "order_value",
            "invoice_value",
        ]
    ].copy()

    value_long = value_chart_data.melt(
        id_vars=["Month"],
        value_vars=[
            "order_value",
            "invoice_value",
        ],
        var_name="Metric",
        value_name="Value",
    )

    value_long["Metric"] = value_long[
        "Metric"
    ].replace(
        {
            "order_value": "Order Value",
            "invoice_value": "Invoice Value",
        }
    )

    value_chart = (
        alt.Chart(value_long)
        .mark_line(
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
                title="Month",
            ),
            y=alt.Y(
                "Value:Q",
                title="Value",
            ),
            color=alt.Color(
                "Metric:N",
                title="Metric",
            ),
            tooltip=[
                "Month:N",
                "Metric:N",
                alt.Tooltip(
                    "Value:Q",
                    format=",.0f",
                ),
            ],
        )
        .properties(
            height=350
        )
    )

    st.altair_chart(
        value_chart,
        use_container_width=True,
    )


# ============================================================
# TAB 2 — BUSINESS GROUP
# ============================================================

with tab2:

    st.markdown(
        '<div class="section-title">Business Group Analysis</div>',
        unsafe_allow_html=True,
    )

    chain_month = aggregate_metrics(
        filtered,
        [
            "Month",
            CONFIG["chain"],
        ],
    )

    chain_month["_sort"] = chain_month[
        "Month"
    ].apply(month_sort_key)

    chain_month = chain_month.sort_values(
        "_sort"
    ).drop(
        columns="_sort"
    )


    # --------------------------------------------
    # CHAIN FILL RATE
    # --------------------------------------------

    st.markdown("#### Fill Rate by Business Group")

    chain_fill_chart = (
        alt.Chart(chain_month)
        .mark_line(
            point=True,
            strokeWidth=2.5,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
                title="Month",
            ),
            y=alt.Y(
                "fill_rate:Q",
                title="Fill Rate %",
                scale=alt.Scale(
                    zero=False
                ),
            ),
            color=alt.Color(
                f"{CONFIG['chain']}:N",
                title="Business Group",
            ),
            tooltip=[
                "Month:N",
                f"{CONFIG['chain']}:N",
                alt.Tooltip(
                    "fill_rate:Q",
                    title="Fill Rate",
                    format=".1f",
                ),
                alt.Tooltip(
                    "order_qty:Q",
                    title="Order Qty",
                    format=",.0f",
                ),
                alt.Tooltip(
                    "invoice_qty:Q",
                    title="Invoice Qty",
                    format=",.0f",
                ),
            ],
        )
        .properties(
            height=450
        )
    )

    st.altair_chart(
        chain_fill_chart,
        use_container_width=True,
    )


    # --------------------------------------------
    # CHAIN SUMMARY
    # --------------------------------------------

    latest_month = available_months[-1]

    latest_chain = chain_month[
        chain_month["Month"]
        == latest_month
    ].copy()

    latest_chain = latest_chain.sort_values(
        "fill_rate"
    )

    latest_chain_display = latest_chain[
        [
            CONFIG["chain"],
            "order_qty",
            "invoice_qty",
            "fill_rate",
            "balance_qty",
            "order_value",
            "invoice_value",
            "balance_value",
        ]
    ].copy()

    latest_chain_display["order_qty"] = latest_chain_display[
        "order_qty"
    ].map(lambda x: f"{x:,.0f}")

    latest_chain_display["invoice_qty"] = latest_chain_display[
        "invoice_qty"
    ].map(lambda x: f"{x:,.0f}")

    latest_chain_display["fill_rate"] = latest_chain_display[
        "fill_rate"
    ].map(lambda x: f"{x:.1f}%")

    latest_chain_display["balance_qty"] = latest_chain_display[
        "balance_qty"
    ].map(lambda x: f"{x:,.0f}")

    latest_chain_display["order_value"] = latest_chain_display[
        "order_value"
    ].map(format_value)

    latest_chain_display["invoice_value"] = latest_chain_display[
        "invoice_value"
    ].map(format_value)

    latest_chain_display["balance_value"] = latest_chain_display[
        "balance_value"
    ].map(format_value)

    latest_chain_display.columns = [
        "Business Group",
        "Order Qty",
        "Invoice Qty",
        "Fill Rate",
        "Balance Qty",
        "Order Value",
        "Invoice Value",
        "Balance Value",
    ]

    st.markdown(
        f"#### {latest_month} Business Group Detail"
    )

    st.dataframe(
        latest_chain_display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 3 — CUSTOMER
# ============================================================

with tab3:

    st.markdown(
        '<div class="section-title">Customer Analysis</div>',
        unsafe_allow_html=True,
    )

    customer_summary = aggregate_metrics(
        filtered,
        [
            CONFIG["customer"],
        ],
    )

    customer_summary = customer_summary.sort_values(
        "fill_rate",
        ascending=True,
    )


    # Search
    customer_search = st.text_input(
        "🔍 Search Customer",
        key="customer_search",
    )

    if customer_search:

        customer_summary = customer_summary[
            customer_summary[
                CONFIG["customer"]
            ]
            .astype(str)
            .str.contains(
                customer_search,
                case=False,
                na=False,
            )
        ]


    st.caption(
        f"{len(customer_summary):,} customers"
    )


    # --------------------------------------------
    # CUSTOMER TABLE
    # --------------------------------------------

    customer_display = customer_summary[
        [
            CONFIG["customer"],
            "order_count",
            "order_qty",
            "invoice_qty",
            "fill_rate",
            "balance_qty",
            "order_value",
            "invoice_value",
            "balance_value",
        ]
    ].copy()

    customer_display.columns = [
        "Customer",
        "Orders",
        "Order Qty",
        "Invoice Qty",
        "Fill Rate",
        "Balance Qty",
        "Order Value",
        "Invoice Value",
        "Balance Value",
    ]

    st.dataframe(
        customer_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Order Qty": st.column_config.NumberColumn(
                format="%,.0f"
            ),
            "Invoice Qty": st.column_config.NumberColumn(
                format="%,.0f"
            ),
            "Balance Qty": st.column_config.NumberColumn(
                format="%,.0f"
            ),
            "Fill Rate": st.column_config.NumberColumn(
                format="%.1f"
            ),
            "Order Value": st.column_config.NumberColumn(
                format="₹ %,.0f"
            ),
            "Invoice Value": st.column_config.NumberColumn(
                format="₹ %,.0f"
            ),
            "Balance Value": st.column_config.NumberColumn(
                format="₹ %,.0f"
            ),
        },
    )


# ============================================================
# TAB 4 — SKU / PRODUCT
# ============================================================

with tab4:

    st.markdown(
        '<div class="section-title">SKU / Product Analysis</div>',
        unsafe_allow_html=True,
    )

    sku_summary = aggregate_metrics(
        filtered,
        [
            CONFIG["sku"],
            CONFIG["description"],
        ],
    )

    sku_summary = sku_summary.sort_values(
        "balance_qty",
        ascending=False,
    )


    sku_search = st.text_input(
        "🔍 Search SKU / Product",
        key="sku_search",
    )


    if sku_search:

        mask = (
            sku_summary[
                CONFIG["sku"]
            ]
            .astype(str)
            .str.contains(
                sku_search,
                case=False,
                na=False,
            )
            |
            sku_summary[
                CONFIG["description"]
            ]
            .astype(str)
            .str.contains(
                sku_search,
                case=False,
                na=False,
            )
        )

        sku_summary = sku_summary[
            mask
        ]


    st.caption(
        f"{len(sku_summary):,} SKUs"
    )


    sku_display = sku_summary[
        [
            CONFIG["sku"],
            CONFIG["description"],
            "order_qty",
            "invoice_qty",
            "fill_rate",
            "balance_qty",
            "order_value",
            "invoice_value",
            "balance_value",
        ]
    ].copy()

    sku_display.columns = [
        "SKU",
        "Description",
        "Order Qty",
        "Invoice Qty",
        "Fill Rate",
        "Balance Qty",
        "Order Value",
        "Invoice Value",
        "Balance Value",
    ]

    st.dataframe(
        sku_display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 5 — DETAILED ORDERS
# ============================================================

with tab5:

    st.markdown(
        '<div class="section-title">Detailed Order / SKU View</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "This view retains the operational-level detail from the monthly sheets."
    )


    # --------------------------------------------
    # SEARCH
    # --------------------------------------------

    detail_search = st.text_input(
        "🔍 Search Document No. / Customer / SKU / Description / Invoice No.",
        key="detail_search",
    )


    detail_df = filtered.copy()


    if detail_search:

        search = str(
            detail_search
        ).lower()

        searchable_columns = [
            CONFIG["document_no"],
            CONFIG["customer"],
            CONFIG["sku"],
            CONFIG["description"],
            CONFIG["invoice_no"],
            CONFIG["order_key"],
        ]

        mask = pd.Series(
            False,
            index=detail_df.index,
        )

        for col in searchable_columns:

            if col in detail_df.columns:

                mask = mask | (
                    detail_df[col]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        search,
                        na=False,
                    )
                )

        detail_df = detail_df[
            mask
        ]


    st.caption(
        f"{len(detail_df):,} detail rows"
    )


    # --------------------------------------------
    # SELECT COLUMNS
    # --------------------------------------------

    detail_columns = [

        "Month",

        CONFIG["order_key"],
        CONFIG["order_date"],
        CONFIG["location"],
        CONFIG["document_no"],

        CONFIG["chain"],
        CONFIG["customer"],
        CONFIG["customer_no"],

        CONFIG["sku"],
        CONFIG["gtin"],
        CONFIG["description"],

        CONFIG["order_qty"],
        CONFIG["order_value"],

        CONFIG["invoice_qty"],
        CONFIG["invoice_value"],

        CONFIG["invoice_no"],
        CONFIG["invoice_status"],

        CONFIG["balance_qty"],
        CONFIG["balance_value"],

        CONFIG["invoice_date"],

        CONFIG["amd_inventory"],
        CONFIG["blr_inventory"],
        CONFIG["nh_inventory"],

        "Fill Rate",
        "Value Fulfilment",
        "Pending %",
        "Total WH Inventory",
    ]


    available_detail_columns = [
        c
        for c in detail_columns
        if c in detail_df.columns
    ]


    detail_display = detail_df[
        available_detail_columns
    ].copy()


    # Format dates
    for col in [
        CONFIG["order_date"],
        CONFIG["invoice_date"],
    ]:

        if col in detail_display.columns:

            detail_display[col] = (
                pd.to_datetime(
                    detail_display[col],
                    errors="coerce",
                )
                .dt.strftime(
                    "%d-%m-%Y"
                )
            )


    # Download
    csv_data = detail_display.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )


    st.download_button(
        "⬇️ Download Filtered Details",
        data=csv_data,
        file_name="MOM_Filtered_Details.csv",
        mime="text/csv",
        use_container_width=False,
    )


    st.dataframe(
        detail_display,
        use_container_width=True,
        hide_index=True,
        height=650,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    f"""
    <div class="small-muted">
        Data source: SharePoint Excel &nbsp;|&nbsp;
        Monthly sheets detected: {", ".join(available_months)}
        &nbsp;|&nbsp;
        Last application load: {datetime.now().strftime("%d-%m-%Y %H:%M")}
    </div>
    """,
    unsafe_allow_html=True,
)
