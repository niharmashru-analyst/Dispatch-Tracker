import io
from datetime import datetime

import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Fill Rate",
    layout="wide",
    page_icon="📶",
)


# ============================================================
# CONFIG
# ============================================================

CONFIG = {
    # Keep your existing secret name
    "sharepoint_secret": "SHAREPOINT_EXCEL_URL",

    # Existing source columns
    "order_received_date": "Order Received Date",
    "order_upload_date": "Order Upload date",
    "wh_receiving_date": "Wh Receiving Date",
    "month": "Month",
    "channel": "Channel",
    "zone": "Zone",
    "db_code": "DB Code",
    "customer": "Customer Name",
    "order_category": "Order Category",
    "category": "Category",
    "order_id": "Order Id",
    "external_document": "External Document No.",

    "order_qty": "Order Qty",
    "order_value": "Order Value",

    "wh_remarks": "Wh. Remarks",
    "order_punch_time": "Order Punch time",

    "invoice_date": "Invoice Date",
    "invoice_qty": "Invoice Qty",
    "invoice_value": "Invoice Value",
    "invoice_number": "InvoiceNumber",
    "invoice_time": "Invoice Time",

    "fr_value": "Over all FR % (Value)",
    "fr_qty": "Over all FR % (Qty)",

    "dispatch_date": "Dispatch Date",
    "awb": "AWB NUMBER",
    "courier": "COURIER",
    "mode": "Mode",
    "box": "Box",
    "weight": "Weight",
    "pin_code": "Pin Code",

    "delivery_status": "Delivery Status",
    "delivery_date": "Delivery Date",

    "dispatched_sla": "Dispatched SLA",
    "logistics_sla": "Logistics SLA",

    "wh_remark": "Wh Remark",
    "logistics_remarks": "Logistics Remarks",

    "sro": "SRO Number",
    "ageing": "Agening",
    "standard_tat": "Standard TAT",
    "order_to_wh": "Order to wh",
    "oti": "OTI",
    "otd": "OTD",
    "otde": "OTDE",
    "dispatch_to_delivery": "Dispatch to Deli TAT",
    "otd_bucket": "OTD Bucket",

    "omt_remarks": "OMT REMARKS",
    "type": "Type",
    "name": "Name",
    "ho_remarks": "HO Remarks",
    "final_remarks": "Final Remarks",

    "otw_days": "OTW Days",
    "invoice_days": "Invoice Days",
    "dispatch_days": "Dispatch Days",
    "actual_delivery_days": "Actual Deli. Days",
    "variance": "Vairance",

    "order_value_lacs": "Order Value Lacs",
    "invoice_value_lacs": "Invoice Value Lacs",
    "sale_loss": "Sale Loss",
}


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
# ORIGINAL WHITE THEME
# ============================================================

C_BG = "#F4F6FA"
C_CARD = "#FFFFFF"
C_BORDER = "#E4E7ED"
C_TEXT = "#1F2937"
C_MUTED = "#6B7280"
C_BLUE = "#4C6FFF"


st.markdown(
    f"""
    <style>

    .stApp {{
        background: {C_BG};
    }}

    /* Main headings */
    h1, h2, h3, h4 {{
        color: {C_TEXT} !important;
    }}

    /* Normal text */
    p, label, span {{
        color: {C_TEXT};
    }}

    /* KPI cards */
    div[data-testid="stMetric"] {{
        background: {C_CARD};
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,.07);
    }}

    div[data-testid="stMetricLabel"] {{
        color: {C_MUTED} !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {C_TEXT} !important;
        font-weight: 700;
    }}

    div[data-testid="stMetricDelta"] {{
        font-weight: 600;
    }}

    /* Original style table */
    .st-key-fillrate_table {{
        border: 1px solid {C_BORDER};
        border-radius: 10px;
        overflow: hidden;
        background: #fff;
    }}

    .st-key-fillrate_table [data-testid="stHorizontalBlock"] {{
        border-bottom: 1px solid {C_BORDER};
        padding: 2px 6px;
        align-items: center;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:last-child {{
        border-bottom: none;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]
    > [data-testid="column"]:not(:last-child),
    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]
    > [data-testid="stColumn"]:not(:last-child) {{
        border-right: 1px solid {C_BORDER};
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:first-child {{
        background: #F8F9FC;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:first-child
    div.stButton > button {{
        font-weight: 700;
        color: {C_TEXT};
        background: transparent;
        border: none;
        box-shadow: none;
    }}

    .st-key-fillrate_table
    div.stButton > button {{
        border: none;
        border-radius: 0;
        box-shadow: none;
        white-space: normal;
        background: transparent;
        color: {C_TEXT};
    }}

    .st-key-fillrate_table
    div.stButton > button:hover {{
        color: {C_BLUE};
        background: #F8F9FC;
    }}

    /* Normal buttons */
    div.stButton > button {{
        border-radius: 7px;
        border: 1px solid {C_BORDER};
        background: #FFFFFF;
        color: {C_TEXT};
        font-weight: 600;
    }}

    div.stButton > button:hover {{
        border-color: {C_BLUE};
        color: {C_BLUE};
    }}

    /* Search/input boxes */
    div[data-baseweb="input"] {{
        background: #FFFFFF;
    }}

    /* Section title */
    .section-title {{
        font-size: 20px;
        font-weight: 700;
        color: {C_TEXT};
        margin-top: 20px;
        margin-bottom: 10px;
    }}

    .dashboard-caption {{
        color: {C_MUTED};
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 18px;
    }}

    .executive-header {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,.05);
    }}

    .executive-title {{
        font-size: 21px;
        font-weight: 750;
        color: {C_TEXT};
    }}

    .executive-subtitle {{
        font-size: 13px;
        color: {C_MUTED};
        margin-top: 3px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def resolve_col(target, columns):
    """
    Case / whitespace tolerant matching.
    """
    if target in columns:
        return target

    target_key = str(target).strip().lower()

    for col in columns:
        if str(col).strip().lower() == target_key:
            return col

    return None


def clean_numeric(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip()
        .replace(
            {
                "": np.nan,
                "nan": np.nan,
                "NaN": np.nan,
                "None": np.nan,
                "-": np.nan,
            }
        ),
        errors="coerce",
    )


def month_sort_key(month):
    try:
        return MONTH_ORDER.index(str(month))
    except ValueError:
        return 999


def format_number(value):
    if value is None or pd.isna(value):
        return "—"

    return f"{value:,.0f}"


def format_value(value):
    if value is None or pd.isna(value):
        return "—"

    value = float(value)

    if abs(value) >= 10_000_000:
        return f"₹ {value / 10_000_000:.2f} Cr"

    if abs(value) >= 100_000:
        return f"₹ {value / 100_000:.2f} L"

    return f"₹ {value:,.0f}"


def format_percent(value):
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.1f}%"


def safe_ratio(numerator, denominator):
    if denominator is None:
        return np.nan

    try:
        if denominator == 0:
            return np.nan
    except Exception:
        pass

    return numerator / denominator * 100


def center(container, text):
    container.markdown(
        f"""
        <div style="
            text-align:center;
            white-space:nowrap;
            color:{C_TEXT};
            font-size:14px;
        ">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SHAREPOINT
# ============================================================

def sharepoint_download_url(url):

    if "download=1" in url.lower():
        return url

    separator = "&" if "?" in url else "?"

    return f"{url}{separator}download=1"


@st.cache_data(
    ttl=300,
    show_spinner="Fetching latest data..."
)
def load_workbook(url):

    response = requests.get(
        sharepoint_download_url(url),
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
            "Got a login/redirect page instead of the Excel file. "
            "Please check SharePoint access."
        )

    workbook = pd.read_excel(
        io.BytesIO(response.content),
        sheet_name=None,
        engine="openpyxl",
    )

    return workbook


# ============================================================
# LOAD ALL MONTHLY SHEETS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner="Combining monthly sheets..."
)
def load_data(url):

    workbook = load_workbook(url)

    frames = []
    sheets_used = []

    for sheet_name, raw_df in workbook.items():

        sheet_name = str(sheet_name).strip()

        if sheet_name not in MONTH_ORDER:
            continue

        if raw_df is None or raw_df.empty:
            continue

        df = raw_df.copy()

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        # Sheet name is authoritative for MOM.
        df["__Dashboard_Month"] = sheet_name

        frames.append(df)
        sheets_used.append(sheet_name)

    if not frames:

        raise ValueError(
            "No monthly sheets found. "
            "Expected Apr, May, Jun, Jul, Aug, etc."
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    # --------------------------------------------------------
    # NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
        CONFIG["order_qty"],
        CONFIG["order_value"],
        CONFIG["invoice_qty"],
        CONFIG["invoice_value"],
        CONFIG["fr_value"],
        CONFIG["fr_qty"],
        CONFIG["box"],
        CONFIG["weight"],
        CONFIG["dispatched_sla"],
        CONFIG["logistics_sla"],
        CONFIG["ageing"],
        CONFIG["standard_tat"],
        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],
        CONFIG["dispatch_to_delivery"],
        CONFIG["otw_days"],
        CONFIG["invoice_days"],
        CONFIG["dispatch_days"],
        CONFIG["actual_delivery_days"],
        CONFIG["variance"],
        CONFIG["order_value_lacs"],
        CONFIG["invoice_value_lacs"],
        CONFIG["sale_loss"],
    ]

    for col in numeric_columns:

        actual = resolve_col(
            col,
            combined.columns,
        )

        if actual:

            combined[actual] = clean_numeric(
                combined[actual]
            )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    date_columns = [
        CONFIG["order_received_date"],
        CONFIG["order_upload_date"],
        CONFIG["wh_receiving_date"],
        CONFIG["invoice_date"],
        CONFIG["dispatch_date"],
        CONFIG["delivery_date"],
    ]

    for col in date_columns:

        actual = resolve_col(
            col,
            combined.columns,
        )

        if actual:

            combined[actual] = pd.to_datetime(
                combined[actual],
                errors="coerce",
                dayfirst=True,
            )

    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    combined["Month"] = combined[
        "__Dashboard_Month"
    ]

    combined["__month_sort"] = combined[
        "Month"
    ].apply(month_sort_key)

    combined = combined.sort_values(
        "__month_sort"
    ).reset_index(drop=True)

    return combined, sheets_used


# ============================================================
# OFFICIAL + CALCULATED FR
# ============================================================

def add_derived_metrics(df):

    df = df.copy()

    oq = resolve_col(
        CONFIG["order_qty"],
        df.columns,
    )

    iq = resolve_col(
        CONFIG["invoice_qty"],
        df.columns,
    )

    ov = resolve_col(
        CONFIG["order_value"],
        df.columns,
    )

    iv = resolve_col(
        CONFIG["invoice_value"],
        df.columns,
    )

    # Calculated quantity FR
    if oq and iq:

        df["__Calculated_FR_Qty"] = np.where(
            df[oq] != 0,
            df[iq] / df[oq] * 100,
            np.nan,
        )

    else:

        df["__Calculated_FR_Qty"] = np.nan

    # Calculated value FR
    if ov and iv:

        df["__Calculated_FR_Value"] = np.where(
            df[ov] != 0,
            df[iv] / df[ov] * 100,
            np.nan,
        )

    else:

        df["__Calculated_FR_Value"] = np.nan

    # Official source FR
    fr_qty = resolve_col(
        CONFIG["fr_qty"],
        df.columns,
    )

    fr_value = resolve_col(
        CONFIG["fr_value"],
        df.columns,
    )

    if fr_qty:
        df["__FR_Qty"] = clean_numeric(
            df[fr_qty]
        )
    else:
        df["__FR_Qty"] = df[
            "__Calculated_FR_Qty"
        ]

    if fr_value:
        df["__FR_Value"] = clean_numeric(
            df[fr_value]
        )
    else:
        df["__FR_Value"] = df[
            "__Calculated_FR_Value"
        ]

    # Pending
    if oq and iq:

        df["__Pending_Qty"] = (
            df[oq].fillna(0)
            - df[iq].fillna(0)
        )

    else:

        df["__Pending_Qty"] = np.nan

    if ov and iv:

        df["__Pending_Value"] = (
            df[ov].fillna(0)
            - df[iv].fillna(0)
        )

    else:

        df["__Pending_Value"] = np.nan

    return df


# ============================================================
# AGGREGATION
# ============================================================

def aggregate_month(df):

    oq = resolve_col(
        CONFIG["order_qty"],
        df.columns,
    )

    iq = resolve_col(
        CONFIG["invoice_qty"],
        df.columns,
    )

    ov = resolve_col(
        CONFIG["order_value"],
        df.columns,
    )

    iv = resolve_col(
        CONFIG["invoice_value"],
        df.columns,
    )

    sale = resolve_col(
        CONFIG["sale_loss"],
        df.columns,
    )

    oid = resolve_col(
        CONFIG["order_id"],
        df.columns,
    )

    inv = resolve_col(
        CONFIG["invoice_number"],
        df.columns,
    )

    aggregation = {}

    if oq:
        aggregation["order_qty"] = (
            oq,
            "sum",
        )

    if iq:
        aggregation["invoice_qty"] = (
            iq,
            "sum",
        )

    if ov:
        aggregation["order_value"] = (
            ov,
            "sum",
        )

    if iv:
        aggregation["invoice_value"] = (
            iv,
            "sum",
        )

    if sale:
        aggregation["sale_loss"] = (
            sale,
            "sum",
        )

    if oid:
        aggregation["orders"] = (
            oid,
            "nunique",
        )

    if inv:
        aggregation["invoices"] = (
            inv,
            lambda x:
            x.dropna()
            .astype(str)
            .nunique(),
        )

    result = (
        df.groupby(
            "Month",
            dropna=False,
        )
        .agg(**aggregation)
        .reset_index()
    )

    if "order_qty" in result.columns:

        result["fr_qty"] = np.where(
            result["order_qty"] != 0,
            result["invoice_qty"]
            / result["order_qty"]
            * 100,
            np.nan,
        )

        result["pending_qty"] = (
            result["order_qty"]
            - result["invoice_qty"]
        )

    if "order_value" in result.columns:

        result["fr_value"] = np.where(
            result["order_value"] != 0,
            result["invoice_value"]
            / result["order_value"]
            * 100,
            np.nan,
        )

        result["pending_value"] = (
            result["order_value"]
            - result["invoice_value"]
        )

    result["__sort"] = result[
        "Month"
    ].apply(month_sort_key)

    result = result.sort_values(
        "__sort"
    ).drop(
        columns="__sort"
    )

    return result


# ============================================================
# ORIGINAL CUSTOMER LOGIC
# ============================================================

def build_customer_summary(filtered):

    customer_col = CONFIG["customer"]
    order_id_col = CONFIG["order_id"]
    invoice_col = CONFIG["invoice_number"]
    oq_col = CONFIG["order_qty"]
    iq_col = CONFIG["invoice_qty"]
    sale_col = CONFIG["sale_loss"]
    tat_col = CONFIG["actual_delivery_days"]

    aggregation = {
        "order_qty": (
            oq_col,
            "sum",
        ),
        "invoice_qty": (
            iq_col,
            "sum",
        ),
    }

    if order_id_col in filtered.columns:

        aggregation["order_count"] = (
            order_id_col,
            "nunique",
        )

    if invoice_col in filtered.columns:

        aggregation["invoice_count"] = (
            invoice_col,
            lambda x:
            x.dropna()
            .astype(str)
            .nunique(),
        )

    if sale_col in filtered.columns:

        aggregation["sale_loss"] = (
            sale_col,
            "sum",
        )

    if tat_col in filtered.columns:

        aggregation["tat_avg"] = (
            tat_col,
            "mean",
        )

    summary = (
        filtered
        .groupby(
            customer_col,
            dropna=False,
        )
        .agg(**aggregation)
        .reset_index()
    )

    summary["fill_rate"] = np.where(
        summary["order_qty"] != 0,
        summary["invoice_qty"]
        / summary["order_qty"]
        * 100,
        np.nan,
    )

    return summary


# ============================================================
# ORIGINAL CUSTOMER DETAIL POPUP
# ============================================================

def clear_selected_customer():

    st.session_state[
        "selected_customer"
    ] = None


@st.dialog(
    "Customer Order Details",
    width="large",
    on_dismiss=clear_selected_customer,
)
def show_customer_details(
    customer_name,
    filtered,
):

    customer_col = CONFIG["customer"]

    rows = filtered[
        filtered[customer_col]
        .astype(str)
        == str(customer_name)
    ].copy()

    if rows.empty:

        st.warning(
            "No matching order rows found."
        )

        return

    rows["Fill Rate"] = np.where(
        rows[CONFIG["order_qty"]] != 0,
        rows[CONFIG["invoice_qty"]]
        / rows[CONFIG["order_qty"]]
        * 100,
        np.nan,
    )

    # --------------------------------------------------------
    # Original preferred order
    # --------------------------------------------------------

    pref_cols = [

        CONFIG["wh_receiving_date"],
        customer_col,
        CONFIG["db_code"],
        CONFIG["category"],
        CONFIG["order_id"],
        CONFIG["invoice_date"],
        CONFIG["invoice_number"],
        CONFIG["order_qty"],
        CONFIG["invoice_qty"],

        "Fill Rate",

        CONFIG["sale_loss"],

        CONFIG["dispatch_date"],
        CONFIG["actual_delivery_days"],
        CONFIG["standard_tat"],
        CONFIG["variance"],

        # Extra original operational details
        CONFIG["awb"],
        CONFIG["courier"],
        CONFIG["mode"],
        CONFIG["delivery_status"],
        CONFIG["delivery_date"],
        CONFIG["final_remarks"],
    ]

    cols_present = []

    seen = set()

    for requested in pref_cols:

        if requested == "Fill Rate":

            cols_present.append(
                requested
            )

            continue

        actual = resolve_col(
            requested,
            rows.columns,
        )

        if actual and actual not in seen:

            cols_present.append(
                actual
            )

            seen.add(actual)

    # --------------------------------------------------------
    # Add remaining important operational fields
    # --------------------------------------------------------

    additional_cols = [

        CONFIG["order_received_date"],
        CONFIG["order_upload_date"],
        CONFIG["channel"],
        CONFIG["zone"],
        CONFIG["order_category"],
        CONFIG["external_document"],

        CONFIG["order_value"],
        CONFIG["invoice_value"],

        CONFIG["invoice_time"],
        CONFIG["dispatch_to_delivery"],

        CONFIG["otd_bucket"],
        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],

        CONFIG["otw_days"],
        CONFIG["invoice_days"],
        CONFIG["dispatch_days"],

        CONFIG["sale_loss"],

        CONFIG["wh_remarks"],
        CONFIG["wh_remark"],
        CONFIG["logistics_remarks"],
        CONFIG["ho_remarks"],
        CONFIG["omt_remarks"],
    ]

    for requested in additional_cols:

        actual = resolve_col(
            requested,
            rows.columns,
        )

        if actual and actual not in seen:

            cols_present.append(
                actual
            )

            seen.add(actual)

    st.caption(
        f"{len(rows):,} order rows for **{customer_name}**"
    )

    # --------------------------------------------------------
    # Sort by WH Receiving Date
    # --------------------------------------------------------

    wh_date = resolve_col(
        CONFIG["wh_receiving_date"],
        rows.columns,
    )

    if wh_date:

        display = rows[
            cols_present
        ].sort_values(
            by=wh_date,
            ascending=False,
        )

    else:

        display = rows[
            cols_present
        ]

    # --------------------------------------------------------
    # Column config
    # --------------------------------------------------------

    column_config = {}

    if "Fill Rate" in display.columns:

        column_config[
            "Fill Rate"
        ] = st.column_config.NumberColumn(
            "Fill Rate",
            format="%.1f%%",
        )

    if CONFIG["sale_loss"] in display.columns:

        column_config[
            CONFIG["sale_loss"]
        ] = st.column_config.NumberColumn(
            "Sale Loss",
            format="₹ %.2f",
        )

    numeric_detail_cols = [
        CONFIG["order_qty"],
        CONFIG["invoice_qty"],
        CONFIG["order_value"],
        CONFIG["invoice_value"],
        CONFIG["standard_tat"],
        CONFIG["actual_delivery_days"],
        CONFIG["variance"],
        CONFIG["dispatch_to_delivery"],
        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],
        CONFIG["otw_days"],
        CONFIG["invoice_days"],
        CONFIG["dispatch_days"],
    ]

    for col in numeric_detail_cols:

        if col in display.columns:

            column_config[
                col
            ] = st.column_config.NumberColumn(
                col,
                format="%.1f",
            )

    date_cols = [
        CONFIG["wh_receiving_date"],
        CONFIG["order_received_date"],
        CONFIG["order_upload_date"],
        CONFIG["invoice_date"],
        CONFIG["dispatch_date"],
        CONFIG["delivery_date"],
    ]

    for col in date_cols:

        if col in display.columns:

            column_config[
                col
            ] = st.column_config.DateColumn(
                col,
                format="DD-MM-YYYY",
            )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config=column_config,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="executive-header">
        <div class="executive-title">
            📊 Fill Rate & MOM Performance
        </div>
        <div class="executive-subtitle">
            Month-on-Month performance with customer-level operational drill-down
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SHAREPOINT
# ============================================================

sp_url = st.secrets.get(
    CONFIG["sharepoint_secret"],
    "",
)

if not sp_url:

    st.error(
        "No SharePoint link configured. "
        "Add SHAREPOINT_EXCEL_URL to Streamlit Secrets."
    )

    st.stop()


# ============================================================
# REFRESH
# ============================================================

top_left, top_right = st.columns(
    [6, 1]
)

with top_right:

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        load_workbook.clear()
        load_data.clear()

        st.rerun()


# ============================================================
# LOAD DATA
# ============================================================

try:

    df, loaded_sheets = load_data(
        sp_url
    )

    df = add_derived_metrics(
        df
    )

except Exception as e:

    st.error(
        f"Could not load the live file: {e}"
    )

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_cols = [
    CONFIG["customer"],
    CONFIG["order_qty"],
    CONFIG["invoice_qty"],
    CONFIG["order_id"],
]

missing = [
    c
    for c in required_cols
    if resolve_col(
        c,
        df.columns,
    ) is None
]

if missing:

    st.error(
        "Missing required columns: "
        + ", ".join(missing)
    )

    st.stop()


# ============================================================
# FILTERS
# ============================================================

with st.expander(
    "🔎 Filters",
    expanded=False,
):

    f1, f2, f3 = st.columns(3)

    with f1:

        available_months = sorted(
            loaded_sheets,
            key=month_sort_key,
        )

        selected_months = st.multiselect(
            "Month",
            available_months,
            default=available_months,
        )

    with f2:

        chain_col = CONFIG["name"]

        chain_options = sorted(
            df[chain_col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_names = st.multiselect(
            "Name",
            chain_options,
        )

    with f3:

        category_options = sorted(
            df[CONFIG["category"]]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_categories = st.multiselect(
            "Category",
            category_options,
        )

    f4, f5, f6 = st.columns(3)

    with f4:

        invoice_options = sorted(
            df[CONFIG["invoice_number"]]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_invoices = st.multiselect(
            "InvoiceNumber",
            invoice_options,
        )

    with f5:

        order_options = sorted(
            df[CONFIG["order_id"]]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_orders = st.multiselect(
            "Order Id",
            order_options,
        )

    with f6:

        final_options = sorted(
            df[CONFIG["final_remarks"]]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_final = st.multiselect(
            "Final Remarks",
            final_options,
        )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = df.copy()

if selected_months:

    filtered = filtered[
        filtered["Month"]
        .isin(selected_months)
    ]

if selected_names:

    filtered = filtered[
        filtered[
            CONFIG["name"]
        ]
        .astype(str)
        .isin(selected_names)
    ]

if selected_categories:

    filtered = filtered[
        filtered[
            CONFIG["category"]
        ]
        .astype(str)
        .isin(selected_categories)
    ]

if selected_invoices:

    filtered = filtered[
        filtered[
            CONFIG["invoice_number"]
        ]
        .astype(str)
        .isin(selected_invoices)
    ]

if selected_orders:

    filtered = filtered[
        filtered[
            CONFIG["order_id"]
        ]
        .astype(str)
        .isin(selected_orders)
    ]

if selected_final:

    filtered = filtered[
        filtered[
            CONFIG["final_remarks"]
        ]
        .astype(str)
        .isin(selected_final)
    ]


if filtered.empty:

    st.warning(
        "No rows match the current filters."
    )

    st.stop()


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True,
)

# Determine latest and previous selected month
selected_sorted = sorted(
    filtered["Month"].dropna().unique(),
    key=month_sort_key,
)

latest_month = (
    selected_sorted[-1]
    if selected_sorted
    else None
)

previous_month = (
    selected_sorted[-2]
    if len(selected_sorted) >= 2
    else None
)

latest_df = filtered[
    filtered["Month"] == latest_month
] if latest_month else filtered

previous_df = filtered[
    filtered["Month"] == previous_month
] if previous_month else pd.DataFrame()


def metric_values(data):

    oq = data[
        CONFIG["order_qty"]
    ].sum()

    iq = data[
        CONFIG["invoice_qty"]
    ].sum()

    ov = data[
        CONFIG["order_value"]
    ].sum()

    iv = data[
        CONFIG["invoice_value"]
    ].sum()

    sale = data[
        CONFIG["sale_loss"]
    ].sum()

    frq = safe_ratio(
        iq,
        oq,
    )

    frv = safe_ratio(
        iv,
        ov,
    )

    return {
        "order_qty": oq,
        "invoice_qty": iq,
        "order_value": ov,
        "invoice_value": iv,
        "sale_loss": sale,
        "fr_qty": frq,
        "fr_value": frv,
        "pending_qty": oq - iq,
        "pending_value": ov - iv,
    }


current_metrics = metric_values(
    latest_df
)

previous_metrics = (
    metric_values(previous_df)
    if not previous_df.empty
    else None
)


# ------------------------------------------------------------
# Cleaner Executive KPI cards
# ------------------------------------------------------------

if latest_month:

    st.caption(
        f"Current Month: **{latest_month}**"
        + (
            f"  |  Previous Month: **{previous_month}**"
            if previous_month
            else ""
        )
    )


k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Fill Rate — Qty",
    format_percent(
        current_metrics["fr_qty"]
    ),
    (
        f"{current_metrics['fr_qty'] - previous_metrics['fr_qty']:+.1f} pp"
        if previous_metrics
        else None
    ),
)

k2.metric(
    "Fill Rate — Value",
    format_percent(
        current_metrics["fr_value"]
    ),
    (
        f"{current_metrics['fr_value'] - previous_metrics['fr_value']:+.1f} pp"
        if previous_metrics
        else None
    ),
)

k3.metric(
    "Pending Qty",
    format_number(
        current_metrics["pending_qty"]
    ),
    (
        f"{current_metrics['pending_qty'] - previous_metrics['pending_qty']:+,.0f}"
        if previous_metrics
        else None
    ),
)

k4.metric(
    "Sale Loss",
    format_value(
        current_metrics["sale_loss"]
    ),
    (
        f"₹ {current_metrics['sale_loss'] - previous_metrics['sale_loss']:+,.0f}"
        if previous_metrics
        else None
    ),
)


k5, k6, k7, k8 = st.columns(4)

k5.metric(
    "Order Qty",
    format_number(
        current_metrics["order_qty"]
    ),
)

k6.metric(
    "Invoice Qty",
    format_number(
        current_metrics["invoice_qty"]
    ),
)

k7.metric(
    "Order Value",
    format_value(
        current_metrics["order_value"]
    ),
)

k8.metric(
    "Invoice Value",
    format_value(
        current_metrics["invoice_value"]
    ),
)


# ============================================================
# TABS
# ============================================================

tab_mom, tab_customer, tab_category = st.tabs(
    [
        "📈 MOM Overview",
        "🏪 Customer Wise",
        "📦 Category Wise",
    ]
)


# ============================================================
# MOM OVERVIEW
# ============================================================

with tab_mom:

    monthly = aggregate_month(
        filtered
    )

    # ========================================================
    # 1. MOM FILL RATE COMPARISON — FIRST
    # ========================================================

    st.markdown(
        '<div class="section-title">Month-on-Month Fill Rate Comparison</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Quantity and Value Fill Rate across the selected months."
    )

    fr_data = monthly[
        [
            "Month",
            "fr_qty",
            "fr_value",
        ]
    ].copy()

    fr_long = fr_data.melt(
        id_vars=["Month"],
        value_vars=[
            "fr_qty",
            "fr_value",
        ],
        var_name="Metric",
        value_name="Fill Rate",
    )

    fr_long["Metric"] = fr_long[
        "Metric"
    ].replace(
        {
            "fr_qty": "Fill Rate Qty",
            "fr_value": "Fill Rate Value",
        }
    )

    # Horizontal labels, visible labels
    fr_chart = (
        alt.Chart(fr_long)
        .mark_line(
            point=alt.OverlayMarkDef(
                filled=True,
                size=85,
            ),
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
                title="Month",
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=13,
                    titleFontSize=13,
                ),
            ),
            y=alt.Y(
                "Fill Rate:Q",
                title="Fill Rate (%)",
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=12,
                    titleFontSize=13,
                ),
                scale=alt.Scale(
                    zero=False
                ),
            ),
            color=alt.Color(
                "Metric:N",
                title="Metric",
            ),
            tooltip=[
                alt.Tooltip(
                    "Month:N",
                    title="Month",
                ),
                alt.Tooltip(
                    "Metric:N",
                    title="Metric",
                ),
                alt.Tooltip(
                    "Fill Rate:Q",
                    title="Fill Rate",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=380
        )
    )

    # Visible point labels
    fr_labels = (
        alt.Chart(fr_long)
        .mark_text(
            dy=-12,
            fontSize=12,
            fontWeight="bold",
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
            ),
            y=alt.Y(
                "Fill Rate:Q"
            ),
            text=alt.Text(
                "Fill Rate:Q",
                format=".1f",
            ),
            color=alt.Color(
                "Metric:N",
                legend=None,
            ),
        )
    )

    st.altair_chart(
        fr_chart + fr_labels,
        use_container_width=True,
    )


    # ========================================================
    # 2. MOM TABLE
    # ========================================================

    st.markdown(
        '<div class="section-title">Month-on-Month Table</div>',
        unsafe_allow_html=True,
    )

    # User can choose columns anytime
    available_mom_columns = {
        "Order Qty": "order_qty",
        "Invoice Qty": "invoice_qty",
        "Fill Rate Qty": "fr_qty",
        "Pending Qty": "pending_qty",
        "Order Value": "order_value",
        "Invoice Value": "invoice_value",
        "Fill Rate Value": "fr_value",
        "Pending Value": "pending_value",
        "Sale Loss": "sale_loss",
        "Orders": "orders",
        "Invoices": "invoices",
    }

    default_mom_columns = [
        "Order Qty",
        "Invoice Qty",
        "Fill Rate Qty",
        "Pending Qty",
        "Fill Rate Value",
        "Sale Loss",
    ]

    with st.expander(
        "⚙️ Choose MOM Table Columns",
        expanded=False,
    ):

        selected_mom_columns = st.multiselect(
            "Columns to show",
            list(
                available_mom_columns.keys()
            ),
            default=default_mom_columns,
            key="mom_table_columns",
        )

    if not selected_mom_columns:

        selected_mom_columns = default_mom_columns


    mom_display = monthly[
        ["Month"]
        + [
            available_mom_columns[c]
            for c in selected_mom_columns
        ]
    ].copy()

    rename_reverse = {
        value: key
        for key, value
        in available_mom_columns.items()
    }

    mom_display = mom_display.rename(
        columns=rename_reverse
    )

    # Format display
    for col in mom_display.columns:

        if col == "Month":
            continue

        if (
            "Fill Rate" in col
        ):

            mom_display[col] = mom_display[
                col
            ].map(
                lambda x:
                "—"
                if pd.isna(x)
                else f"{x:.1f}%"
            )

        elif (
            "Value" in col
            or col == "Sale Loss"
        ):

            mom_display[col] = mom_display[
                col
            ].map(
                format_value
            )

        else:

            mom_display[col] = mom_display[
                col
            ].map(
                format_number
            )

    st.dataframe(
        mom_display,
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # 3. FILL RATE QTY VS VALUE
    # ========================================================

    st.markdown(
        '<div class="section-title">Fill Rate — Qty vs Value</div>',
        unsafe_allow_html=True,
    )

    fr_compare = monthly[
        [
            "Month",
            "fr_qty",
            "fr_value",
        ]
    ].melt(
        id_vars=["Month"],
        var_name="Metric",
        value_name="Fill Rate",
    )

    fr_compare["Metric"] = fr_compare[
        "Metric"
    ].replace(
        {
            "fr_qty": "Qty",
            "fr_value": "Value",
        }
    )

    fr_bar = (
        alt.Chart(fr_compare)
        .mark_bar(
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
                title="Month",
                axis=alt.Axis(
                    labelAngle=0
                ),
            ),
            xOffset=alt.XOffset(
                "Metric:N"
            ),
            y=alt.Y(
                "Fill Rate:Q",
                title="Fill Rate (%)",
            ),
            color=alt.Color(
                "Metric:N",
                title="Metric",
            ),
            tooltip=[
                "Month:N",
                "Metric:N",
                alt.Tooltip(
                    "Fill Rate:Q",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=360
        )
    )

    fr_bar_labels = (
        alt.Chart(fr_compare)
        .mark_text(
            dy=-7,
            fontSize=11,
            fontWeight="bold",
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
            ),
            xOffset=alt.XOffset(
                "Metric:N"
            ),
            y=alt.Y(
                "Fill Rate:Q"
            ),
            text=alt.Text(
                "Fill Rate:Q",
                format=".1f",
            ),
            color=alt.Color(
                "Metric:N",
                legend=None,
            ),
        )
    )

    st.altair_chart(
        fr_bar + fr_bar_labels,
        use_container_width=True,
    )


    # ========================================================
    # 4. SALE LOSS MOM
    # ========================================================

    st.markdown(
        '<div class="section-title">Sale Loss MOM</div>',
        unsafe_allow_html=True,
    )

    if "sale_loss" in monthly.columns:

        sale_chart = (
            alt.Chart(monthly)
            .mark_bar(
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5,
            )
            .encode(
                x=alt.X(
                    "Month:N",
                    sort=available_months,
                    title="Month",
                    axis=alt.Axis(
                        labelAngle=0
                    ),
                ),
                y=alt.Y(
                    "sale_loss:Q",
                    title="Sale Loss",
                    axis=alt.Axis(
                        labelAngle=0
                    ),
                ),
                tooltip=[
                    "Month:N",
                    alt.Tooltip(
                        "sale_loss:Q",
                        title="Sale Loss",
                        format=",.0f",
                    ),
                ],
            )
            .properties(
                height=350
            )
        )

        sale_labels = (
            alt.Chart(monthly)
            .mark_text(
                dy=-8,
                fontSize=12,
                fontWeight="bold",
            )
            .encode(
                x=alt.X(
                    "Month:N",
                    sort=available_months,
                ),
                y=alt.Y(
                    "sale_loss:Q"
                ),
                text=alt.Text(
                    "sale_loss:Q",
                    format=",.0f",
                ),
            )
        )

        st.altair_chart(
            sale_chart + sale_labels,
            use_container_width=True,
        )


    # ========================================================
    # 5. LAST MONTH VS THIS MONTH
    # ========================================================

    st.markdown(
        '<div class="section-title">Last Month vs This Month</div>',
        unsafe_allow_html=True,
    )

    if len(monthly) >= 2:

        prev = monthly.iloc[-2]
        curr = monthly.iloc[-1]

        p1, p2, p3, p4 = st.columns(4)

        p1.metric(
            "Fill Rate Qty",
            format_percent(
                curr["fr_qty"]
            ),
            f"{curr['fr_qty'] - prev['fr_qty']:+.1f} pp",
        )

        p2.metric(
            "Fill Rate Value",
            format_percent(
                curr["fr_value"]
            ),
            f"{curr['fr_value'] - prev['fr_value']:+.1f} pp",
        )

        p3.metric(
            "Pending Qty",
            format_number(
                curr["pending_qty"]
            ),
            f"{curr['pending_qty'] - prev['pending_qty']:+,.0f}",
        )

        p4.metric(
            "Sale Loss",
            format_value(
                curr.get("sale_loss", 0)
            ),
            f"₹ {curr.get('sale_loss', 0) - prev.get('sale_loss', 0):+,.0f}",
        )

        st.caption(
            f"{prev['Month']} → {curr['Month']}"
        )

    else:

        st.info(
            "Select at least two months to compare."
        )


# ============================================================
# CUSTOMER WISE
# ============================================================

with tab_customer:

    st.markdown(
        '<div class="section-title">Customer Wise Performance</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Original customer/shop logic retained — click a customer to open its complete order details."
    )

    # --------------------------------------------------------
    # Customer summary
    # --------------------------------------------------------

    customer_summary = build_customer_summary(
        filtered
    )

    # --------------------------------------------------------
    # Original search
    # --------------------------------------------------------

    customer_search = st.text_input(
        "🔍 Search customer name",
        key="customer_search",
    )

    shop_view = customer_summary.copy()

    if customer_search:

        shop_view = shop_view[
            shop_view[
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
        f"{len(shop_view):,} of {len(customer_summary):,} customers"
    )


    # --------------------------------------------------------
    # Original column picker
    # --------------------------------------------------------

    metric_options = [
        "Order Qty",
        "Invoice Qty",
        "Fill Rate",
    ]

    if "order_count" in shop_view.columns:
        metric_options.insert(
            0,
            "Order (count)"
        )

    if "invoice_count" in shop_view.columns:
        metric_options.insert(
            1 if "order_count" in shop_view.columns else 0,
            "Invoice (count)"
        )

    if "sale_loss" in shop_view.columns:
        metric_options.append(
            "Sale Loss (In Lacs)"
        )

    if "tat_avg" in shop_view.columns:
        metric_options.append(
            "TAT (avg)"
        )

    with st.expander(
        "⚙️ Columns to show",
        expanded=False,
    ):

        visible_metrics = st.multiselect(
            "Columns to show",
            metric_options,
            default=metric_options,
            key="customer_visible_cols",
        )

    if not visible_metrics:

        visible_metrics = metric_options


    SORT_KEY_MAP = {
        "Order (count)": "order_count",
        "Invoice (count)": "invoice_count",
        "Order Qty": "order_qty",
        "Invoice Qty": "invoice_qty",
        "Fill Rate": "fill_rate",
        "Sale Loss (In Lacs)": "sale_loss",
        "TAT (avg)": "tat_avg",
    }


    # --------------------------------------------------------
    # Original sort state
    # --------------------------------------------------------

    if "customer_sort_col" not in st.session_state:

        st.session_state[
            "customer_sort_col"
        ] = None

        st.session_state[
            "customer_sort_dir"
        ] = None


    if "selected_customer" not in st.session_state:

        st.session_state[
            "selected_customer"
        ] = None


    def cycle_customer_sort(
        col_key
    ):

        current_col = st.session_state[
            "customer_sort_col"
        ]

        current_dir = st.session_state[
            "customer_sort_dir"
        ]

        if current_col != col_key:

            st.session_state[
                "customer_sort_col"
            ] = col_key

            st.session_state[
                "customer_sort_dir"
            ] = "asc"

        elif current_dir == "asc":

            st.session_state[
                "customer_sort_dir"
            ] = "desc"

        else:

            st.session_state[
                "customer_sort_col"
            ] = None

            st.session_state[
                "customer_sort_dir"
            ] = None


    def customer_arrow(
        col_key
    ):

        if (
            st.session_state[
                "customer_sort_col"
            ]
            != col_key
        ):

            return ""

        return (
            " ▲"
            if st.session_state[
                "customer_sort_dir"
            ] == "asc"
            else " ▼"
        )


    # --------------------------------------------------------
    # Original clickable customer table
    # --------------------------------------------------------

    header_widths = [
        3
    ] + [
        1
    ] * len(visible_metrics)


    with st.container(
        key="fillrate_table"
    ):

        header_cols = st.columns(
            header_widths
        )

        if header_cols[0].button(
            f"{CONFIG['customer']}"
            f"{customer_arrow('__customer__')}",
            key="customer_header",
            use_container_width=True,
        ):

            cycle_customer_sort(
                "__customer__"
            )

        for hc, label in zip(
            header_cols[1:],
            visible_metrics,
        ):

            key = SORT_KEY_MAP[
                label
            ]

            if hc.button(
                f"{label}"
                f"{customer_arrow(key)}",
                key=f"customer_header_{key}",
                use_container_width=True,
            ):

                cycle_customer_sort(
                    key
                )


        # Apply sort
        active_col = st.session_state[
            "customer_sort_col"
        ]

        active_dir = st.session_state[
            "customer_sort_dir"
        ]

        if active_col:

            sort_col = (
                CONFIG["customer"]
                if active_col
                == "__customer__"
                else active_col
            )

            shop_view = shop_view.sort_values(
                sort_col,
                ascending=(
                    active_dir == "asc"
                ),
                na_position="last",
            )


        # ----------------------------------------------------
        # Rows
        # ----------------------------------------------------

        for row_idx, row in (
            shop_view
            .reset_index(drop=True)
            .iterrows()
        ):

            row_cols = st.columns(
                header_widths
            )

            if row_cols[0].button(
                str(
                    row[
                        CONFIG["customer"]
                    ]
                ),
                key=(
                    f"customer_btn_"
                    f"{row_idx}_"
                    f"{row[CONFIG['customer']]}"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "selected_customer"
                ] = row[
                    CONFIG["customer"]
                ]

                st.rerun()


            for rc, label in zip(
                row_cols[1:],
                visible_metrics,
            ):

                if label == "Order (count)":

                    center(
                        rc,
                        f"{int(row['order_count']):,}",
                    )

                elif label == "Invoice (count)":

                    center(
                        rc,
                        f"{int(row['invoice_count']):,}",
                    )

                elif label == "Order Qty":

                    center(
                        rc,
                        f"{row['order_qty']:,.0f}",
                    )

                elif label == "Invoice Qty":

                    center(
                        rc,
                        f"{row['invoice_qty']:,.0f}",
                    )

                elif label == "Fill Rate":

                    value = row[
                        "fill_rate"
                    ]

                    center(
                        rc,
                        (
                            "—"
                            if pd.isna(value)
                            else f"{value:.1f}%"
                        ),
                    )

                elif label == "Sale Loss (In Lacs)":

                    value = row.get(
                        "sale_loss"
                    )

                    center(
                        rc,
                        (
                            "—"
                            if value is None
                            or pd.isna(value)
                            else f"₹ {value:,.2f}"
                        ),
                    )

                elif label == "TAT (avg)":

                    value = row.get(
                        "tat_avg"
                    )

                    center(
                        rc,
                        (
                            "—"
                            if value is None
                            or pd.isna(value)
                            else f"{value:.1f}"
                        ),
                    )


    # --------------------------------------------------------
    # Open original-style dialog
    # --------------------------------------------------------

    if st.session_state.get(
        "selected_customer"
    ):

        show_customer_details(
            st.session_state[
                "selected_customer"
            ],
            filtered,
        )


# ============================================================
# CATEGORY WISE
# ============================================================

with tab_category:

    st.markdown(
        '<div class="section-title">Category Wise Performance</div>',
        unsafe_allow_html=True,
    )

    category_col = CONFIG["category"]

    category_summary = (
        filtered
        .groupby(
            category_col,
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
            order_value=(
                CONFIG["order_value"],
                "sum",
            ),
            invoice_value=(
                CONFIG["invoice_value"],
                "sum",
            ),
            sale_loss=(
                CONFIG["sale_loss"],
                "sum",
            ),
            orders=(
                CONFIG["order_id"],
                "nunique",
            ),
        )
        .reset_index()
    )

    category_summary["fr_qty"] = np.where(
        category_summary["order_qty"] != 0,
        category_summary["invoice_qty"]
        / category_summary["order_qty"]
        * 100,
        np.nan,
    )

    category_summary["fr_value"] = np.where(
        category_summary["order_value"] != 0,
        category_summary["invoice_value"]
        / category_summary["order_value"]
        * 100,
        np.nan,
    )

    category_summary["pending_qty"] = (
        category_summary["order_qty"]
        - category_summary["invoice_qty"]
    )

    category_summary["pending_value"] = (
        category_summary["order_value"]
        - category_summary["invoice_value"]
    )


    # --------------------------------------------------------
    # Category table
    # --------------------------------------------------------

    category_display = category_summary[
        [
            category_col,
            "orders",
            "order_qty",
            "invoice_qty",
            "fr_qty",
            "fr_value",
            "pending_qty",
            "order_value",
            "invoice_value",
            "pending_value",
            "sale_loss",
        ]
    ].rename(
        columns={
            category_col: "Category",
            "orders": "Orders",
            "order_qty": "Order Qty",
            "invoice_qty": "Invoice Qty",
            "fr_qty": "FR % Qty",
            "fr_value": "FR % Value",
            "pending_qty": "Pending Qty",
            "order_value": "Order Value",
            "invoice_value": "Invoice Value",
            "pending_value": "Pending Value",
            "sale_loss": "Sale Loss",
        }
    )

    st.dataframe(
        category_display,
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # Category Fill Rate Chart
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Category Fill Rate</div>',
        unsafe_allow_html=True,
    )

    category_chart_data = category_summary[
        [
            category_col,
            "fr_qty",
        ]
    ].copy()

    category_chart = (
        alt.Chart(
            category_chart_data
        )
        .mark_bar(
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
        )
        .encode(
            x=alt.X(
                f"{category_col}:N",
                title="Category",
                sort="-y",
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=12,
                ),
            ),
            y=alt.Y(
                "fr_qty:Q",
                title="Fill Rate (%)",
                axis=alt.Axis(
                    labelAngle=0
                ),
            ),
            tooltip=[
                f"{category_col}:N",
                alt.Tooltip(
                    "fr_qty:Q",
                    title="Fill Rate",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=380
        )
    )

    category_labels = (
        alt.Chart(
            category_chart_data
        )
        .mark_text(
            dy=-8,
            fontSize=12,
            fontWeight="bold",
        )
        .encode(
            x=alt.X(
                f"{category_col}:N",
                sort="-y",
            ),
            y=alt.Y(
                "fr_qty:Q"
            ),
            text=alt.Text(
                "fr_qty:Q",
                format=".1f",
            ),
        )
    )

    st.altair_chart(
        category_chart
        + category_labels,
        use_container_width=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Monthly sheets detected: "
    f"{', '.join(loaded_sheets)}"
    f"  |  "
    f"Filtered rows: {len(filtered):,}"
    f"  |  "
    f"Updated: {datetime.now().strftime('%d-%m-%Y %H:%M')}"
)
