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
    page_title="Fill Rate MOM Dashboard",
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
    # OTHER
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
# THEME
# ============================================================

C_BG = "#F4F6FA"
C_CARD = "#FFFFFF"
C_BORDER = "#E1E5EB"
C_TEXT = "#132238"
C_MUTED = "#6B7280"
C_BLUE = "#0068C9"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* =====================================================
       APP
       ===================================================== */

    .stApp {{
        background: {C_BG};
    }}

    h1, h2, h3, h4 {{
        color: {C_TEXT} !important;
    }}

    /* =====================================================
       EXECUTIVE HEADER
       ===================================================== */

    .executive-title {{
        color: {C_TEXT};
        font-size: 24px;
        font-weight: 750;
        margin-bottom: 4px;
    }}

    .executive-subtitle {{
        color: {C_MUTED};
        font-size: 14px;
        margin-bottom: 18px;
    }}

    /* =====================================================
       SECTION TITLES
       ===================================================== */

    .section-title {{
        font-size: 21px;
        font-weight: 750;
        color: {C_TEXT};
        margin-top: 20px;
        margin-bottom: 8px;
    }}

    .dashboard-subtitle {{
        color: {C_MUTED};
        font-size: 14px;
        margin-bottom: 15px;
    }}

    /* =====================================================
       METRIC CARDS
       ===================================================== */

    div[data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
        min-height: 118px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {C_TEXT} !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {C_TEXT} !important;
        font-weight: 750 !important;
        font-size: 40px !important;
    }}

    div[data-testid="stMetricDelta"] {{
        font-weight: 600 !important;
    }}

    /* =====================================================
       TABS
       ===================================================== */

    button[data-baseweb="tab"] {{
        color: {C_TEXT} !important;
        font-size: 14px !important;
    }}

    /* =====================================================
       BUTTONS
       ===================================================== */

    div.stButton > button {{
        border-radius: 8px;
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
        series
        .astype(str)
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

    return f"{float(value):,.0f}"


def format_percent(value):

    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.1f}%"


def format_sale_loss(value):

    if value is None or pd.isna(value):
        return "—"

    return f"₹ {float(value):,.2f}"


def format_currency(value):

    if value is None or pd.isna(value):
        return "—"

    value = float(value)

    sign = "-" if value < 0 else ""

    value = abs(value)

    if value >= 10_000_000:

        return (
            f"{sign}₹ "
            f"{value / 10_000_000:.2f} Cr"
        )

    if value >= 100_000:

        return (
            f"{sign}₹ "
            f"{value / 100_000:.2f} L"
        )

    return (
        f"{sign}₹ "
        f"{value:,.2f}"
    )


def safe_ratio(
    numerator,
    denominator,
):

    if denominator is None:
        return np.nan

    if pd.isna(denominator):
        return np.nan

    if denominator == 0:
        return np.nan

    return (
        numerator
        / denominator
        * 100
    )


# ============================================================
# SHAREPOINT
# ============================================================

def get_download_url(url):

    if "download=1" in url.lower():
        return url

    separator = (
        "&"
        if "?" in url
        else "?"
    )

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
            "SharePoint returned an HTML/login page "
            "instead of the Excel workbook."
        )

    return pd.read_excel(
        io.BytesIO(
            response.content
        ),
        sheet_name=None,
        engine="openpyxl",
    )


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

        # Only Apr, May, Jun, Jul, Aug etc.
        if sheet_name not in MONTH_ORDER:
            continue

        if raw_df is None or raw_df.empty:
            continue

        df = raw_df.copy()

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        df[
            "__Dashboard_Month"
        ] = sheet_name

        frames.append(df)

        sheets_used.append(
            sheet_name
        )

    if not frames:

        raise ValueError(
            "No monthly sheets found. "
            "Expected sheets like Apr, May, Jun, Jul, Aug."
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
        .reset_index(drop=True)
    )

    return (
        combined,
        sheets_used,
    )


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
    # Calculated Fill Rate
    # --------------------------------------------------------

    if oq and iq:

        df[
            "__Calculated_FR_Qty"
        ] = np.where(
            df[oq] != 0,
            (
                df[iq]
                / df[oq]
                * 100
            ),
            np.nan,
        )

    else:

        df[
            "__Calculated_FR_Qty"
        ] = np.nan

    if ov and iv:

        df[
            "__Calculated_FR_Value"
        ] = np.where(
            df[ov] != 0,
            (
                df[iv]
                / df[ov]
                * 100
            ),
            np.nan,
        )

    else:

        df[
            "__Calculated_FR_Value"
        ] = np.nan

    # --------------------------------------------------------
    # Fill Rate
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
            df[
                "__Calculated_FR_Qty"
            ]
        )

    if frv:

        df["__FR_Value"] = clean_numeric(
            df[frv]
        )

    else:

        df["__FR_Value"] = (
            df[
                "__Calculated_FR_Value"
            ]
        )

    # --------------------------------------------------------
    # Pending Qty
    # --------------------------------------------------------

    if oq and iq:

        df["__Pending_Qty"] = (
            df[oq].fillna(0)
            -
            df[iq].fillna(0)
        )

    else:

        df["__Pending_Qty"] = np.nan

    # --------------------------------------------------------
    # Pending Value
    # --------------------------------------------------------

    if ov and iv:

        df["__Pending_Value"] = (
            df[ov].fillna(0)
            -
            df[iv].fillna(0)
        )

    else:

        df["__Pending_Value"] = np.nan

    # --------------------------------------------------------
    # Valid TAT
    #
    # Ignore obviously invalid values like 172472.1
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
# MONTHLY SUMMARY
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
        df
        .groupby(
            "Month",
            dropna=False,
        )
        .agg(**aggregation)
        .reset_index()
    )

    # --------------------------------------------------------
    # Fill Rate Qty
    # --------------------------------------------------------

    if (
        "order_qty"
        in result.columns
        and
        "invoice_qty"
        in result.columns
    ):

        result["fr_qty"] = np.where(
            result["order_qty"] != 0,
            (
                result["invoice_qty"]
                /
                result["order_qty"]
                * 100
            ),
            np.nan,
        )

        result["pending_qty"] = (
            result["order_qty"]
            -
            result["invoice_qty"]
        )

    # --------------------------------------------------------
    # Fill Rate Value
    # --------------------------------------------------------

    if (
        "order_value"
        in result.columns
        and
        "invoice_value"
        in result.columns
    ):

        result["fr_value"] = np.where(
            result["order_value"] != 0,
            (
                result["invoice_value"]
                /
                result["order_value"]
                * 100
            ),
            np.nan,
        )

        result["pending_value"] = (
            result["order_value"]
            -
            result["invoice_value"]
        )

    result["__sort"] = (
        result["Month"]
        .apply(month_sort_key)
    )

    return (
        result
        .sort_values("__sort")
        .drop(
            columns="__sort"
        )
        .reset_index(drop=True)
    )


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def customer_summary(df):

    aggregation = {

        "order_qty": (
            CONFIG["order_qty"],
            "sum",
        ),

        "invoice_qty": (
            CONFIG["invoice_qty"],
            "sum",
        ),

        "order_count": (
            CONFIG["order_id"],
            "nunique",
        ),

        "sale_loss": (
            CONFIG["sale_loss"],
            "sum",
        ),

        "tat_avg": (
            "__Valid_TAT",
            "mean",
        ),
    }

    if (
        CONFIG["invoice_number"]
        in df.columns
    ):

        aggregation[
            "invoice_count"
        ] = (
            CONFIG["invoice_number"],
            lambda x:
            x.dropna()
            .astype(str)
            .nunique(),
        )

    else:

        aggregation[
            "invoice_count"
        ] = (
            CONFIG["invoice_qty"],
            lambda x:
            int(
                (
                    x.fillna(0)
                    > 0
                ).sum()
            ),
        )

    result = (
        df
        .groupby(
            CONFIG["customer"],
            dropna=False,
        )
        .agg(**aggregation)
        .reset_index()
    )

    result["fill_rate"] = np.where(
        result["order_qty"] != 0,
        (
            result["invoice_qty"]
            /
            result["order_qty"]
            * 100
        ),
        np.nan,
    )

    return result


# ============================================================
# CUSTOMER DETAIL DIALOG
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

    rows["TAT"] = (
        rows["__Valid_TAT"]
    )

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
    # Date formatting
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
        ] = (
            st.column_config
            .NumberColumn(
                "Fill Rate",
                format="%.1f%%",
            )
        )

    if "TAT" in display.columns:

        column_config[
            "TAT"
        ] = (
            st.column_config
            .NumberColumn(
                "TAT",
                format="%.1f",
            )
        )

    if (
        CONFIG["sale_loss"]
        in display.columns
    ):

        column_config[
            CONFIG["sale_loss"]
        ] = (
            st.column_config
            .NumberColumn(
                CONFIG["sale_loss"],
                format="₹ %.2f",
            )
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
    <div class="executive-title">
        📊 Fill Rate & MOM Performance
    </div>

    <div class="executive-subtitle">
        Month-on-Month performance with
        customer-level operational drill-down
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
        "SHAREPOINT_EXCEL_URL is not configured "
        "in Streamlit secrets."
    )

    st.stop()


# ============================================================
# REFRESH BUTTON
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
# LOAD DATA
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
        f"Could not load Excel file: {e}"
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
    CONFIG["category"],
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
        filtered[
            "Month"
        ].isin(
            selected_months
        )
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
# MONTH SELECTION
# ============================================================

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


# ============================================================
# CURRENT / PREVIOUS DATA
# ============================================================

current_df = (
    filtered[
        filtered[
            "Month"
        ] == latest_month
    ]
    if latest_month
    else filtered
)

previous_df = (
    filtered[
        filtered[
            "Month"
        ] == previous_month
    ]
    if previous_month
    else pd.DataFrame()
)


# ============================================================
# EXECUTIVE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Executive Overview'
    '</div>',
    unsafe_allow_html=True,
)

if latest_month:

    if previous_month:

        st.caption(
            f"Current Month: **{latest_month}**"
            f"  |  "
            f"Previous Month: **{previous_month}**"
        )

    else:

        st.caption(
            f"Current Month: **{latest_month}**"
        )


# ============================================================
# EXECUTIVE METRICS
# ============================================================

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

    return {

        "order_qty":
            order_qty,

        "invoice_qty":
            invoice_qty,

        "fr_qty":
            safe_ratio(
                invoice_qty,
                order_qty,
            ),

        "pending_qty":
            order_qty
            - invoice_qty,

        "order_value":
            order_value,

        "invoice_value":
            invoice_value,

        "fr_value":
            safe_ratio(
                invoice_value,
                order_value,
            ),

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

def number_delta(current_value, previous_value):

    if previous_value is None:
        return None

    difference = current_value - previous_value

    return f"{difference:+,.0f}"


def percent_delta(current_value, previous_value):

    if previous_value is None:
        return None

    difference = current_value - previous_value

    return f"{difference:+.1f}%"


def currency_delta(current_value, previous_value):

    if previous_value is None:
        return None

    difference = current_value - previous_value

    return f"₹ {difference:+,.0f}"


def sale_loss_delta(current_value, previous_value):

    if previous_value is None:
        return None

    difference = current_value - previous_value

    return f"₹ {difference:+,.2f}"
# ============================================================
# EXECUTIVE CARD ROW 1
#
# Order Qty
# Invoice Qty
# Fill Rate Qty
# Pending Qty
# ============================================================

e1, e2, e3, e4 = st.columns(4)


# ------------------------------------------------------------
# ORDER QTY
#
# Neutral
# ------------------------------------------------------------

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
    delta_color="off",
)


# ------------------------------------------------------------
# INVOICE QTY
#
# Neutral
# ------------------------------------------------------------

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
    delta_color="off",
)


# ------------------------------------------------------------
# FILL RATE QTY
#
# Higher is better.
# Streamlit "normal" gives:
# increase = green
# decrease = red
# ------------------------------------------------------------

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
    delta_color="normal",
)


# ------------------------------------------------------------
# PENDING QTY
#
# Lower is better.
# Streamlit "inverse" gives:
# decrease = green
# increase = red
# ------------------------------------------------------------

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
    delta_color="inverse",
)


# ============================================================
# EXECUTIVE CARD ROW 2
#
# Order Value
# Invoice Value
# Fill Rate Value
# Sale Loss
# ============================================================

e5, e6, e7, e8 = st.columns(4)


# ------------------------------------------------------------
# ORDER VALUE
#
# Neutral
# ------------------------------------------------------------

e5.metric(
    "Order Value",
    format_currency(
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
    delta_color="off",
)


# ------------------------------------------------------------
# INVOICE VALUE
#
# Neutral
# ------------------------------------------------------------

e6.metric(
    "Invoice Value",
    format_currency(
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
    delta_color="off",
)


# ------------------------------------------------------------
# FILL RATE VALUE
#
# Higher is better.
# ------------------------------------------------------------

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
    delta_color="normal",
)


# ------------------------------------------------------------
# SALE LOSS
#
# Lower is better.
# TWO DECIMAL PLACES.
# ------------------------------------------------------------

e8.metric(
    "Sale Loss",
    format_sale_loss(
        current["sale_loss"]
    ),
    (
        sale_loss_delta(
            current["sale_loss"],
            previous["sale_loss"],
        )
        if previous
        else None
    ),
    delta_color="inverse",
)


# ============================================================
# LAST MONTH VS THIS MONTH
#
# IMPORTANT:
# This is now OUTSIDE the tabs.
# It appears directly below Executive Overview cards.
# ============================================================

st.markdown(
    '<div class="section-title">'
    'Last Month vs This Month'
    '</div>',
    unsafe_allow_html=True,
)


if (
    previous_month
    and latest_month
    and not previous_df.empty
):

    lm1, lm2, lm3, lm4 = st.columns(4)

    # --------------------------------------------------------
    # Fill Rate Qty
    # --------------------------------------------------------

    lm1.metric(
        "Fill Rate — Qty",
        format_percent(
            current["fr_qty"]
        ),
        percent_delta(
            current["fr_qty"],
            previous["fr_qty"],
        ),
        delta_color="normal",
    )

    # --------------------------------------------------------
    # Fill Rate Value
    # --------------------------------------------------------

    lm2.metric(
        "Fill Rate — Value",
        format_percent(
            current["fr_value"]
        ),
        percent_delta(
            current["fr_value"],
            previous["fr_value"],
        ),
        delta_color="normal",
    )

    # --------------------------------------------------------
    # Pending Qty
    # --------------------------------------------------------

    lm3.metric(
        "Pending Qty",
        format_number(
            current["pending_qty"]
        ),
        number_delta(
            current["pending_qty"],
            previous["pending_qty"],
        ),
        delta_color="inverse",
    )

    # --------------------------------------------------------
    # Sale Loss
    #
    # TWO DECIMAL PLACES.
    # --------------------------------------------------------

    lm4.metric(
        "Sale Loss",
        format_sale_loss(
            current["sale_loss"]
        ),
        sale_loss_delta(
            current["sale_loss"],
            previous["sale_loss"],
        ),
        delta_color="inverse",
    )

    st.caption(
        f"{previous_month} → {latest_month}"
    )

else:

    st.info(
        "At least two months are required "
        "for Last Month vs This Month comparison."
    )


# ============================================================
# MAIN TABS
#
# ONLY ONE SET OF TABS
# ============================================================

tab_mom, tab_customer, tab_category = st.tabs(
    [
        "📈 MOM Overview",
        "🏪 Customer Wise",
        "📦 Category Wise",
    ]
)


# ============================================================
# TAB 1
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

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Fill Rate comparison across months.'
        '</div>',
        unsafe_allow_html=True,
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


    # ========================================================
    # LINE CHART
    # ========================================================

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
            height=390
        )
    )


    # ========================================================
    # LABELS
    #
    # Qty above
    # Value below
    #
    # Prevents May-style overlap.
    # ========================================================

    qty_labels = (
        alt.Chart(
            fr_long[
                fr_long["Metric"]
                ==
                "Fill Rate Qty"
            ]
        )
        .mark_text(
            dy=-15,
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


    value_labels = (
        alt.Chart(
            fr_long[
                fr_long["Metric"]
                ==
                "Fill Rate Value"
            ]
        )
        .mark_text(
            dy=17,
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
        (
            fr_chart
            +
            qty_labels
            +
            value_labels
        ),
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

        selected_mom_columns = st.multiselect(
            "Columns to show",
            list(
                mom_columns.keys()
            ),
            default=default_mom_columns,
            key="mom_columns",
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
    # Formatting
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
                    else
                    f"{x:.1f}%"
                )
            )

        elif (
            "Value" in col
            or col == "Sale Loss"
        ):

            mom_display[col] = (
                mom_display[col]
                .map(
                    format_currency
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
            id_vars=["Month"],
            var_name="Metric",
            value_name="Fill Rate",
        )
    )

    fr_compare["Metric"] = (
        fr_compare["Metric"]
        .replace(
            {
                "fr_qty":
                    "Qty",

                "fr_value":
                    "Value",
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
        (
            fr_bar
            +
            fr_bar_labels
        ),
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

                    alt.Tooltip(
                        "Month:N",
                        title="Month",
                    ),

                    alt.Tooltip(
                        "sale_loss:Q",
                        title="Sale Loss",
                        format=",.2f",
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
                    format=",.2f",
                ),
            )
        )

        st.altair_chart(
            (
                sale_chart
                +
                sale_labels
            ),
            use_container_width=True,
        )


# ============================================================
# TAB 2
# CUSTOMER WISE
# ============================================================

with tab_customer:

    st.markdown(
        '<div class="section-title">'
        'Customer Wise Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Click any customer name to view detailed order-level information.'
        '</div>',
        unsafe_allow_html=True,
    )

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

        selected_customer_columns = st.multiselect(
            "Columns to show",
            customer_column_options,
            default=default_customer_columns,
            key="customer_columns",
        )

    if not selected_customer_columns:

        selected_customer_columns = (
            default_customer_columns
        )

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    if (
        "customer_sort_column"
        not in st.session_state
    ):

        st.session_state[
            "customer_sort_column"
        ] = None

        st.session_state[
            "customer_sort_direction"
        ] = None

    if (
        "selected_customer"
        not in st.session_state
    ):

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

        current_sort = (
            st.session_state[
                "customer_sort_column"
            ]
        )

        current_direction = (
            st.session_state[
                "customer_sort_direction"
            ]
        )

        if current_sort != column:

            st.session_state[
                "customer_sort_column"
            ] = column

            st.session_state[
                "customer_sort_direction"
            ] = "asc"

        elif current_direction == "asc":

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
            if
            st.session_state[
                "customer_sort_direction"
            ]
            == "asc"
            else
            " ▼"
        )


    active_sort = (
        st.session_state[
            "customer_sort_column"
        ]
    )

    active_direction = (
        st.session_state[
            "customer_sort_direction"
        ]
    )

    if active_sort == "__customer__":

        customer_view = (
            customer_view
            .sort_values(
                CONFIG["customer"],
                ascending=(
                    active_direction
                    == "asc"
                ),
                na_position="last",
            )
        )

    elif active_sort:

        customer_view = (
            customer_view
            .sort_values(
                active_sort,
                ascending=(
                    active_direction
                    == "asc"
                ),
                na_position="last",
            )
        )


    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    column_widths = (
        [3]
        +
        [1] *
        len(
            selected_customer_columns
        )
    )

    with st.container():

        header = st.columns(
            column_widths
        )

        if header[0].button(
            "Customer Name"
            +
            sort_arrow(
                "__customer__"
            ),
            key="customer_name_header",
            use_container_width=True,
        ):

            change_sort(
                "__customer__"
            )

            st.rerun()


        for (
            header_col,
            label
        ) in zip(
            header[1:],
            selected_customer_columns,
        ):

            key = sort_map[
                label
            ]

            if header_col.button(
                label
                +
                sort_arrow(key),
                key=(
                    "cust_header_"
                    + key
                ),
                use_container_width=True,
            ):

                change_sort(
                    key
                )

                st.rerun()


        # ----------------------------------------------------
        # DATA ROWS
        # ----------------------------------------------------

        for (
            idx,
            row
        ) in (
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

            if row_columns[0].button(
                str(customer_name),
                key=(
                    f"cust_{idx}_"
                    f"{str(customer_name)}"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "selected_customer"
                ] = customer_name

                st.rerun()


            for (
                col_container,
                label
            ) in zip(
                row_columns[1:],
                selected_customer_columns,
            ):

                if label == "Order (count)":

                    col_container.markdown(
                        f"<div style='text-align:center'>{format_number(row['order_count'])}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "Invoice (count)":

                    col_container.markdown(
                        f"<div style='text-align:center'>{format_number(row['invoice_count'])}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "Order Qty":

                    col_container.markdown(
                        f"<div style='text-align:center'>{format_number(row['order_qty'])}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "Invoice Qty":

                    col_container.markdown(
                        f"<div style='text-align:center'>{format_number(row['invoice_qty'])}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "Fill Rate":

                    col_container.markdown(
                        f"<div style='text-align:center'>{format_percent(row['fill_rate'])}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "Sale Loss (In Lacs)":

                    value = row[
                        "sale_loss"
                    ]

                    display_value = (
                        "—"
                        if pd.isna(value)
                        else
                        f"₹ {value:,.2f}"
                    )

                    col_container.markdown(
                        f"<div style='text-align:center'>{display_value}</div>",
                        unsafe_allow_html=True,
                    )

                elif label == "TAT (avg)":

                    value = row[
                        "tat_avg"
                    ]

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

                    col_container.markdown(
                        f"<div style='text-align:center'>{display_tat}</div>",
                        unsafe_allow_html=True,
                    )


    # --------------------------------------------------------
    # CUSTOMER DETAIL
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

        st.session_state[
            "selected_customer"
        ] = None


# ============================================================
# TAB 3
# CATEGORY WISE
# ============================================================

with tab_category:

    st.markdown(
        '<div class="section-title">'
        'Category Wise Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Category-level order, invoice, fill rate and sale loss performance.'
        '</div>',
        unsafe_allow_html=True,
    )


    # ========================================================
    # CATEGORY SUMMARY
    # ========================================================

    category_summary = (
        filtered
        .groupby(
            CONFIG["category"],
            dropna=False,
        )
        .agg(

            orders=(
                CONFIG["order_id"],
                "nunique",
            ),

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
        )
        .reset_index()
    )


    # --------------------------------------------------------
    # Fill Rate
    # --------------------------------------------------------

    category_summary[
        "fr_qty"
    ] = np.where(
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


    category_summary[
        "fr_value"
    ] = np.where(
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


    # --------------------------------------------------------
    # Pending
    # --------------------------------------------------------

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
        .copy()
    )


    # --------------------------------------------------------
    # Category name cleanup
    # --------------------------------------------------------

    category_display[
        CONFIG["category"]
    ] = (
        category_display[
            CONFIG["category"]
        ]
        .fillna(
            "Blank / Not Available"
        )
        .astype(str)
        .replace(
            {
                "None":
                    "Blank / Not Available",

                "nan":
                    "Blank / Not Available",

                "":
                    "Blank / Not Available",
            }
        )
    )


    # --------------------------------------------------------
    # Rename
    # --------------------------------------------------------

    category_display = (
        category_display
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


    # ========================================================
    # FORMATTED CATEGORY TABLE
    # ========================================================

    # Qty
    for col in [
        "Orders",
        "Order Qty",
        "Invoice Qty",
        "Pending Qty",
    ]:

        category_display[
            col
        ] = (
            category_display[
                col
            ]
            .apply(
                format_number
            )
        )


    # Percentage
    for col in [
        "FR % Qty",
        "FR % Value",
    ]:

        category_display[
            col
        ] = (
            category_display[
                col
            ]
            .apply(
                format_percent
            )
        )


    # Currency
    for col in [
        "Order Value",
        "Invoice Value",
        "Pending Value",
    ]:

        category_display[
            col
        ] = (
            category_display[
                col
            ]
            .apply(
                format_currency
            )
        )


    # Sale Loss = ALWAYS 2 DECIMALS
    category_display[
        "Sale Loss"
    ] = (
        category_display[
            "Sale Loss"
        ]
        .apply(
            format_sale_loss
        )
    )


    # ========================================================
    # DISPLAY CATEGORY TABLE
    # ========================================================

    st.dataframe(
        category_display,
        use_container_width=True,
        hide_index=True,
        height=430,
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

    category_chart_data[
        CONFIG["category"]
    ] = (
        category_chart_data[
            CONFIG["category"]
        ]
        .fillna(
            "Blank / Not Available"
        )
        .astype(str)
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
        (
            category_chart
            +
            category_labels
        ),
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
