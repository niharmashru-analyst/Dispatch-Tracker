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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = {

    # --------------------------------------------------------
    # SHAREPOINT
    # --------------------------------------------------------

    "sharepoint_secret": "SHAREPOINT_EXCEL_URL",

    # --------------------------------------------------------
    # BASIC
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

    "order_id": "Order Id",
    "external_document": "External Document No.",

    "order_qty": "Order Qty",
    "order_value": "Order Value",

    "wh_remarks": "Wh. Remarks",
    "order_punch_time": "Order Punch time",

    # --------------------------------------------------------
    # INVOICE
    # --------------------------------------------------------

    "invoice_date": "Invoice Date",
    "invoice_qty": "Invoice Qty",
    "invoice_value": "Invoice Value",
    "invoice_number": "InvoiceNumber",
    "invoice_time": "Invoice Time",

    # --------------------------------------------------------
    # FILL RATE
    # --------------------------------------------------------

    "fr_value": "Over all FR % (Value)",
    "fr_qty": "Over all FR % (Qty)",

    # --------------------------------------------------------
    # DISPATCH
    # --------------------------------------------------------

    "dispatch_date": "Dispatch Date",
    "awb": "AWB NUMBER",
    "courier": "COURIER",
    "mode": "Mode",
    "box": "Box",
    "weight": "Weight",

    # --------------------------------------------------------
    # DELIVERY
    # --------------------------------------------------------

    "pin_code": "Pin Code",
    "delivery_status": "Delivery Status",
    "delivery_date": "Delivery Date",

    # --------------------------------------------------------
    # SLA / TAT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # REMARKS / OTHER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # COMMERCIAL
    # --------------------------------------------------------

    "order_value_lacs": "Order Value Lacs",
    "invoice_value_lacs": "Invoice Value Lacs",
    "sale_loss": "Sale Loss",
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
# WHITE THEME
# ============================================================

C_BG = "#F4F6FA"
C_CARD = "#FFFFFF"
C_BORDER = "#E1E5EB"
C_TEXT = "#132238"
C_MUTED = "#6B7280"
C_BLUE = "#4C6FFF"


st.markdown(
    f"""
    <style>

    .stApp {{
        background: {C_BG};
    }}

    h1, h2, h3, h4 {{
        color: {C_TEXT} !important;
    }}

    p, label {{
        color: {C_TEXT};
    }}

    /* =====================================================
       KPI CARDS
       ===================================================== */

    div[data-testid="stMetric"] {{
        background: {C_CARD};
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
        min-height: 112px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {C_TEXT} !important;
        font-size: 14px !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {C_TEXT} !important;
        font-weight: 750 !important;
    }}

    div[data-testid="stMetricDelta"] {{
        font-weight: 600 !important;
    }}

    /* =====================================================
       SECTION TITLE
       ===================================================== */

    .section-title {{
        font-size: 20px;
        font-weight: 750;
        color: {C_TEXT};
        margin-top: 22px;
        margin-bottom: 10px;
    }}

    .dashboard-subtitle {{
        color: {C_MUTED};
        font-size: 14px;
        margin-top: -8px;
        margin-bottom: 16px;
    }}

    /* =====================================================
       EXECUTIVE HEADER
       ===================================================== */

    .executive-header {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    }}

    .executive-title {{
        color: {C_TEXT};
        font-size: 22px;
        font-weight: 750;
    }}

    .executive-subtitle {{
        color: {C_MUTED};
        font-size: 13px;
        margin-top: 3px;
    }}

    /* =====================================================
       CUSTOMER TABLE
       ===================================================== */

    .st-key-customer_table {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    .st-key-customer_table
    [data-testid="stHorizontalBlock"] {{
        border-bottom: 1px solid #E8EBF0;
        padding: 4px 6px;
        align-items: center;
        background: #FFFFFF;
    }}

    .st-key-customer_table
    [data-testid="stHorizontalBlock"]:first-child {{
        background: #F8F9FC;
    }}

    .st-key-customer_table
    div.stButton > button {{
        background: transparent;
        border: none;
        box-shadow: none;
        color: {C_TEXT};
        border-radius: 5px;
    }}

    .st-key-customer_table
    div.stButton > button:hover {{
        background: #F1F4FA;
        color: {C_BLUE};
    }}

    /* =====================================================
       NORMAL BUTTONS
       ===================================================== */

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

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def resolve_col(target, columns):

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
        return MONTH_ORDER.index(
            str(month)
        )
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
        return (
            f"₹ {value / 10_000_000:.2f} Cr"
        )

    if abs(value) >= 100_000:
        return (
            f"₹ {value / 100_000:.2f} L"
        )

    return f"₹ {value:,.0f}"


def format_percent(value):

    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.1f}%"


def safe_ratio(numerator, denominator):

    try:

        if denominator == 0:
            return np.nan

        return numerator / denominator * 100

    except Exception:

        return np.nan


def center(container, text):

    container.markdown(
        f"""
        <div style="
            text-align:center;
            color:{C_TEXT};
            font-size:14px;
            white-space:nowrap;
        ">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SHAREPOINT
# ============================================================

def get_sharepoint_download_url(url):

    if "download=1" in url.lower():
        return url

    separator = "&" if "?" in url else "?"

    return (
        f"{url}"
        f"{separator}"
        f"download=1"
    )


@st.cache_data(
    ttl=300,
    show_spinner="Fetching latest Excel file..."
)
def get_workbook(url):

    response = requests.get(
        get_sharepoint_download_url(url),
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
            "SharePoint returned a login/HTML page "
            "instead of the Excel workbook."
        )

    workbook = pd.read_excel(
        io.BytesIO(
            response.content
        ),
        sheet_name=None,
        engine="openpyxl",
    )

    return workbook


# ============================================================
# LOAD MONTHLY SHEETS
# ============================================================

@st.cache_data(
    ttl=300,
    show_spinner="Combining monthly sheets..."
)
def load_data(url):

    workbook = get_workbook(url)

    frames = []
    sheets_used = []

    for sheet_name, raw_df in workbook.items():

        sheet_name = str(
            sheet_name
        ).strip()

        # Only monthly sheets
        if sheet_name not in MONTH_ORDER:
            continue

        if raw_df is None or raw_df.empty:
            continue

        df = raw_df.copy()

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        # Sheet name controls MOM month
        df["__Dashboard_Month"] = (
            sheet_name
        )

        frames.append(df)

        sheets_used.append(
            sheet_name
        )

    if not frames:

        raise ValueError(
            "No monthly sheets found. "
            "Expected Apr, May, Jun, Jul, Aug."
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

        CONFIG["fr_qty"],
        CONFIG["fr_value"],

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
    # DATE COLUMNS
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
    # AUTHORITATIVE MONTH
    # --------------------------------------------------------

    combined["Month"] = (
        combined[
            "__Dashboard_Month"
        ]
    )

    combined["__month_sort"] = (
        combined["Month"]
        .apply(month_sort_key)
    )

    combined = (
        combined
        .sort_values(
            "__month_sort"
        )
        .reset_index(
            drop=True
        )
    )

    return combined, sheets_used


# ============================================================
# DERIVED METRICS
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

    # --------------------------------------------------------
    # Calculated FR
    # --------------------------------------------------------

    if oq and iq:

        df["__Calculated_FR_Qty"] = (
            np.where(
                df[oq] != 0,
                df[iq] / df[oq] * 100,
                np.nan,
            )
        )

    else:

        df["__Calculated_FR_Qty"] = np.nan

    if ov and iv:

        df["__Calculated_FR_Value"] = (
            np.where(
                df[ov] != 0,
                df[iv] / df[ov] * 100,
                np.nan,
            )
        )

    else:

        df["__Calculated_FR_Value"] = np.nan

    # --------------------------------------------------------
    # Official FR
    # --------------------------------------------------------

    frq = resolve_col(
        CONFIG["fr_qty"],
        df.columns,
    )

    frv = resolve_col(
        CONFIG["fr_value"],
        df.columns,
    )

    if frq:

        df["__FR_Qty"] = clean_numeric(
            df[frq]
        )

    else:

        df["__FR_Qty"] = (
            df["__Calculated_FR_Qty"]
        )

    if frv:

        df["__FR_Value"] = clean_numeric(
            df[frv]
        )

    else:

        df["__FR_Value"] = (
            df["__Calculated_FR_Value"]
        )

    # --------------------------------------------------------
    # Pending
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CLEAN TAT
    #
    # IMPORTANT:
    # Invalid values such as 172472.1 are removed.
    # Normal operational TAT is expected to be between
    # 0 and 365 days.
    # --------------------------------------------------------

    tat_col = resolve_col(
        CONFIG["actual_delivery_days"],
        df.columns,
    )

    if tat_col:

        df["__Valid_TAT"] = clean_numeric(
            df[tat_col]
        )

        df.loc[
            (
                df["__Valid_TAT"] < 0
            )
            |
            (
                df["__Valid_TAT"] > 365
            ),
            "__Valid_TAT",
        ] = np.nan

    else:

        df["__Valid_TAT"] = np.nan

    return df


# ============================================================
# MONTHLY AGGREGATION
# ============================================================

def monthly_summary(df):

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
        .agg(
            **aggregation
        )
        .reset_index()
    )

    if (
        "order_qty" in result.columns
        and "invoice_qty"
        in result.columns
    ):

        result["fr_qty"] = np.where(
            result["order_qty"] != 0,
            (
                result["invoice_qty"]
                / result["order_qty"]
                * 100
            ),
            np.nan,
        )

        result["pending_qty"] = (
            result["order_qty"]
            - result["invoice_qty"]
        )

    if (
        "order_value" in result.columns
        and "invoice_value"
        in result.columns
    ):

        result["fr_value"] = np.where(
            result["order_value"] != 0,
            (
                result["invoice_value"]
                / result["order_value"]
                * 100
            ),
            np.nan,
        )

        result["pending_value"] = (
            result["order_value"]
            - result["invoice_value"]
        )

    result["__sort"] = (
        result["Month"]
        .apply(month_sort_key)
    )

    return (
        result
        .sort_values("__sort")
        .drop(columns="__sort")
        .reset_index(drop=True)
    )


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def customer_summary(df):

    customer_col = CONFIG["customer"]

    aggregation = {

        "order_qty": (
            CONFIG["order_qty"],
            "sum",
        ),

        "invoice_qty": (
            CONFIG["invoice_qty"],
            "sum",
        ),
    }

    if CONFIG["order_id"] in df.columns:

        aggregation[
            "order_count"
        ] = (
            CONFIG["order_id"],
            "nunique",
        )

    if CONFIG["invoice_number"] in df.columns:

        aggregation[
            "invoice_count"
        ] = (
            CONFIG["invoice_number"],
            lambda x:
            x.dropna()
            .astype(str)
            .nunique(),
        )

    if CONFIG["sale_loss"] in df.columns:

        aggregation[
            "sale_loss"
        ] = (
            CONFIG["sale_loss"],
            "sum",
        )

    # IMPORTANT:
    # Use cleaned TAT, not raw Actual Deli. Days.
    aggregation[
        "tat_avg"
    ] = (
        "__Valid_TAT",
        "mean",
    )

    result = (
        df.groupby(
            customer_col,
            dropna=False,
        )
        .agg(
            **aggregation
        )
        .reset_index()
    )

    result["fill_rate"] = np.where(
        result["order_qty"] != 0,
        (
            result["invoice_qty"]
            / result["order_qty"]
            * 100
        ),
        np.nan,
    )

    return result


# ============================================================
# CUSTOMER DETAILS DIALOG
# ============================================================

@st.dialog(
    "Customer Order Details",
    width="large",
)
def show_customer_details(
    customer_name,
    df,
):

    rows = df[
        df[
            CONFIG["customer"]
        ]
        .astype(str)
        ==
        str(customer_name)
    ].copy()

    if rows.empty:

        st.warning(
            "No order details found."
        )

        return

    # --------------------------------------------------------
    # Valid customer TAT
    # --------------------------------------------------------

    rows["TAT"] = (
        rows["__Valid_TAT"]
    )

    # --------------------------------------------------------
    # Fill Rate
    # --------------------------------------------------------

    rows["Fill Rate"] = np.where(
        rows[
            CONFIG["order_qty"]
        ] != 0,
        (
            rows[
                CONFIG["invoice_qty"]
            ]
            /
            rows[
                CONFIG["order_qty"]
            ]
            * 100
        ),
        np.nan,
    )

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    desired_columns = [

        CONFIG["wh_receiving_date"],

        CONFIG["customer"],
        CONFIG["db_code"],
        CONFIG["category"],

        CONFIG["order_id"],
        CONFIG["external_document"],

        CONFIG["order_qty"],
        CONFIG["order_value"],

        CONFIG["invoice_date"],
        CONFIG["invoice_number"],
        CONFIG["invoice_qty"],
        CONFIG["invoice_value"],

        "Fill Rate",

        CONFIG["sale_loss"],

        CONFIG["dispatch_date"],
        CONFIG["awb"],
        CONFIG["courier"],
        CONFIG["mode"],

        CONFIG["delivery_status"],
        CONFIG["delivery_date"],

        "TAT",

        CONFIG["standard_tat"],
        CONFIG["variance"],

        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],

        CONFIG["dispatch_to_delivery"],
        CONFIG["otd_bucket"],

        CONFIG["wh_remarks"],
        CONFIG["wh_remark"],
        CONFIG["logistics_remarks"],
        CONFIG["ho_remarks"],
        CONFIG["final_remarks"],
    ]

    selected = []

    seen = set()

    for col in desired_columns:

        if col in [
            "Fill Rate",
            "TAT",
        ]:

            selected.append(col)

            continue

        actual = resolve_col(
            col,
            rows.columns,
        )

        if (
            actual
            and actual not in seen
        ):

            selected.append(
                actual
            )

            seen.add(actual)

    display = rows[
        selected
    ].copy()

    # --------------------------------------------------------
    # Sort newest first
    # --------------------------------------------------------

    wh_date = resolve_col(
        CONFIG["wh_receiving_date"],
        display.columns,
    )

    if wh_date:

        display = (
            display
            .sort_values(
                wh_date,
                ascending=False,
                na_position="last",
            )
        )

    # --------------------------------------------------------
    # Format
    # --------------------------------------------------------

    for col in [
        CONFIG["order_received_date"],
        CONFIG["order_upload_date"],
        CONFIG["wh_receiving_date"],
        CONFIG["invoice_date"],
        CONFIG["dispatch_date"],
        CONFIG["delivery_date"],
    ]:

        if col in display.columns:

            display[col] = (
                pd.to_datetime(
                    display[col],
                    errors="coerce",
                )
                .dt.strftime(
                    "%d-%m-%Y"
                )
            )

    st.caption(
        f"{len(display):,} order rows for "
        f"**{customer_name}**"
    )

    column_config = {}

    if "Fill Rate" in display.columns:

        column_config[
            "Fill Rate"
        ] = st.column_config.NumberColumn(
            "Fill Rate",
            format="%.1f%%",
        )

    if "TAT" in display.columns:

        column_config[
            "TAT"
        ] = st.column_config.NumberColumn(
            "TAT",
            format="%.1f",
        )

    if CONFIG["sale_loss"] in display.columns:

        column_config[
            CONFIG["sale_loss"]
        ] = st.column_config.NumberColumn(
            CONFIG["sale_loss"],
            format="₹ %.2f",
        )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=550,
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
            Month-on-Month performance with customer-level
            operational drill-down
        </div>

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
        "SHAREPOINT_EXCEL_URL is not configured."
    )

    st.stop()


# ============================================================
# REFRESH
# ============================================================

refresh_col, blank_col = st.columns(
    [1, 8]
)

with refresh_col:

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        get_workbook.clear()
        load_data.clear()

        st.rerun()


# ============================================================
# LOAD
# ============================================================

try:

    df, sheets_used = load_data(
        sharepoint_url
    )

    df = add_derived_metrics(
        df
    )

except Exception as e:

    st.error(
        f"Could not load the Excel file: {e}"
    )

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [

    CONFIG["customer"],
    CONFIG["order_qty"],
    CONFIG["invoice_qty"],
    CONFIG["order_value"],
    CONFIG["invoice_value"],
    CONFIG["order_id"],
]

missing = []

for col in required_columns:

    if resolve_col(
        col,
        df.columns,
    ) is None:

        missing.append(col)


if missing:

    st.error(
        "Missing required columns:"
    )

    for col in missing:
        st.write(
            f"- {col}"
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

    # --------------------------------------------------------
    # Month
    # --------------------------------------------------------

    with f1:

        available_months = sorted(
            sheets_used,
            key=month_sort_key,
        )

        selected_months = st.multiselect(
            "Month",
            available_months,
            default=available_months,
        )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    with f2:

        name_options = sorted(
            df[
                CONFIG["name"]
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_names = st.multiselect(
            "Name",
            name_options,
        )

    # --------------------------------------------------------
    # Category
    # --------------------------------------------------------

    with f3:

        category_options = sorted(
            df[
                CONFIG["category"]
            ]
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

    # --------------------------------------------------------
    # Channel
    # --------------------------------------------------------

    with f4:

        channel_options = sorted(
            df[
                CONFIG["channel"]
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_channels = st.multiselect(
            "Channel",
            channel_options,
        )

    # --------------------------------------------------------
    # Zone
    # --------------------------------------------------------

    with f5:

        zone_options = sorted(
            df[
                CONFIG["zone"]
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_zones = st.multiselect(
            "Zone",
            zone_options,
        )

    # --------------------------------------------------------
    # Customer
    # --------------------------------------------------------

    with f6:

        customer_options = sorted(
            df[
                CONFIG["customer"]
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        selected_customers = st.multiselect(
            "Customer",
            customer_options,
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
        .isin(
            selected_names
        )
    ]

if selected_categories:

    filtered = filtered[
        filtered[
            CONFIG["category"]
        ]
        .astype(str)
        .isin(
            selected_categories
        )
    ]

if selected_channels:

    filtered = filtered[
        filtered[
            CONFIG["channel"]
        ]
        .astype(str)
        .isin(
            selected_channels
        )
    ]

if selected_zones:

    filtered = filtered[
        filtered[
            CONFIG["zone"]
        ]
        .astype(str)
        .isin(
            selected_zones
        )
    ]

if selected_customers:

    filtered = filtered[
        filtered[
            CONFIG["customer"]
        ]
        .astype(str)
        .isin(
            selected_customers
        )
    ]


if filtered.empty:

    st.warning(
        "No records match the selected filters."
    )

    st.stop()


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Latest / previous month
# ------------------------------------------------------------

selected_sorted = sorted(
    filtered[
        "Month"
    ]
    .dropna()
    .unique(),
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

current_df = (
    filtered[
        filtered["Month"]
        == latest_month
    ]
    if latest_month
    else filtered
)

previous_df = (
    filtered[
        filtered["Month"]
        == previous_month
    ]
    if previous_month
    else pd.DataFrame()
)


def get_metrics(data):

    order_qty = data[
        CONFIG["order_qty"]
    ].sum()

    invoice_qty = data[
        CONFIG["invoice_qty"]
    ].sum()

    order_value = data[
        CONFIG["order_value"]
    ].sum()

    invoice_value = data[
        CONFIG["invoice_value"]
    ].sum()

    sale_loss = data[
        CONFIG["sale_loss"]
    ].sum()

    fr_qty = safe_ratio(
        invoice_qty,
        order_qty,
    )

    fr_value = safe_ratio(
        invoice_value,
        order_value,
    )

    return {

        "order_qty":
            order_qty,

        "invoice_qty":
            invoice_qty,

        "fr_qty":
            fr_qty,

        "pending_qty":
            order_qty - invoice_qty,

        "order_value":
            order_value,

        "invoice_value":
            invoice_value,

        "fr_value":
            fr_value,

        "sale_loss":
            sale_loss,
    }


current = get_metrics(
    current_df
)

previous = (
    get_metrics(
        previous_df
    )
    if not previous_df.empty
    else None
)


# ============================================================
# DELTA FUNCTIONS
# ============================================================

def number_delta(
    current_value,
    previous_value,
):

    if previous_value is None:
        return None

    difference = (
        current_value
        - previous_value
    )

    sign = (
        "+"
        if difference > 0
        else ""
    )

    return (
        f"{sign}"
        f"{difference:,.0f}"
    )


def percent_delta(
    current_value,
    previous_value,
):

    if previous_value is None:
        return None

    difference = (
        current_value
        - previous_value
    )

    sign = (
        "+"
        if difference > 0
        else ""
    )

    return (
        f"{sign}"
        f"{difference:.1f}%"
    )


def currency_delta(
    current_value,
    previous_value,
):

    if previous_value is None:
        return None

    difference = (
        current_value
        - previous_value
    )

    sign = (
        "+"
        if difference > 0
        else ""
    )

    return (
        f"{sign}"
        f"₹ {difference:,.0f}"
    )


def business_delta_color(
    current_value,
    previous_value,
    higher_is_better=True,
):

    if previous_value is None:
        return "off"

    difference = (
        current_value
        - previous_value
    )

    if difference == 0:
        return "off"

    if higher_is_better:

        return (
            "normal"
            if difference > 0
            else "inverse"
        )

    return (
        "normal"
        if difference < 0
        else "inverse"
    )


# ============================================================
# MONTH LABEL
# ============================================================

if latest_month:

    if previous_month:

        st.caption(
            f"Current Month: **{latest_month}**"
            f"  |  Previous Month: **{previous_month}**"
        )

    else:

        st.caption(
            f"Current Month: **{latest_month}**"
        )


# ============================================================
# EXECUTIVE ROW 1
#
# Order Qty
# Invoice Qty
# Fill Rate — Qty
# Pending Qty
# ============================================================

e1, e2, e3, e4 = st.columns(4)


e1.metric(
    "Order Qty",
    format_number(
        current["order_qty"]
    ),
    (
        number_delta(
            current["order_qty"],
            previous["order_qty"],
        )
        if previous
        else None
    ),
)


e2.metric(
    "Invoice Qty",
    format_number(
        current["invoice_qty"]
    ),
    (
        number_delta(
            current["invoice_qty"],
            previous["invoice_qty"],
        )
        if previous
        else None
    ),
)


e3.metric(
    "Fill Rate — Qty",
    format_percent(
        current["fr_qty"]
    ),
    (
        percent_delta(
            current["fr_qty"],
            previous["fr_qty"],
        )
        if previous
        else None
    ),
    delta_color=(
        business_delta_color(
            current["fr_qty"],
            previous["fr_qty"],
            higher_is_better=True,
        )
        if previous
        else "off"
    ),
)


# Pending lower is better
e4.metric(
    "Pending Qty",
    format_number(
        current["pending_qty"]
    ),
    (
        number_delta(
            current["pending_qty"],
            previous["pending_qty"],
        )
        if previous
        else None
    ),
    delta_color=(
        business_delta_color(
            current["pending_qty"],
            previous["pending_qty"],
            higher_is_better=False,
        )
        if previous
        else "off"
    ),
)


# ============================================================
# EXECUTIVE ROW 2
#
# Order Value
# Invoice Value
# Fill Rate — Value
# Sale Loss
# ============================================================

e5, e6, e7, e8 = st.columns(4)


e5.metric(
    "Order Value",
    format_value(
        current["order_value"]
    ),
    (
        currency_delta(
            current["order_value"],
            previous["order_value"],
        )
        if previous
        else None
    ),
)


e6.metric(
    "Invoice Value",
    format_value(
        current["invoice_value"]
    ),
    (
        currency_delta(
            current["invoice_value"],
            previous["invoice_value"],
        )
        if previous
        else None
    ),
)


e7.metric(
    "Fill Rate — Value",
    format_percent(
        current["fr_value"]
    ),
    (
        percent_delta(
            current["fr_value"],
            previous["fr_value"],
        )
        if previous
        else None
    ),
    delta_color=(
        business_delta_color(
            current["fr_value"],
            previous["fr_value"],
            higher_is_better=True,
        )
        if previous
        else "off"
    ),
)


# Sale loss lower is better
e8.metric(
    "Sale Loss",
    format_value(
        current["sale_loss"]
    ),
    (
        currency_delta(
            current["sale_loss"],
            previous["sale_loss"],
        )
        if previous
        else None
    ),
    delta_color=(
        business_delta_color(
            current["sale_loss"],
            previous["sale_loss"],
            higher_is_better=False,
        )
        if previous
        else "off"
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

    monthly = monthly_summary(
        filtered
    )

    # ========================================================
    # 1. MOM FILL RATE COMPARISON
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        'Month-on-Month Fill Rate Comparison'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Fill Rate comparison across months."
    )

    fr_data = monthly[
        [
            "Month",
            "fr_qty",
            "fr_value",
        ]
    ].copy()

    fr_long = fr_data.melt(
        id_vars=[
            "Month"
        ],
        value_vars=[
            "fr_qty",
            "fr_value",
        ],
        var_name="Metric",
        value_name="Fill Rate",
    )

    fr_long["Metric"] = (
        fr_long["Metric"]
        .replace(
            {
                "fr_qty":
                    "Fill Rate Qty",
                "fr_value":
                    "Fill Rate Value",
            }
        )
    )

    fr_chart = (
        alt.Chart(
            fr_long
        )
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

    fr_labels = (
        alt.Chart(
            fr_long
        )
        .mark_text(
            dy=-13,
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
        '<div class="section-title">'
        'Month-on-Month Table'
        '</div>',
        unsafe_allow_html=True,
    )

    mom_columns = {

        "Order Qty":
            "order_qty",

        "Invoice Qty":
            "invoice_qty",

        "Fill Rate Qty":
            "fr_qty",

        "Pending Qty":
            "pending_qty",

        "Order Value":
            "order_value",

        "Invoice Value":
            "invoice_value",

        "Fill Rate Value":
            "fr_value",

        "Pending Value":
            "pending_value",

        "Sale Loss":
            "sale_loss",

        "Orders":
            "orders",

        "Invoices":
            "invoices",
    }

    default_mom_columns = [

        "Order Qty",
        "Invoice Qty",
        "Fill Rate Qty",
        "Pending Qty",

        "Order Value",
        "Invoice Value",
        "Fill Rate Value",
        "Sale Loss",
    ]

    with st.expander(
        "⚙️ Choose MOM Table Columns",
        expanded=False,
    ):

        selected_mom_columns = (
            st.multiselect(
                "Columns to show",
                list(
                    mom_columns.keys()
                ),
                default=default_mom_columns,
                key="mom_columns",
            )
        )

    if not selected_mom_columns:

        selected_mom_columns = (
            default_mom_columns
        )

    mom_display = monthly[
        [
            "Month"
        ]
        +
        [
            mom_columns[c]
            for c
            in selected_mom_columns
        ]
    ].copy()

    rename_map = {
        value: key
        for key, value
        in mom_columns.items()
    }

    mom_display = (
        mom_display
        .rename(
            columns=rename_map
        )
    )

    # --------------------------------------------------------
    # Format MOM table
    # --------------------------------------------------------

    for col in mom_display.columns:

        if col == "Month":
            continue

        if "Fill Rate" in col:

            mom_display[col] = (
                mom_display[col]
                .map(
                    lambda x:
                    "—"
                    if pd.isna(x)
                    else f"{x:.1f}%"
                )
            )

        elif (
            "Value" in col
            or col == "Sale Loss"
        ):

            mom_display[col] = (
                mom_display[col]
                .map(
                    format_value
                )
            )

        else:

            mom_display[col] = (
                mom_display[col]
                .map(
                    format_number
                )
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
        '<div class="section-title">'
        'Fill Rate — Qty vs Value'
        '</div>',
        unsafe_allow_html=True,
    )

    fr_compare = (
        monthly[
            [
                "Month",
                "fr_qty",
                "fr_value",
            ]
        ]
        .melt(
            id_vars=[
                "Month"
            ],
            var_name="Metric",
            value_name="Fill Rate",
        )
    )

    fr_compare["Metric"] = (
        fr_compare["Metric"]
        .replace(
            {
                "fr_qty": "Qty",
                "fr_value": "Value",
            }
        )
    )

    fr_bar = (
        alt.Chart(
            fr_compare
        )
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
                    labelAngle=0,
                ),
            ),

            xOffset=alt.XOffset(
                "Metric:N"
            ),

            y=alt.Y(
                "Fill Rate:Q",
                title="Fill Rate (%)",
                axis=alt.Axis(
                    labelAngle=0,
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
                    title="Fill Rate",
                    format=".1f",
                ),
            ],
        )
        .properties(
            height=360
        )
    )

    fr_bar_labels = (
        alt.Chart(
            fr_compare
        )
        .mark_text(
            dy=-8,
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
        '<div class="section-title">'
        'Sale Loss MOM'
        '</div>',
        unsafe_allow_html=True,
    )

    if "sale_loss" in monthly.columns:

        sale_chart = (
            alt.Chart(
                monthly
            )
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
                        labelAngle=0,
                    ),
                ),

                y=alt.Y(
                    "sale_loss:Q",
                    title="Sale Loss",
                    axis=alt.Axis(
                        labelAngle=0,
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
            alt.Chart(
                monthly
            )
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
            sale_chart
            + sale_labels,
            use_container_width=True,
        )


    # ========================================================
    # 5. LAST MONTH VS THIS MONTH
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        'Last Month vs This Month'
        '</div>',
        unsafe_allow_html=True,
    )

    if len(monthly) >= 2:

        previous_mom = (
            monthly.iloc[-2]
        )

        current_mom = (
            monthly.iloc[-1]
        )

        l1, l2, l3, l4 = (
            st.columns(4)
        )

        # Fill Rate Qty
        l1.metric(
            "Fill Rate Qty",
            format_percent(
                current_mom[
                    "fr_qty"
                ]
            ),
            (
                f"{current_mom['fr_qty'] - previous_mom['fr_qty']:+.1f}%"
            ),
            delta_color=(
                "normal"
                if current_mom["fr_qty"]
                >= previous_mom["fr_qty"]
                else "inverse"
            ),
        )

        # Fill Rate Value
        l2.metric(
            "Fill Rate Value",
            format_percent(
                current_mom[
                    "fr_value"
                ]
            ),
            (
                f"{current_mom['fr_value'] - previous_mom['fr_value']:+.1f}%"
            ),
            delta_color=(
                "normal"
                if current_mom["fr_value"]
                >= previous_mom["fr_value"]
                else "inverse"
            ),
        )

        # Pending Qty
        l3.metric(
            "Pending Qty",
            format_number(
                current_mom[
                    "pending_qty"
                ]
            ),
            (
                f"{current_mom['pending_qty'] - previous_mom['pending_qty']:+,.0f}"
            ),
            delta_color=(
                "normal"
                if current_mom["pending_qty"]
                <= previous_mom["pending_qty"]
                else "inverse"
            ),
        )

        # Sale Loss
        l4.metric(
            "Sale Loss",
            format_value(
                current_mom[
                    "sale_loss"
                ]
            ),
            (
                f"₹ {current_mom['sale_loss'] - previous_mom['sale_loss']:+,.0f}"
            ),
            delta_color=(
                "normal"
                if current_mom["sale_loss"]
                <= previous_mom["sale_loss"]
                else "inverse"
            ),
        )

        st.caption(
            f"{previous_mom['Month']} → "
            f"{current_mom['Month']}"
        )

    else:

        st.info(
            "Select at least two months "
            "for month-on-month comparison."
        )


# ============================================================
# CUSTOMER WISE
# ============================================================

with tab_customer:

    st.markdown(
        '<div class="section-title">'
        'Customer Wise Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Click any customer name to view its detailed order-level information."
    )

    # --------------------------------------------------------
    # CUSTOMER SUMMARY
    # --------------------------------------------------------

    cust_summary = customer_summary(
        filtered
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    customer_search = st.text_input(
        "🔍 Search Customer",
        key="customer_search_box",
    )

    customer_view = (
        cust_summary.copy()
    )

    if customer_search:

        customer_view = (
            customer_view[
                customer_view[
                    CONFIG["customer"]
                ]
                .astype(str)
                .str.contains(
                    customer_search,
                    case=False,
                    na=False,
                )
            ]
        )

    # --------------------------------------------------------
    # COLUMN SELECTOR
    # --------------------------------------------------------

    customer_column_options = [

        "Order (count)",
        "Invoice (count)",
        "Order Qty",
        "Invoice Qty",
        "Fill Rate",
        "Sale Loss (In Lacs)",
        "TAT (avg)",
    ]

    default_customer_columns = (
        customer_column_options.copy()
    )

    with st.expander(
        "⚙️ Choose Customer Table Columns",
        expanded=False,
    ):

        selected_customer_columns = (
            st.multiselect(
                "Columns to show",
                customer_column_options,
                default=default_customer_columns,
                key="customer_columns",
            )
        )

    if not selected_customer_columns:

        selected_customer_columns = (
            default_customer_columns
        )


    # --------------------------------------------------------
    # SORTING STATE
    # --------------------------------------------------------

    if "customer_sort_column" not in st.session_state:

        st.session_state[
            "customer_sort_column"
        ] = None

        st.session_state[
            "customer_sort_direction"
        ] = None


    if "selected_customer" not in st.session_state:

        st.session_state[
            "selected_customer"
        ] = None


    sort_map = {

        "Order (count)":
            "order_count",

        "Invoice (count)":
            "invoice_count",

        "Order Qty":
            "order_qty",

        "Invoice Qty":
            "invoice_qty",

        "Fill Rate":
            "fill_rate",

        "Sale Loss (In Lacs)":
            "sale_loss",

        "TAT (avg)":
            "tat_avg",
    }


    def change_sort(column):

        current = st.session_state[
            "customer_sort_column"
        ]

        direction = st.session_state[
            "customer_sort_direction"
        ]

        if current != column:

            st.session_state[
                "customer_sort_column"
            ] = column

            st.session_state[
                "customer_sort_direction"
            ] = "asc"

        elif direction == "asc":

            st.session_state[
                "customer_sort_direction"
            ] = "desc"

        else:

            st.session_state[
                "customer_sort_column"
            ] = None

            st.session_state[
                "customer_sort_direction"
            ] = None


    def sort_arrow(column):

        if (
            st.session_state[
                "customer_sort_column"
            ]
            != column
        ):

            return ""

        return (
            " ▲"
            if st.session_state[
                "customer_sort_direction"
            ]
            == "asc"
            else " ▼"
        )


    # --------------------------------------------------------
    # APPLY SORT
    # --------------------------------------------------------

    active_sort = st.session_state[
        "customer_sort_column"
    ]

    active_direction = st.session_state[
        "customer_sort_direction"
    ]

    if active_sort:

        customer_view = (
            customer_view
            .sort_values(
                by=active_sort,
                ascending=(
                    active_direction
                    == "asc"
                ),
                na_position="last",
            )
        )

    # --------------------------------------------------------
    # CUSTOMER TABLE
    # --------------------------------------------------------

    column_widths = (
        [3]
        +
        [1] * len(
            selected_customer_columns
        )
    )

    with st.container(
        key="customer_table"
    ):

        header = st.columns(
            column_widths
        )

        # Customer Name
        if header[0].button(
            "Customer Name"
            + sort_arrow(
                "__customer__"
            ),
            key="customer_name_header",
            use_container_width=True,
        ):

            change_sort(
                "__customer__"
            )

            if (
                st.session_state[
                    "customer_sort_column"
                ]
                == "__customer__"
            ):

                customer_view = (
                    customer_view
                    .sort_values(
                        CONFIG[
                            "customer"
                        ],
                        ascending=(
                            st.session_state[
                                "customer_sort_direction"
                            ]
                            == "asc"
                        ),
                        na_position="last",
                    )
                )

        # Other headers
        for header_col, label in zip(
            header[1:],
            selected_customer_columns,
        ):

            key = sort_map[
                label
            ]

            if header_col.button(
                label
                + sort_arrow(key),
                key=(
                    "cust_header_"
                    + key
                ),
                use_container_width=True,
            ):

                change_sort(key)

                st.rerun()


        # ----------------------------------------------------
        # DATA ROWS
        # ----------------------------------------------------

        for idx, row in (
            customer_view
            .reset_index(
                drop=True
            )
            .iterrows()
        ):

            row_columns = st.columns(
                column_widths
            )

            customer_name = row[
                CONFIG["customer"]
            ]

            # Customer name
            if row_columns[0].button(
                str(customer_name),
                key=(
                    f"cust_"
                    f"{idx}_"
                    f"{str(customer_name)}"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "selected_customer"
                ] = customer_name

                st.rerun()


            # Metrics
            for col_container, label in zip(
                row_columns[1:],
                selected_customer_columns,
            ):

                if label == "Order (count)":

                    center(
                        col_container,
                        format_number(
                            row[
                                "order_count"
                            ]
                        ),
                    )

                elif label == "Invoice (count)":

                    center(
                        col_container,
                        format_number(
                            row[
                                "invoice_count"
                            ]
                        ),
                    )

                elif label == "Order Qty":

                    center(
                        col_container,
                        format_number(
                            row[
                                "order_qty"
                            ]
                        ),
                    )

                elif label == "Invoice Qty":

                    center(
                        col_container,
                        format_number(
                            row[
                                "invoice_qty"
                            ]
                        ),
                    )

                elif label == "Fill Rate":

                    center(
                        col_container,
                        format_percent(
                            row[
                                "fill_rate"
                            ]
                        ),
                    )

                elif label == "Sale Loss (In Lacs)":

                    value = row[
                        "sale_loss"
                    ]

                    center(
                        col_container,
                        (
                            "—"
                            if pd.isna(
                                value
                            )
                            else
                            f"₹ {value:,.2f}"
                        ),
                    )

                elif label == "TAT (avg)":

                    value = row[
                        "tat_avg"
                    ]

                    # Extra protection against
                    # invalid TAT values.
                    if (
                        pd.isna(value)
                        or value < 0
                        or value > 365
                    ):

                        display_tat = "—"

                    else:

                        display_tat = (
                            f"{value:.1f}"
                        )

                    center(
                        col_container,
                        display_tat,
                    )


    # --------------------------------------------------------
    # OPEN DETAILS
    # --------------------------------------------------------

    selected_customer = (
        st.session_state.get(
            "selected_customer"
        )
    )

    if selected_customer:

        show_customer_details(
            selected_customer,
            filtered,
        )

        # Clear after dialog is opened
        st.session_state[
            "selected_customer"
        ] = None


# ============================================================
# CATEGORY WISE
# ============================================================

with tab_category:

    st.markdown(
        '<div class="section-title">'
        'Category Wise Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    category_summary = (
        filtered
        .groupby(
            CONFIG["category"],
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

    category_summary["fr_qty"] = (
        np.where(
            category_summary[
                "order_qty"
            ] != 0,

            (
                category_summary[
                    "invoice_qty"
                ]
                /
                category_summary[
                    "order_qty"
                ]
                * 100
            ),

            np.nan,
        )
    )

    category_summary["fr_value"] = (
        np.where(
            category_summary[
                "order_value"
            ] != 0,

            (
                category_summary[
                    "invoice_value"
                ]
                /
                category_summary[
                    "order_value"
                ]
                * 100
            ),

            np.nan,
        )
    )

    category_summary[
        "pending_qty"
    ] = (
        category_summary[
            "order_qty"
        ]
        -
        category_summary[
            "invoice_qty"
        ]
    )

    category_summary[
        "pending_value"
    ] = (
        category_summary[
            "order_value"
        ]
        -
        category_summary[
            "invoice_value"
        ]
    )

    # ========================================================
    # CATEGORY TABLE
    # ========================================================

    category_display = (
        category_summary[
            [
                CONFIG["category"],
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
        ]
        .rename(
            columns={

                CONFIG["category"]:
                    "Category",

                "orders":
                    "Orders",

                "order_qty":
                    "Order Qty",

                "invoice_qty":
                    "Invoice Qty",

                "fr_qty":
                    "FR % Qty",

                "fr_value":
                    "FR % Value",

                "pending_qty":
                    "Pending Qty",

                "order_value":
                    "Order Value",

                "invoice_value":
                    "Invoice Value",

                "pending_value":
                    "Pending Value",

                "sale_loss":
                    "Sale Loss",
            }
        )
    )

    st.dataframe(
        category_display,
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # CATEGORY FILL RATE CHART
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        'Category Fill Rate'
        '</div>',
        unsafe_allow_html=True,
    )

    category_chart_data = (
        category_summary[
            [
                CONFIG["category"],
                "fr_qty",
            ]
        ]
        .copy()
    )

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
                f"{CONFIG['category']}:N",
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
                    labelAngle=0,
                ),
            ),

            tooltip=[
                alt.Tooltip(
                    f"{CONFIG['category']}:N",
                    title="Category",
                ),
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
                f"{CONFIG['category']}:N",
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
    f"Sheets: {', '.join(sheets_used)}"
    f"  |  "
    f"Rows: {len(filtered):,}"
    f"  |  "
    f"Updated: "
    f"{datetime.now().strftime('%d-%m-%Y %H:%M')}"
)
