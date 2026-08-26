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
    page_title="MOM Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {
    # IMPORTANT:
    # Keep this exactly as your existing Streamlit secret.
    "sharepoint_secret": "SHAREPOINT_EXCEL_URL",

    # Main dimensions
    "month": "Month",
    "channel": "Channel",
    "zone": "Zone",
    "db_code": "DB Code",
    "customer": "Customer Name",
    "order_category": "Order Category",
    "category": "Category",
    "name": "Name",
    "type": "Type",

    # Order
    "order_id": "Order Id",
    "external_document": "External Document No.",
    "order_received": "Order Received Date",
    "order_upload": "Order Upload date",
    "wh_receiving": "Wh Receiving Date",
    "order_qty": "Order Qty",
    "order_value": "Order Value",
    "order_punch": "Order Punch time",

    # Invoice
    "invoice_date": "Invoice Date",
    "invoice_qty": "Invoice Qty",
    "invoice_value": "Invoice Value",
    "invoice_number": "InvoiceNumber",
    "invoice_time": "Invoice Time",

    # Fill Rate
    "fr_value": "Over all FR % (Value)",
    "fr_qty": "Over all FR % (Qty)",

    # Dispatch
    "dispatch_date": "Dispatch Date",
    "awb": "AWB NUMBER",
    "courier": "COURIER",
    "mode": "Mode",
    "box": "Box",
    "weight": "Weight",

    # Delivery
    "pin_code": "Pin Code",
    "delivery_status": "Delivery Status",
    "delivery_date": "Delivery Date",

    # SLA / TAT
    "dispatched_sla": "Dispatched SLA",
    "logistics_sla": "Logistics SLA",
    "ageing": "Agening",
    "standard_tat": "Standard TAT",
    "order_to_wh": "Order to wh",
    "oti": "OTI",
    "otd": "OTD",
    "otde": "OTDE",
    "dispatch_to_delivery": "Dispatch to Deli TAT",
    "otd_bucket": "OTD Bucket",
    "otw_days": "OTW Days",
    "invoice_days": "Invoice Days",
    "dispatch_days": "Dispatch Days",
    "actual_delivery_days": "Actual Deli. Days",
    "variance": "Vairance",

    # Remarks
    "wh_remarks": "Wh. Remarks",
    "wh_remark": "Wh Remark",
    "logistics_remarks": "Logistics Remarks",
    "sro": "SRO Number",
    "omt_remarks": "OMT REMARKS",
    "ho_remarks": "HO Remarks",
    "final_remarks": "Final Remarks",

    # Commercial
    "order_value_lacs": "Order Value Lacs",
    "invoice_value_lacs": "Invoice Value Lacs",
    "sale_loss": "Sale Loss",

    # Other
    "other_otd": "OTD",
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
# STYLE
# ============================================================

st.markdown(
    """
    <style>

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

    h1, h2, h3, h4 {
        color: #F9FAFB !important;
    }

    div[data-testid="stMetric"] {
        background: #11161D;
        border: 1px solid #252B34;
        border-radius: 14px;
        padding: 14px 16px;
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

    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #F9FAFB;
        margin-top: 18px;
        margin-bottom: 10px;
    }

    .dashboard-subtitle {
        color: #9CA3AF;
        font-size: 14px;
        margin-top: -10px;
        margin-bottom: 20px;
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
# HELPERS
# ============================================================

def normalize_columns(df):
    df = df.copy()

    new_cols = []
    seen = {}

    for col in df.columns:
        col = str(col).strip()

        if col not in seen:
            seen[col] = 0
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}.{seen[col]}")

    df.columns = new_cols
    return df


def resolve_col(target, columns):
    """Case/space tolerant column resolver."""

    if target in columns:
        return target

    key = str(target).strip().lower()

    for col in columns:
        if str(col).strip().lower() == key:
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
                "None": np.nan,
                "NaN": np.nan,
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


def safe_ratio(numerator, denominator):
    numerator = pd.to_numeric(
        numerator,
        errors="coerce",
    )

    denominator = pd.to_numeric(
        denominator,
        errors="coerce",
    )

    return np.where(
        denominator != 0,
        numerator / denominator * 100,
        np.nan,
    )


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


def get_delta(current, previous):
    if previous is None or pd.isna(previous):
        return None

    if pd.isna(current):
        return None

    return current - previous


def delta_text(current, previous, suffix=""):
    delta = get_delta(current, previous)

    if delta is None:
        return None

    sign = "+" if delta > 0 else ""

    return f"{sign}{delta:.1f}{suffix}"


def is_valid_month_sheet(sheet_name):
    return str(sheet_name).strip() in MONTH_ORDER


# ============================================================
# SHAREPOINT
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
    show_spinner="Fetching latest Excel workbook..."
)
def download_workbook(url):

    response = requests.get(
        get_download_url(url),
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
            "SharePoint returned an HTML/login page instead of "
            "the Excel workbook. Check the sharing permission."
        )

    return response.content


# ============================================================
# LOAD + COMBINE MONTHLY SHEETS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner="Reading Apr-Aug monthly sheets..."
)
def load_data(url):

    content = download_workbook(url)

    workbook = pd.read_excel(
        io.BytesIO(content),
        sheet_name=None,
        engine="openpyxl",
    )

    frames = []
    loaded_sheets = []

    for sheet_name, raw_df in workbook.items():

        sheet_name = str(sheet_name).strip()

        if not is_valid_month_sheet(sheet_name):
            continue

        if raw_df is None or raw_df.empty:
            continue

        df = normalize_columns(
            raw_df.copy()
        )

        # The sheet name is the authoritative month.
        df["__Dashboard_Month"] = sheet_name

        frames.append(df)
        loaded_sheets.append(sheet_name)

    if not frames:
        raise ValueError(
            "No monthly sheets found. Expected sheets such as "
            "Apr, May, Jun, Jul, Aug."
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

        if actual is not None:
            combined[actual] = clean_numeric(
                combined[actual]
            )

    # --------------------------------------------------------
    # DATE COLUMNS
    # --------------------------------------------------------

    date_columns = [
        CONFIG["order_received"],
        CONFIG["order_upload"],
        CONFIG["wh_receiving"],
        CONFIG["invoice_date"],
        CONFIG["dispatch_date"],
        CONFIG["delivery_date"],
    ]

    for col in date_columns:

        actual = resolve_col(
            col,
            combined.columns,
        )

        if actual is not None:

            combined[actual] = pd.to_datetime(
                combined[actual],
                errors="coerce",
                dayfirst=True,
            )

    # --------------------------------------------------------
    # TIME COLUMNS
    # --------------------------------------------------------

    for col in [
        CONFIG["order_punch"],
        CONFIG["invoice_time"],
    ]:

        actual = resolve_col(
            col,
            combined.columns,
        )

        if actual is not None:

            # Keep as string; Excel may contain mixed time formats.
            combined[actual] = (
                combined[actual]
                .astype(str)
                .replace("NaT", "")
            )

    # --------------------------------------------------------
    # DERIVED METRICS
    # --------------------------------------------------------

    order_qty_col = resolve_col(
        CONFIG["order_qty"],
        combined.columns,
    )

    invoice_qty_col = resolve_col(
        CONFIG["invoice_qty"],
        combined.columns,
    )

    order_value_col = resolve_col(
        CONFIG["order_value"],
        combined.columns,
    )

    invoice_value_col = resolve_col(
        CONFIG["invoice_value"],
        combined.columns,
    )

    if order_qty_col and invoice_qty_col:

        combined["__FR_QTY_CALC"] = safe_ratio(
            combined[invoice_qty_col],
            combined[order_qty_col],
        )

    else:

        combined["__FR_QTY_CALC"] = np.nan

    if order_value_col and invoice_value_col:

        combined["__FR_VALUE_CALC"] = safe_ratio(
            combined[invoice_value_col],
            combined[order_value_col],
        )

    else:

        combined["__FR_VALUE_CALC"] = np.nan

    # --------------------------------------------------------
    # Prefer official FR columns where available.
    # But keep calculated FR for validation.
    # --------------------------------------------------------

    official_fr_qty = resolve_col(
        CONFIG["fr_qty"],
        combined.columns,
    )

    official_fr_value = resolve_col(
        CONFIG["fr_value"],
        combined.columns,
    )

    if official_fr_qty:

        combined["__FR_QTY"] = clean_numeric(
            combined[official_fr_qty]
        )

    else:

        combined["__FR_QTY"] = combined[
            "__FR_QTY_CALC"
        ]

    if official_fr_value:

        combined["__FR_VALUE"] = clean_numeric(
            combined[official_fr_value]
        )

    else:

        combined["__FR_VALUE"] = combined[
            "__FR_VALUE_CALC"
        ]

    # --------------------------------------------------------
    # Pending quantities / values
    # --------------------------------------------------------

    combined["__Pending_Qty"] = np.nan
    combined["__Pending_Value"] = np.nan

    if order_qty_col and invoice_qty_col:

        combined["__Pending_Qty"] = (
            combined[order_qty_col].fillna(0)
            - combined[invoice_qty_col].fillna(0)
        )

    if order_value_col and invoice_value_col:

        combined["__Pending_Value"] = (
            combined[order_value_col].fillna(0)
            - combined[invoice_value_col].fillna(0)
        )

    # --------------------------------------------------------
    # Month
    # --------------------------------------------------------

    combined["Month"] = combined[
        "__Dashboard_Month"
    ]

    combined["__Month_Sort"] = combined[
        "Month"
    ].apply(month_sort_key)

    combined = combined.sort_values(
        "__Month_Sort"
    ).reset_index(drop=True)

    return combined, loaded_sheets


# ============================================================
# VALIDATION
# ============================================================

def validate_columns(df):

    required = [
        CONFIG["customer"],
        CONFIG["order_qty"],
        CONFIG["invoice_qty"],
        CONFIG["order_value"],
        CONFIG["invoice_value"],
        CONFIG["order_id"],
    ]

    missing = []

    for col in required:

        if resolve_col(
            col,
            df.columns,
        ) is None:

            missing.append(col)

    return missing


# ============================================================
# AGGREGATION
# ============================================================

def aggregate_data(
    df,
    group_columns,
):

    order_qty_col = resolve_col(
        CONFIG["order_qty"],
        df.columns,
    )

    invoice_qty_col = resolve_col(
        CONFIG["invoice_qty"],
        df.columns,
    )

    order_value_col = resolve_col(
        CONFIG["order_value"],
        df.columns,
    )

    invoice_value_col = resolve_col(
        CONFIG["invoice_value"],
        df.columns,
    )

    sale_loss_col = resolve_col(
        CONFIG["sale_loss"],
        df.columns,
    )

    order_id_col = resolve_col(
        CONFIG["order_id"],
        df.columns,
    )

    invoice_no_col = resolve_col(
        CONFIG["invoice_number"],
        df.columns,
    )

    customer_col = resolve_col(
        CONFIG["customer"],
        df.columns,
    )

    db_col = resolve_col(
        CONFIG["db_code"],
        df.columns,
    )

    # Build aggregation dynamically.
    agg = {}

    if order_qty_col:
        agg["order_qty"] = (
            order_qty_col,
            "sum",
        )

    if invoice_qty_col:
        agg["invoice_qty"] = (
            invoice_qty_col,
            "sum",
        )

    if order_value_col:
        agg["order_value"] = (
            order_value_col,
            "sum",
        )

    if invoice_value_col:
        agg["invoice_value"] = (
            invoice_value_col,
            "sum",
        )

    if sale_loss_col:
        agg["sale_loss"] = (
            sale_loss_col,
            "sum",
        )

    if order_id_col:
        agg["orders"] = (
            order_id_col,
            "nunique",
        )

    if invoice_no_col:
        agg["invoices"] = (
            invoice_no_col,
            lambda x: x.dropna()
            .astype(str)
            .nunique(),
        )

    if customer_col:
        agg["customers"] = (
            customer_col,
            "nunique",
        )

    if db_col:
        agg["db_codes"] = (
            db_col,
            "nunique",
        )

    result = (
        df.groupby(
            group_columns,
            dropna=False,
        )
        .agg(**agg)
        .reset_index()
    )

    # Derived metrics
    if "order_qty" in result.columns:

        if "invoice_qty" in result.columns:

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

        if "invoice_value" in result.columns:

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

    # TAT metrics if available
    actual_tat_col = resolve_col(
        CONFIG["actual_delivery_days"],
        df.columns,
    )

    standard_tat_col = resolve_col(
        CONFIG["standard_tat"],
        df.columns,
    )

    variance_col = resolve_col(
        CONFIG["variance"],
        df.columns,
    )

    if actual_tat_col:

        temp = df.copy()

        temp[actual_tat_col] = clean_numeric(
            temp[actual_tat_col]
        )

        tat_avg = (
            temp.groupby(
                group_columns,
                dropna=False,
            )[actual_tat_col]
            .mean()
            .reset_index(
                name="avg_actual_tat"
            )
        )

        result = result.merge(
            tat_avg,
            on=group_columns,
            how="left",
        )

    if standard_tat_col:

        temp = df.copy()

        temp[standard_tat_col] = clean_numeric(
            temp[standard_tat_col]
        )

        std_tat = (
            temp.groupby(
                group_columns,
                dropna=False,
            )[standard_tat_col]
            .mean()
            .reset_index(
                name="avg_standard_tat"
            )
        )

        result = result.merge(
            std_tat,
            on=group_columns,
            how="left",
        )

    if variance_col:

        temp = df.copy()

        temp[variance_col] = clean_numeric(
            temp[variance_col]
        )

        variance = (
            temp.groupby(
                group_columns,
                dropna=False,
            )[variance_col]
            .mean()
            .reset_index(
                name="avg_variance"
            )
        )

        result = result.merge(
            variance,
            on=group_columns,
            how="left",
        )

    return result


# ============================================================
# KPI DISPLAY
# ============================================================

def show_kpis(df):

    order_qty_col = resolve_col(
        CONFIG["order_qty"],
        df.columns,
    )

    invoice_qty_col = resolve_col(
        CONFIG["invoice_qty"],
        df.columns,
    )

    order_value_col = resolve_col(
        CONFIG["order_value"],
        df.columns,
    )

    invoice_value_col = resolve_col(
        CONFIG["invoice_value"],
        df.columns,
    )

    sale_loss_col = resolve_col(
        CONFIG["sale_loss"],
        df.columns,
    )

    order_id_col = resolve_col(
        CONFIG["order_id"],
        df.columns,
    )

    customer_col = resolve_col(
        CONFIG["customer"],
        df.columns,
    )

    # Totals
    order_qty = (
        df[order_qty_col].sum()
        if order_qty_col
        else 0
    )

    invoice_qty = (
        df[invoice_qty_col].sum()
        if invoice_qty_col
        else 0
    )

    order_value = (
        df[order_value_col].sum()
        if order_value_col
        else 0
    )

    invoice_value = (
        df[invoice_value_col].sum()
        if invoice_value_col
        else 0
    )

    sale_loss = (
        df[sale_loss_col].sum()
        if sale_loss_col
        else 0
    )

    fr_qty = safe_ratio(
        invoice_qty,
        order_qty,
    )

    fr_value = safe_ratio(
        invoice_value,
        order_value,
    )

    pending_qty = (
        order_qty
        - invoice_qty
    )

    pending_value = (
        order_value
        - invoice_value
    )

    orders = (
        df[order_id_col]
        .nunique()
        if order_id_col
        else 0
    )

    customers = (
        df[customer_col]
        .nunique()
        if customer_col
        else 0
    )

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
        "FR % — Qty",
        format_percent(fr_qty),
    )

    c4.metric(
        "Pending Qty",
        format_number(pending_qty),
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
        "FR % — Value",
        format_percent(fr_value),
    )

    c8.metric(
        "Pending Value",
        format_value(pending_value),
    )

    c9, c10, c11 = st.columns(3)

    c9.metric(
        "Sale Loss",
        format_value(sale_loss),
    )

    c10.metric(
        "Orders",
        format_number(orders),
    )

    c11.metric(
        "Customers",
        format_number(customers),
    )


# ============================================================
# MONTHLY SUMMARY
# ============================================================

def create_monthly_summary(df):

    summary = aggregate_data(
        df,
        ["Month"],
    )

    summary["__sort"] = summary[
        "Month"
    ].apply(month_sort_key)

    summary = summary.sort_values(
        "__sort"
    ).drop(
        columns="__sort"
    )

    return summary


# ============================================================
# MAIN HEADER
# ============================================================

st.title(
    "📊 MOM Operations Dashboard"
)

st.markdown(
    """
    <div class="dashboard-subtitle">
        Order → Invoice → Fill Rate → Dispatch → Delivery → TAT → Sale Loss
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
        "SHAREPOINT_EXCEL_URL is not configured in Streamlit Secrets."
    )

    st.stop()


# ============================================================
# LOAD
# ============================================================

try:

    df, loaded_sheets = load_data(
        sharepoint_url
    )

except Exception as e:

    st.error(
        f"Could not load the SharePoint Excel file: {e}"
    )

    st.stop()


# ============================================================
# VALIDATE
# ============================================================

missing = validate_columns(
    df
)

if missing:

    st.error(
        "The following required columns are missing:"
    )

    for col in missing:
        st.write(f"- {col}")

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🎛 Filters"
    )

    if st.button(
        "🔄 Refresh Now",
        use_container_width=True,
    ):

        download_workbook.clear()
        load_data.clear()

        st.rerun()

    st.markdown("---")

    available_months = sorted(
        loaded_sheets,
        key=month_sort_key,
    )

    selected_months = st.multiselect(
        "Month",
        available_months,
        default=available_months,
    )

    def get_options(column):

        actual = resolve_col(
            column,
            df.columns,
        )

        if not actual:
            return []

        return sorted(
            df[actual]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    selected_channels = st.multiselect(
        "Channel",
        get_options(
            CONFIG["channel"]
        ),
    )

    selected_zones = st.multiselect(
        "Zone",
        get_options(
            CONFIG["zone"]
        ),
    )

    selected_names = st.multiselect(
        "Name",
        get_options(
            CONFIG["name"]
        ),
    )

    selected_categories = st.multiselect(
        "Category",
        get_options(
            CONFIG["category"]
        ),
    )

    selected_order_categories = st.multiselect(
        "Order Category",
        get_options(
            CONFIG["order_category"]
        ),
    )

    selected_customers = st.multiselect(
        "Customer",
        get_options(
            CONFIG["customer"]
        ),
    )

    selected_status = st.multiselect(
        "Delivery Status",
        get_options(
            CONFIG["delivery_status"]
        ),
    )

    selected_final_remarks = st.multiselect(
        "Final Remarks",
        get_options(
            CONFIG["final_remarks"]
        ),
    )

    st.markdown("---")

    st.caption(
        f"Sheets: {', '.join(available_months)}"
    )

    st.caption(
        f"Total rows: {len(df):,}"
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = df.copy()


def apply_multiselect(
    dataframe,
    column,
    values,
):

    if not values:
        return dataframe

    actual = resolve_col(
        column,
        dataframe.columns,
    )

    if not actual:
        return dataframe

    return dataframe[
        dataframe[actual]
        .astype(str)
        .isin(values)
    ]


if selected_months:

    filtered = filtered[
        filtered["Month"]
        .isin(selected_months)
    ]

filtered = apply_multiselect(
    filtered,
    CONFIG["channel"],
    selected_channels,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["zone"],
    selected_zones,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["name"],
    selected_names,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["category"],
    selected_categories,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["order_category"],
    selected_order_categories,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["customer"],
    selected_customers,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["delivery_status"],
    selected_status,
)

filtered = apply_multiselect(
    filtered,
    CONFIG["final_remarks"],
    selected_final_remarks,
)


if filtered.empty:

    st.warning(
        "No records match the selected filters."
    )

    st.stop()


# ============================================================
# FILTER STATUS
# ============================================================

st.caption(
    f"Showing {len(filtered):,} rows | "
    f"{filtered['Month'].nunique()} month(s)"
)


# ============================================================
# EXECUTIVE KPI
# ============================================================

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True,
)

show_kpis(
    filtered
)


# ============================================================
# TABS
# ============================================================

(
    tab_mom,
    tab_chain,
    tab_customer,
    tab_category,
    tab_tat,
    tab_orders,
) = st.tabs(
    [
        "📈 MOM Overview",
        "🏢 Channel / Chain",
        "🏪 Customer",
        "📦 Category",
        "⏱ TAT & SLA",
        "🔎 Order Details",
    ]
)


# ============================================================
# TAB 1 — MOM OVERVIEW
# ============================================================

with tab_mom:

    st.markdown(
        '<div class="section-title">Month-on-Month Performance</div>',
        unsafe_allow_html=True,
    )

    monthly = create_monthly_summary(
        filtered
    )

    # --------------------------------------------------------
    # MOM TABLE
    # --------------------------------------------------------

    mom_display = monthly.copy()

    rename_map = {
        "order_qty": "Order Qty",
        "invoice_qty": "Invoice Qty",
        "fr_qty": "FR % Qty",
        "pending_qty": "Pending Qty",
        "order_value": "Order Value",
        "invoice_value": "Invoice Value",
        "fr_value": "FR % Value",
        "pending_value": "Pending Value",
        "sale_loss": "Sale Loss",
        "orders": "Orders",
        "invoices": "Invoices",
        "customers": "Customers",
        "db_codes": "DB Codes",
    }

    mom_display = mom_display.rename(
        columns=rename_map
    )

    display_columns = [
        "Month",
        "Order Qty",
        "Invoice Qty",
        "FR % Qty",
        "Pending Qty",
        "Order Value",
        "Invoice Value",
        "FR % Value",
        "Pending Value",
        "Sale Loss",
        "Orders",
        "Invoices",
        "Customers",
        "DB Codes",
    ]

    display_columns = [
        c
        for c in display_columns
        if c in mom_display.columns
    ]

    st.dataframe(
        mom_display[display_columns],
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # FR TREND
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Fill Rate — Qty vs Value</div>',
        unsafe_allow_html=True,
    )

    fr_chart_df = monthly[
        [
            "Month",
            "fr_qty",
            "fr_value",
        ]
    ].copy()

    fr_long = fr_chart_df.melt(
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
            "fr_qty": "FR % — Qty",
            "fr_value": "FR % — Value",
        }
    )

    chart = (
        alt.Chart(fr_long)
        .mark_line(
            point=alt.OverlayMarkDef(
                filled=True,
                size=70,
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
                "Fill Rate:Q",
                title="Fill Rate %",
                scale=alt.Scale(
                    zero=False
                ),
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

    st.altair_chart(
        chart,
        use_container_width=True,
    )


    # --------------------------------------------------------
    # ORDER / INVOICE VALUE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Order vs Invoice Value</div>',
        unsafe_allow_html=True,
    )

    value_data = monthly[
        [
            "Month",
            "order_value",
            "invoice_value",
        ]
    ].melt(
        id_vars=["Month"],
        var_name="Metric",
        value_name="Value",
    )

    value_data["Metric"] = value_data[
        "Metric"
    ].replace(
        {
            "order_value": "Order Value",
            "invoice_value": "Invoice Value",
        }
    )

    value_chart = (
        alt.Chart(value_data)
        .mark_line(
            point=True,
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "Month:N",
                sort=available_months,
            ),
            y=alt.Y(
                "Value:Q",
                title="Value",
            ),
            color=alt.Color(
                "Metric:N"
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


    # --------------------------------------------------------
    # SALE LOSS TREND
    # --------------------------------------------------------

    if "sale_loss" in monthly.columns:

        st.markdown(
            '<div class="section-title">Sale Loss MOM</div>',
            unsafe_allow_html=True,
        )

        sale_chart = (
            alt.Chart(monthly)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Month:N",
                    sort=available_months,
                ),
                y=alt.Y(
                    "sale_loss:Q",
                    title="Sale Loss",
                ),
                tooltip=[
                    "Month:N",
                    alt.Tooltip(
                        "sale_loss:Q",
                        format=",.0f",
                    ),
                ],
            )
            .properties(
                height=320
            )
        )

        st.altair_chart(
            sale_chart,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # MOM IMPROVEMENT / DETERIORATION
    # --------------------------------------------------------

    if len(monthly) >= 2:

        latest = monthly.iloc[-1]
        previous = monthly.iloc[-2]

        st.markdown(
            '<div class="section-title">Latest Month vs Previous Month</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)

        m1.metric(
            "FR % Qty",
            format_percent(
                latest.get("fr_qty")
            ),
            delta_text(
                latest.get("fr_qty"),
                previous.get("fr_qty"),
                " pp",
            ),
        )

        m2.metric(
            "FR % Value",
            format_percent(
                latest.get("fr_value")
            ),
            delta_text(
                latest.get("fr_value"),
                previous.get("fr_value"),
                " pp",
            ),
        )

        m3.metric(
            "Pending Qty",
            format_number(
                latest.get("pending_qty")
            ),
            delta_text(
                latest.get("pending_qty"),
                previous.get("pending_qty"),
            ),
        )

        m4.metric(
            "Sale Loss",
            format_value(
                latest.get("sale_loss")
            ),
            delta_text(
                latest.get("sale_loss"),
                previous.get("sale_loss"),
            ),
        )


# ============================================================
# TAB 2 — CHANNEL / CHAIN
# ============================================================

with tab_chain:

    st.markdown(
        '<div class="section-title">Channel / Chain Performance</div>',
        unsafe_allow_html=True,
    )

    chain_col = resolve_col(
        CONFIG["channel"],
        filtered.columns,
    )

    if not chain_col:

        st.warning(
            "Channel column is not available."
        )

    else:

        chain_month = aggregate_data(
            filtered,
            [
                "Month",
                chain_col,
            ],
        )

        # --------------------------------------------
        # FR TREND BY CHANNEL
        # --------------------------------------------

        st.markdown(
            "#### Fill Rate Trend by Channel"
        )

        chain_chart = (
            alt.Chart(chain_month)
            .mark_line(
                point=True,
                strokeWidth=2.5,
            )
            .encode(
                x=alt.X(
                    "Month:N",
                    sort=available_months,
                ),
                y=alt.Y(
                    "fr_qty:Q",
                    title="FR % Qty",
                    scale=alt.Scale(
                        zero=False
                    ),
                ),
                color=alt.Color(
                    f"{chain_col}:N",
                    title="Channel",
                ),
                tooltip=[
                    "Month:N",
                    f"{chain_col}:N",
                    alt.Tooltip(
                        "fr_qty:Q",
                        title="FR Qty %",
                        format=".1f",
                    ),
                    alt.Tooltip(
                        "fr_value:Q",
                        title="FR Value %",
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
                height=430
            )
        )

        st.altair_chart(
            chain_chart,
            use_container_width=True,
        )


        # --------------------------------------------
        # LATEST MONTH TABLE
        # --------------------------------------------

        latest_month = max(
            selected_months,
            key=month_sort_key,
        )

        latest_chain = chain_month[
            chain_month["Month"]
            == latest_month
        ].copy()

        latest_chain = latest_chain.sort_values(
            "fr_qty"
        )

        columns_to_show = [
            chain_col,
            "order_qty",
            "invoice_qty",
            "fr_qty",
            "fr_value",
            "pending_qty",
            "order_value",
            "invoice_value",
            "pending_value",
            "sale_loss",
            "orders",
            "customers",
        ]

        columns_to_show = [
            c
            for c in columns_to_show
            if c in latest_chain.columns
        ]

        chain_display = latest_chain[
            columns_to_show
        ].copy()

        chain_display = chain_display.rename(
            columns={
                chain_col: "Channel",
                "order_qty": "Order Qty",
                "invoice_qty": "Invoice Qty",
                "fr_qty": "FR % Qty",
                "fr_value": "FR % Value",
                "pending_qty": "Pending Qty",
                "order_value": "Order Value",
                "invoice_value": "Invoice Value",
                "pending_value": "Pending Value",
                "sale_loss": "Sale Loss",
                "orders": "Orders",
                "customers": "Customers",
            }
        )

        st.markdown(
            f"#### {latest_month} Channel Detail"
        )

        st.dataframe(
            chain_display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TAB 3 — CUSTOMER
# ============================================================

with tab_customer:

    st.markdown(
        '<div class="section-title">Customer Performance</div>',
        unsafe_allow_html=True,
    )

    customer_col = resolve_col(
        CONFIG["customer"],
        filtered.columns,
    )

    if customer_col:

        customer_search = st.text_input(
            "🔍 Search Customer",
            key="customer_search",
        )

        customer_data = filtered.copy()

        if customer_search:

            customer_data = customer_data[
                customer_data[
                    customer_col
                ]
                .astype(str)
                .str.contains(
                    customer_search,
                    case=False,
                    na=False,
                )
            ]

        customer_summary = aggregate_data(
            customer_data,
            [customer_col],
        )

        customer_summary = customer_summary.sort_values(
            "fr_qty",
            ascending=True,
        )

        st.caption(
            f"{len(customer_summary):,} customers"
        )

        customer_columns = [
            customer_col,
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
            "avg_actual_tat",
            "avg_standard_tat",
            "avg_variance",
        ]

        customer_columns = [
            c
            for c in customer_columns
            if c in customer_summary.columns
        ]

        customer_display = customer_summary[
            customer_columns
        ].rename(
            columns={
                customer_col: "Customer",
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
                "avg_actual_tat": "Avg Actual TAT",
                "avg_standard_tat": "Avg Standard TAT",
                "avg_variance": "Avg Variance",
            }
        )

        st.dataframe(
            customer_display,
            use_container_width=True,
            hide_index=True,
            height=550,
        )


# ============================================================
# TAB 4 — CATEGORY
# ============================================================

with tab_category:

    st.markdown(
        '<div class="section-title">Category Performance</div>',
        unsafe_allow_html=True,
    )

    category_col = resolve_col(
        CONFIG["category"],
        filtered.columns,
    )

    if category_col:

        category_summary = aggregate_data(
            filtered,
            [
                category_col,
            ],
        )

        category_summary = category_summary.sort_values(
            "fr_qty"
        )

        category_display = category_summary.rename(
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
                "avg_actual_tat": "Avg Actual TAT",
                "avg_standard_tat": "Avg Standard TAT",
                "avg_variance": "Avg Variance",
            }
        )

        st.dataframe(
            category_display,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        # Category FR chart

        st.markdown(
            "#### Category Fill Rate"
        )

        category_chart = (
            alt.Chart(category_summary)
            .mark_bar()
            .encode(
                x=alt.X(
                    f"{category_col}:N",
                    sort="-y",
                    title="Category",
                    axis=alt.Axis(
                        labelAngle=-40
                    ),
                ),
                y=alt.Y(
                    "fr_qty:Q",
                    title="FR % Qty",
                ),
                tooltip=[
                    f"{category_col}:N",
                    alt.Tooltip(
                        "fr_qty:Q",
                        format=".1f",
                    ),
                    alt.Tooltip(
                        "fr_value:Q",
                        format=".1f",
                    ),
                ],
            )
            .properties(
                height=400
            )
        )

        st.altair_chart(
            category_chart,
            use_container_width=True,
        )


# ============================================================
# TAB 5 — TAT & SLA
# ============================================================

with tab_tat:

    st.markdown(
        '<div class="section-title">TAT & SLA Analysis</div>',
        unsafe_allow_html=True,
    )

    tat_col = resolve_col(
        CONFIG["actual_delivery_days"],
        filtered.columns,
    )

    standard_tat_col = resolve_col(
        CONFIG["standard_tat"],
        filtered.columns,
    )

    variance_col = resolve_col(
        CONFIG["variance"],
        filtered.columns,
    )

    if tat_col:

        tat_df = filtered.copy()

        tat_df["__Actual_TAT"] = clean_numeric(
            tat_df[tat_col]
        )

        tat_month = (
            tat_df.groupby(
                "Month",
                dropna=False,
            )
            .agg(
                avg_actual_tat=(
                    "__Actual_TAT",
                    "mean",
                )
            )
            .reset_index()
        )

        if standard_tat_col:

            tat_df["__Standard_TAT"] = clean_numeric(
                tat_df[standard_tat_col]
            )

            standard_month = (
                tat_df.groupby(
                    "Month",
                    dropna=False,
                )
                .agg(
                    avg_standard_tat=(
                        "__Standard_TAT",
                        "mean",
                    )
                )
                .reset_index()
            )

            tat_month = tat_month.merge(
                standard_month,
                on="Month",
                how="left",
            )

        st.markdown(
            "#### Actual TAT vs Standard TAT"
        )

        tat_long_columns = [
            "Month",
            "avg_actual_tat",
        ]

        if "avg_standard_tat" in tat_month.columns:
            tat_long_columns.append(
                "avg_standard_tat"
            )

        tat_long = tat_month[
            tat_long_columns
        ].melt(
            id_vars=["Month"],
            var_name="Metric",
            value_name="Days",
        )

        tat_long["Metric"] = tat_long[
            "Metric"
        ].replace(
            {
                "avg_actual_tat": "Actual TAT",
                "avg_standard_tat": "Standard TAT",
            }
        )

        tat_chart = (
            alt.Chart(tat_long)
            .mark_line(
                point=True,
                strokeWidth=3,
            )
            .encode(
                x=alt.X(
                    "Month:N",
                    sort=available_months,
                ),
                y=alt.Y(
                    "Days:Q",
                    title="Days",
                ),
                color=alt.Color(
                    "Metric:N"
                ),
                tooltip=[
                    "Month:N",
                    "Metric:N",
                    alt.Tooltip(
                        "Days:Q",
                        format=".1f",
                    ),
                ],
            )
            .properties(
                height=350
            )
        )

        st.altair_chart(
            tat_chart,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # TAT BUCKET
    # --------------------------------------------------------

    bucket_col = resolve_col(
        CONFIG["otd_bucket"],
        filtered.columns,
    )

    if bucket_col:

        bucket_summary = (
            filtered.groupby(
                bucket_col,
                dropna=False,
            )
            .size()
            .reset_index(
                name="Orders"
            )
            .sort_values(
                "Orders",
                ascending=False,
            )
        )

        st.markdown(
            "#### OTD Bucket Distribution"
        )

        bucket_chart = (
            alt.Chart(bucket_summary)
            .mark_bar()
            .encode(
                x=alt.X(
                    f"{bucket_col}:N",
                    title="OTD Bucket",
                    sort="-y",
                ),
                y=alt.Y(
                    "Orders:Q",
                    title="Orders",
                ),
                tooltip=[
                    f"{bucket_col}:N",
                    "Orders:Q",
                ],
            )
            .properties(
                height=350
            )
        )

        st.altair_chart(
            bucket_chart,
            use_container_width=True,
        )


    # --------------------------------------------------------
    # DELIVERY STATUS
    # --------------------------------------------------------

    delivery_col = resolve_col(
        CONFIG["delivery_status"],
        filtered.columns,
    )

    if delivery_col:

        delivery_summary = (
            filtered.groupby(
                delivery_col,
                dropna=False,
            )
            .size()
            .reset_index(
                name="Orders"
            )
            .sort_values(
                "Orders",
                ascending=False,
            )
        )

        st.markdown(
            "#### Delivery Status"
        )

        st.dataframe(
            delivery_summary,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TAB 6 — DETAILED ORDERS
# ============================================================

with tab_orders:

    st.markdown(
        '<div class="section-title">Detailed Operational View</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "All detailed source-level information is retained here."
    )

    search_text = st.text_input(
        "🔍 Search Order ID / Customer / DB Code / Invoice / AWB / SKU / Remarks",
        key="detail_search",
    )

    detail_df = filtered.copy()

    if search_text:

        search_columns = [
            CONFIG["order_id"],
            CONFIG["external_document"],
            CONFIG["customer"],
            CONFIG["db_code"],
            CONFIG["invoice_number"],
            CONFIG["awb"],
            CONFIG["category"],
            CONFIG["final_remarks"],
            CONFIG["wh_remarks"],
            CONFIG["logistics_remarks"],
            CONFIG["sro"],
        ]

        search_columns = [
            resolve_col(
                c,
                detail_df.columns,
            )
            for c in search_columns
        ]

        search_columns = [
            c
            for c in search_columns
            if c is not None
        ]

        mask = pd.Series(
            False,
            index=detail_df.index,
        )

        for col in search_columns:

            mask = (
                mask
                |
                detail_df[col]
                .astype(str)
                .str.contains(
                    search_text,
                    case=False,
                    na=False,
                )
            )

        detail_df = detail_df[
            mask
        ]


    # --------------------------------------------------------
    # DETAIL COLUMN PICKER
    # --------------------------------------------------------

    detail_candidates = [
        "Month",

        CONFIG["order_received"],
        CONFIG["order_upload"],
        CONFIG["wh_receiving"],

        CONFIG["channel"],
        CONFIG["zone"],
        CONFIG["db_code"],
        CONFIG["customer"],

        CONFIG["order_category"],
        CONFIG["category"],

        CONFIG["order_id"],
        CONFIG["external_document"],

        CONFIG["order_qty"],
        CONFIG["order_value"],

        CONFIG["wh_remarks"],
        CONFIG["order_punch"],

        CONFIG["invoice_date"],
        CONFIG["invoice_qty"],
        CONFIG["invoice_value"],
        CONFIG["invoice_number"],
        CONFIG["invoice_time"],

        CONFIG["fr_value"],
        CONFIG["fr_qty"],

        CONFIG["dispatch_date"],
        CONFIG["awb"],
        CONFIG["courier"],
        CONFIG["mode"],
        CONFIG["box"],
        CONFIG["weight"],

        CONFIG["pin_code"],
        CONFIG["delivery_status"],
        CONFIG["delivery_date"],

        CONFIG["dispatched_sla"],
        CONFIG["logistics_sla"],

        CONFIG["logistics_remarks"],

        CONFIG["sro"],
        CONFIG["ageing"],
        CONFIG["standard_tat"],

        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],

        CONFIG["dispatch_to_delivery"],
        CONFIG["otd_bucket"],

        CONFIG["omt_remarks"],
        CONFIG["type"],
        CONFIG["name"],
        CONFIG["ho_remarks"],
        CONFIG["final_remarks"],

        CONFIG["otw_days"],
        CONFIG["invoice_days"],
        CONFIG["dispatch_days"],
        CONFIG["actual_delivery_days"],
        CONFIG["variance"],

        CONFIG["order_value_lacs"],
        CONFIG["invoice_value_lacs"],
        CONFIG["sale_loss"],
    ]

    available_detail_columns = []

    for requested in detail_candidates:

        if requested == "Month":

            available_detail_columns.append(
                "Month"
            )

            continue

        actual = resolve_col(
            requested,
            detail_df.columns,
        )

        if actual and actual not in available_detail_columns:

            available_detail_columns.append(
                actual
            )


    # Derived metrics
    for derived in [
        "__FR_QTY",
        "__FR_VALUE",
        "__Pending_Qty",
        "__Pending_Value",
    ]:

        if derived in detail_df.columns:
            available_detail_columns.append(
                derived
            )


    # --------------------------------------------------------
    # COLUMN SELECTION
    # --------------------------------------------------------

    with st.expander(
        "⚙️ Columns to show",
        expanded=False,
    ):

        default_detail_columns = [
            c
            for c in available_detail_columns
            if c in [
                "Month",
                CONFIG["order_received"],
                CONFIG["wh_receiving"],
                CONFIG["channel"],
                CONFIG["zone"],
                CONFIG["db_code"],
                CONFIG["customer"],
                CONFIG["category"],
                CONFIG["order_id"],
                CONFIG["order_qty"],
                CONFIG["order_value"],
                CONFIG["invoice_date"],
                CONFIG["invoice_qty"],
                CONFIG["invoice_value"],
                CONFIG["invoice_number"],
                CONFIG["fr_qty"],
                CONFIG["fr_value"],
                CONFIG["dispatch_date"],
                CONFIG["delivery_status"],
                CONFIG["delivery_date"],
                CONFIG["standard_tat"],
                CONFIG["actual_delivery_days"],
                CONFIG["variance"],
                CONFIG["sale_loss"],
                CONFIG["final_remarks"],
            ]
        ]

        selected_detail_columns = st.multiselect(
            "Select columns",
            options=available_detail_columns,
            default=default_detail_columns,
        )


    if not selected_detail_columns:

        selected_detail_columns = available_detail_columns


    detail_display = detail_df[
        selected_detail_columns
    ].copy()


    # --------------------------------------------------------
    # FRIENDLY NAMES FOR DERIVED FIELDS
    # --------------------------------------------------------

    detail_display = detail_display.rename(
        columns={
            "__FR_QTY": "Calculated FR % Qty",
            "__FR_VALUE": "Calculated FR % Value",
            "__Pending_Qty": "Calculated Pending Qty",
            "__Pending_Value": "Calculated Pending Value",
        }
    )


    # --------------------------------------------------------
    # DATE FORMATTING
    # --------------------------------------------------------

    date_headers = [
        CONFIG["order_received"],
        CONFIG["order_upload"],
        CONFIG["wh_receiving"],
        CONFIG["invoice_date"],
        CONFIG["dispatch_date"],
        CONFIG["delivery_date"],
    ]

    for col in date_headers:

        if col in detail_display.columns:

            detail_display[col] = pd.to_datetime(
                detail_display[col],
                errors="coerce",
            ).dt.strftime(
                "%d-%m-%Y"
            )


    # --------------------------------------------------------
    # ORDER DETAILS TABLE
    # --------------------------------------------------------

    st.caption(
        f"{len(detail_display):,} detailed rows"
    )

    st.dataframe(
        detail_display,
        use_container_width=True,
        hide_index=True,
        height=620,
    )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    csv_bytes = detail_display.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    st.download_button(
        "⬇️ Download Filtered Details",
        data=csv_bytes,
        file_name="MOM_Filtered_Order_Details.csv",
        mime="text/csv",
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    f"""
    <div class="small-muted">
        SharePoint source: SHAREPOINT_EXCEL_URL
        &nbsp; | &nbsp;
        Monthly sheets: {", ".join(loaded_sheets)}
        &nbsp; | &nbsp;
        Filtered rows: {len(filtered):,}
        &nbsp; | &nbsp;
        Refreshed: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}
    </div>
    """,
    unsafe_allow_html=True,
)
