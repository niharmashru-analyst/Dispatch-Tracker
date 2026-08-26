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

    # IMPORTANT:
    # Keep your existing secret name
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
    "order_id": "Order Id",
    "external_document": "External Document No.",

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

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
# COLORS / LIGHT THEME
# ============================================================

C_BG = "#F5F7FB"
C_CARD = "#FFFFFF"
C_BORDER = "#DDE3EC"
C_BORDER_DARK = "#C9D1DC"
C_TEXT = "#172B4D"
C_MUTED = "#6B7280"
C_BLUE = "#3157D5"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ======================================================
       MAIN
       ====================================================== */

    .stApp {{
        background: {C_BG};
    }}

    h1, h2, h3, h4 {{
        color: {C_TEXT} !important;
    }}

    p {{
        color: {C_TEXT};
    }}


    /* ======================================================
       EXECUTIVE KPI CARDS
       ====================================================== */

    div[data-testid="stMetric"] {{
        background: {C_CARD};
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 15px 18px;
        min-height: 105px;
        box-shadow: 0 2px 7px rgba(20, 30, 50, 0.06);
    }}

    div[data-testid="stMetricLabel"] {{
        color: {C_TEXT} !important;
        font-size: 14px !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {C_TEXT} !important;
        font-weight: 750 !important;
        font-size: 32px !important;
    }}

    div[data-testid="stMetricDelta"] {{
        font-weight: 600 !important;
    }}


    /* ======================================================
       SECTION TITLES
       ====================================================== */

    .section-title {{
        font-size: 20px;
        font-weight: 750;
        color: {C_TEXT};
        margin-top: 20px;
        margin-bottom: 10px;
    }}

    .dashboard-caption {{
        color: {C_MUTED};
        font-size: 13px;
        margin-top: -5px;
        margin-bottom: 15px;
    }}


    /* ======================================================
       EXECUTIVE HEADER
       ====================================================== */

    .executive-header {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 7px rgba(20, 30, 50, 0.05);
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


    /* ======================================================
       CUSTOMER TABLE
       ====================================================== */

    /*
       The previous version had a large white gap between
       rows because Streamlit's vertical block gap was being
       applied between every horizontal row.

       These rules remove that gap and create clean borders.
    */

    div[data-testid="stVerticalBlock"]:has(
        div.st-key-fillrate_table
    ) {{
        gap: 0 !important;
    }}

    .st-key-fillrate_table {{
        background: #FFFFFF;
        border: 1px solid {C_BORDER};
        border-radius: 10px;
        overflow: hidden;
        padding: 0 !important;
        gap: 0 !important;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"] {{
        gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        min-height: 48px !important;
        border-bottom: 1px solid {C_BORDER};
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:last-child {{
        border-bottom: none;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]
    > [data-testid="column"] {{
        padding: 0 !important;
        margin: 0 !important;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]
    > [data-testid="column"]:not(:last-child) {{
        border-right: 1px solid {C_BORDER};
    }}

    /* Header */
    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:first-child {{
        background: #F7F9FC;
        min-height: 55px !important;
    }}

    .st-key-fillrate_table
    [data-testid="stHorizontalBlock"]:first-child
    div.stButton > button {{
        font-weight: 700 !important;
        color: {C_TEXT} !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }}

    /* Table buttons */
    .st-key-fillrate_table
    div.stButton {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    .st-key-fillrate_table
    div.stButton > button {{
        min-height: 48px !important;
        height: 48px !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
        color: {C_TEXT} !important;
        padding: 4px 8px !important;
        margin: 0 !important;
        white-space: normal !important;
    }}

    .st-key-fillrate_table
    div.stButton > button:hover {{
        background: #F2F5FA !important;
        color: {C_BLUE} !important;
    }}


    /* ======================================================
       NORMAL BUTTONS
       ====================================================== */

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


    /* ======================================================
       TABS
       ====================================================== */

    button[data-baseweb="tab"] {{
        color: {C_TEXT};
        font-weight: 600;
    }}


    /* ======================================================
       DATAFRAME
       ====================================================== */

    div[data-testid="stDataFrame"] {{
        border: 1px solid {C_BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
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


def safe_ratio(
    numerator,
    denominator,
):

    try:

        if denominator == 0:
            return np.nan

        return (
            numerator
            / denominator
            * 100
        )

    except Exception:

        return np.nan


def center(container, text):

    container.markdown(
        f"""
        <div style="
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
            min-height:48px;
            color:{C_TEXT};
            font-size:14px;
            padding:0 4px;
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
    show_spinner="Fetching latest Excel workbook..."
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
            "SharePoint returned an HTML/login page "
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

    workbook = load_workbook(url)

    frames = []
    sheets_used = []

    for sheet_name, raw_df in workbook.items():

        sheet_name = str(
            sheet_name
        ).strip()

        # Only monthly sheets
        if sheet_name not in MONTH_ORDER:
            continue

        if raw_df is None:
            continue

        if raw_df.empty:
            continue

        df = raw_df.copy()

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        # Sheet name is authoritative.
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
            "Expected Apr, May, Jun, Jul, Aug, etc."
        )

    combined = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    # ========================================================
    # NUMERIC COLUMNS
    # ========================================================

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

    # ========================================================
    # DATES
    # ========================================================

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

    # ========================================================
    # MONTH
    # ========================================================

    combined["Month"] = combined[
        "__Dashboard_Month"
    ]

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
    # Calculated FR Qty
    # --------------------------------------------------------

    if oq and iq:

        df[
            "__Calculated_FR_Qty"
        ] = np.where(
            df[oq] != 0,
            df[iq]
            / df[oq]
            * 100,
            np.nan,
        )

    else:

        df[
            "__Calculated_FR_Qty"
        ] = np.nan

    # --------------------------------------------------------
    # Calculated FR Value
    # --------------------------------------------------------

    if ov and iv:

        df[
            "__Calculated_FR_Value"
        ] = np.where(
            df[ov] != 0,
            df[iv]
            / df[ov]
            * 100,
            np.nan,
        )

    else:

        df[
            "__Calculated_FR_Value"
        ] = np.nan

    # --------------------------------------------------------
    # Official FR
    # --------------------------------------------------------

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

    return df


# ============================================================
# MONTHLY AGGREGATION
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

    invoice = resolve_col(
        CONFIG["invoice_number"],
        df.columns,
    )

    aggregation = {}

    if oq:

        aggregation[
            "order_qty"
        ] = (
            oq,
            "sum",
        )

    if iq:

        aggregation[
            "invoice_qty"
        ] = (
            iq,
            "sum",
        )

    if ov:

        aggregation[
            "order_value"
        ] = (
            ov,
            "sum",
        )

    if iv:

        aggregation[
            "invoice_value"
        ] = (
            iv,
            "sum",
        )

    if sale:

        aggregation[
            "sale_loss"
        ] = (
            sale,
            "sum",
        )

    if oid:

        aggregation[
            "orders"
        ] = (
            oid,
            "nunique",
        )

    if invoice:

        aggregation[
            "invoices"
        ] = (
            invoice,
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
        .agg(
            **aggregation
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Qty FR
    # --------------------------------------------------------

    if (
        "order_qty"
        in result.columns
        and "invoice_qty"
        in result.columns
    ):

        result[
            "fr_qty"
        ] = np.where(
            result[
                "order_qty"
            ] != 0,

            result[
                "invoice_qty"
            ]
            /
            result[
                "order_qty"
            ]
            * 100,

            np.nan,
        )

        result[
            "pending_qty"
        ] = (
            result[
                "order_qty"
            ]
            -
            result[
                "invoice_qty"
            ]
        )

    # --------------------------------------------------------
    # Value FR
    # --------------------------------------------------------

    if (
        "order_value"
        in result.columns
        and "invoice_value"
        in result.columns
    ):

        result[
            "fr_value"
        ] = np.where(
            result[
                "order_value"
            ] != 0,

            result[
                "invoice_value"
            ]
            /
            result[
                "order_value"
            ]
            * 100,

            np.nan,
        )

        result[
            "pending_value"
        ] = (
            result[
                "order_value"
            ]
            -
            result[
                "invoice_value"
            ]
        )

    result["__sort"] = (
        result["Month"]
        .apply(month_sort_key)
    )

    result = (
        result
        .sort_values(
            "__sort"
        )
        .drop(
            columns="__sort"
        )
    )

    return result


# ============================================================
# CUSTOMER SUMMARY
# ============================================================

def build_customer_summary(
    filtered
):

    customer_col = CONFIG[
        "customer"
    ]

    order_col = CONFIG[
        "order_id"
    ]

    invoice_col = CONFIG[
        "invoice_number"
    ]

    oq_col = CONFIG[
        "order_qty"
    ]

    iq_col = CONFIG[
        "invoice_qty"
    ]

    sale_col = CONFIG[
        "sale_loss"
    ]

    tat_col = CONFIG[
        "actual_delivery_days"
    ]

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

    if order_col in filtered.columns:

        aggregation[
            "order_count"
        ] = (
            order_col,
            "nunique",
        )

    if invoice_col in filtered.columns:

        aggregation[
            "invoice_count"
        ] = (
            invoice_col,
            lambda x:
            x.dropna()
            .astype(str)
            .nunique(),
        )

    if sale_col in filtered.columns:

        aggregation[
            "sale_loss"
        ] = (
            sale_col,
            "sum",
        )

    if tat_col in filtered.columns:

        # Avoid obvious date-serial / corrupted TAT values.
        # Normal delivery TAT should not be 172472 days.
        tat_temp = filtered.copy()

        tat_temp["__TAT_Clean"] = pd.to_numeric(
            tat_temp[tat_col],
            errors="coerce",
        )

        tat_temp.loc[
            (
                tat_temp["__TAT_Clean"] < 0
            )
            |
            (
                tat_temp["__TAT_Clean"] > 365
            ),
            "__TAT_Clean",
        ] = np.nan

        tat_summary = (
            tat_temp
            .groupby(
                customer_col,
                dropna=False,
            )["__TAT_Clean"]
            .mean()
            .reset_index(
                name="tat_avg"
            )
        )

    summary = (
        filtered
        .groupby(
            customer_col,
            dropna=False,
        )
        .agg(
            **aggregation
        )
        .reset_index()
    )

    if tat_col in filtered.columns:

        summary = summary.merge(
            tat_summary,
            on=customer_col,
            how="left",
        )

    summary[
        "fill_rate"
    ] = np.where(
        summary[
            "order_qty"
        ] != 0,

        summary[
            "invoice_qty"
        ]
        /
        summary[
            "order_qty"
        ]
        * 100,

        np.nan,
    )

    return summary


# ============================================================
# CUSTOMER DETAIL DIALOG
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

    customer_col = CONFIG[
        "customer"
    ]

    rows = filtered[
        filtered[
            customer_col
        ]
        .astype(str)
        ==
        str(customer_name)
    ].copy()

    if rows.empty:

        st.warning(
            "No matching order rows found."
        )

        return

    # --------------------------------------------------------
    # Calculate row-level Fill Rate
    # --------------------------------------------------------

    rows[
        "Fill Rate"
    ] = np.where(

        rows[
            CONFIG["order_qty"]
        ] != 0,

        rows[
            CONFIG["invoice_qty"]
        ]
        /
        rows[
            CONFIG["order_qty"]
        ]
        * 100,

        np.nan,
    )

    # --------------------------------------------------------
    # Original important fields
    # --------------------------------------------------------

    preferred_columns = [

        CONFIG[
            "wh_receiving_date"
        ],

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

        CONFIG[
            "actual_delivery_days"
        ],

        CONFIG["standard_tat"],

        CONFIG["variance"],

        CONFIG["awb"],

        CONFIG["courier"],

        CONFIG["mode"],

        CONFIG[
            "delivery_status"
        ],

        CONFIG[
            "delivery_date"
        ],

        CONFIG[
            "final_remarks"
        ],
    ]

    columns_to_show = []
    seen = set()

    for requested in preferred_columns:

        if requested == "Fill Rate":

            columns_to_show.append(
                requested
            )

            continue

        actual = resolve_col(
            requested,
            rows.columns,
        )

        if (
            actual
            and actual not in seen
        ):

            columns_to_show.append(
                actual
            )

            seen.add(actual)

    # --------------------------------------------------------
    # Additional operational fields
    # --------------------------------------------------------

    additional_columns = [

        CONFIG[
            "order_received_date"
        ],

        CONFIG[
            "order_upload_date"
        ],

        CONFIG["channel"],

        CONFIG["zone"],

        CONFIG[
            "order_category"
        ],

        CONFIG[
            "external_document"
        ],

        CONFIG[
            "order_value"
        ],

        CONFIG[
            "invoice_value"
        ],

        CONFIG[
            "invoice_time"
        ],

        CONFIG[
            "dispatch_to_delivery"
        ],

        CONFIG["otd_bucket"],

        CONFIG["order_to_wh"],

        CONFIG["oti"],

        CONFIG["otd"],

        CONFIG["otde"],

        CONFIG["otw_days"],

        CONFIG["invoice_days"],

        CONFIG["dispatch_days"],

        CONFIG["wh_remarks"],

        CONFIG["wh_remark"],

        CONFIG[
            "logistics_remarks"
        ],

        CONFIG["ho_remarks"],

        CONFIG["omt_remarks"],
    ]

    for requested in additional_columns:

        actual = resolve_col(
            requested,
            rows.columns,
        )

        if (
            actual
            and actual not in seen
        ):

            columns_to_show.append(
                actual
            )

            seen.add(actual)

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    wh_date = resolve_col(
        CONFIG[
            "wh_receiving_date"
        ],
        rows.columns,
    )

    if wh_date:

        display = (
            rows[
                columns_to_show
            ]
            .sort_values(
                by=wh_date,
                ascending=False,
            )
        )

    else:

        display = rows[
            columns_to_show
        ]

    st.caption(
        f"{len(display):,} order rows for "
        f"**{customer_name}**"
    )

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

    numeric_columns = [

        CONFIG["order_qty"],
        CONFIG["invoice_qty"],
        CONFIG["order_value"],
        CONFIG["invoice_value"],

        CONFIG["standard_tat"],
        CONFIG[
            "actual_delivery_days"
        ],

        CONFIG["variance"],

        CONFIG[
            "dispatch_to_delivery"
        ],

        CONFIG["order_to_wh"],
        CONFIG["oti"],
        CONFIG["otd"],
        CONFIG["otde"],

        CONFIG["otw_days"],
        CONFIG["invoice_days"],
        CONFIG["dispatch_days"],

        CONFIG["sale_loss"],
    ]

    for col in numeric_columns:

        if col in display.columns:

            column_config[
                col
            ] = st.column_config.NumberColumn(
                col
            )

    # --------------------------------------------------------
    # Date config
    # --------------------------------------------------------

    date_columns = [

        CONFIG[
            "wh_receiving_date"
        ],

        CONFIG[
            "order_received_date"
        ],

        CONFIG[
            "order_upload_date"
        ],

        CONFIG[
            "invoice_date"
        ],

        CONFIG[
            "dispatch_date"
        ],

        CONFIG[
            "delivery_date"
        ],
    ]

    for col in date_columns:

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
        height=540,
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
# SHAREPOINT SECRET
# ============================================================

sharepoint_url = st.secrets.get(
    CONFIG[
        "sharepoint_secret"
    ],
    "",
)

if not sharepoint_url:

    st.error(
        "SHAREPOINT_EXCEL_URL is not configured "
        "in Streamlit Secrets."
    )

    st.stop()


# ============================================================
# REFRESH BUTTON
# ============================================================

refresh_left, refresh_right = st.columns(
    [8, 1]
)

with refresh_right:

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
        sharepoint_url
    )

    df = add_derived_metrics(
        df
    )

except Exception as e:

    st.error(
        f"Could not load the live Excel file: {e}"
    )

    st.stop()


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [

    CONFIG["customer"],

    CONFIG["order_qty"],

    CONFIG["invoice_qty"],

    CONFIG["order_id"],
]

missing_columns = [

    col

    for col in required_columns

    if resolve_col(
        col,
        df.columns,
    ) is None
]

if missing_columns:

    st.error(
        "Required columns are missing: "
        + ", ".join(
            missing_columns
        )
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
            loaded_sheets,
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

        name_col = resolve_col(
            CONFIG["name"],
            df.columns,
        )

        name_options = (
            sorted(
                df[name_col]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if name_col
            else []
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

        selected_categories = (
            st.multiselect(
                "Category",
                category_options,
            )
        )

    # --------------------------------------------------------
    # Channel
    # --------------------------------------------------------

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

        selected_channels = (
            st.multiselect(
                "Channel",
                channel_options,
            )
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

        selected_zones = (
            st.multiselect(
                "Zone",
                zone_options,
            )
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

        selected_customers = (
            st.multiselect(
                "Customer",
                customer_options,
            )
        )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = df.copy()


if selected_months:

    filtered = filtered[
        filtered["Month"]
        .isin(
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
# EXECUTIVE OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">Executive Overview</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SELECTED MONTHS
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


latest_df = (

    filtered[
        filtered[
            "Month"
        ]
        == latest_month
    ]

    if latest_month

    else filtered
)


previous_df = (

    filtered[
        filtered[
            "Month"
        ]
        == previous_month
    ]

    if previous_month

    else pd.DataFrame()
)


# ============================================================
# EXECUTIVE METRICS
# ============================================================

def calculate_metrics(data):

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

    fill_rate_qty = safe_ratio(
        invoice_qty,
        order_qty,
    )

    fill_rate_value = safe_ratio(
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

    return {

        "order_qty": order_qty,

        "invoice_qty": invoice_qty,

        "fill_rate_qty": fill_rate_qty,

        "pending_qty": pending_qty,

        "order_value": order_value,

        "invoice_value": invoice_value,

        "fill_rate_value": fill_rate_value,

        "sale_loss": sale_loss,

        "pending_value": pending_value,
    }


current = calculate_metrics(
    latest_df
)

previous = (
    calculate_metrics(
        previous_df
    )
    if not previous_df.empty
    else None
)


# ============================================================
# DELTA FUNCTIONS
# ============================================================

def numeric_delta(
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


def percentage_delta(
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
        f"{sign}₹ "
        f"{difference:,.0f}"
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

    # Lower is better
    return (
        "normal"
        if difference < 0
        else "inverse"
    )


# ============================================================
# CURRENT / PREVIOUS MONTH LABEL
# ============================================================

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
# EXECUTIVE ROW 1
#
# Order Qty
# Invoice Qty
# Fill Rate Qty
# Pending Qty
# ============================================================

r1c1, r1c2, r1c3, r1c4 = (
    st.columns(4)
)


# ------------------------------------------------------------
# ORDER QTY
# ------------------------------------------------------------

r1c1.metric(

    "Order Qty",

    format_number(
        current[
            "order_qty"
        ]
    ),

    numeric_delta(
        current[
            "order_qty"
        ],

        previous[
            "order_qty"
        ]
        if previous
        else None,
    )
    if previous
    else None,

)


# ------------------------------------------------------------
# INVOICE QTY
# ------------------------------------------------------------

r1c2.metric(

    "Invoice Qty",

    format_number(
        current[
            "invoice_qty"
        ]
    ),

    numeric_delta(
        current[
            "invoice_qty"
        ],

        previous[
            "invoice_qty"
        ]
        if previous
        else None,
    )
    if previous
    else None,

)


# ------------------------------------------------------------
# FILL RATE QTY
# Higher is better
# ------------------------------------------------------------

r1c3.metric(

    "Fill Rate — Qty",

    format_percent(
        current[
            "fill_rate_qty"
        ]
    ),

    percentage_delta(
        current[
            "fill_rate_qty"
        ],

        previous[
            "fill_rate_qty"
        ]
        if previous
        else None,
    )
    if previous
    else None,

    delta_color=business_delta_color(

        current[
            "fill_rate_qty"
        ],

        previous[
            "fill_rate_qty"
        ]
        if previous
        else None,

        higher_is_better=True,
    ),

)


# ------------------------------------------------------------
# PENDING QTY
# Lower is better
# ------------------------------------------------------------

r1c4.metric(

    "Pending Qty",

    format_number(
        current[
            "pending_qty"
        ]
    ),

    numeric_delta(

        current[
            "pending_qty"
        ],

        previous[
            "pending_qty"
        ]
        if previous
        else None,
    )
    if previous
    else None,

    delta_color=business_delta_color(

        current[
            "pending_qty"
        ],

        previous[
            "pending_qty"
        ]
        if previous
        else None,

        higher_is_better=False,
    ),

)


# ============================================================
# EXECUTIVE ROW 2
#
# Order Value
# Invoice Value
# Fill Rate Value
# Sale Loss
# ============================================================

r2c1, r2c2, r2c3, r2c4 = (
    st.columns(4)
)


# ------------------------------------------------------------
# ORDER VALUE
# ------------------------------------------------------------

r2c1.metric(

    "Order Value",

    format_value(
        current[
            "order_value"
        ]
    ),

    currency_delta(

        current[
            "order_value"
        ],

        previous[
            "order_value"
        ]
        if previous
        else None,
    )
    if previous
    else None,

)


# ------------------------------------------------------------
# INVOICE VALUE
# ------------------------------------------------------------

r2c2.metric(

    "Invoice Value",

    format_value(
        current[
            "invoice_value"
        ]
    ),

    currency_delta(

        current[
            "invoice_value"
        ],

        previous[
            "invoice_value"
        ]
        if previous
        else None,
    )
    if previous
    else None,

)


# ------------------------------------------------------------
# FILL RATE VALUE
# Higher is better
# ------------------------------------------------------------

r2c3.metric(

    "Fill Rate — Value",

    format_percent(
        current[
            "fill_rate_value"
        ]
    ),

    percentage_delta(

        current[
            "fill_rate_value"
        ],

        previous[
            "fill_rate_value"
        ]
        if previous
        else None,
    )
    if previous
    else None,

    delta_color=business_delta_color(

        current[
            "fill_rate_value"
        ],

        previous[
            "fill_rate_value"
        ]
        if previous
        else None,

        higher_is_better=True,
    ),

)


# ------------------------------------------------------------
# SALE LOSS
# Lower is better
# ------------------------------------------------------------

r2c4.metric(

    "Sale Loss",

    format_value(
        current[
            "sale_loss"
        ]
    ),

    currency_delta(

        current[
            "sale_loss"
        ],

        previous[
            "sale_loss"
        ]
        if previous
        else None,
    )
    if previous
    else None,

    delta_color=business_delta_color(

        current[
            "sale_loss"
        ],

        previous[
            "sale_loss"
        ]
        if previous
        else None,

        higher_is_better=False,
    ),

)


# ============================================================
# MAIN TABS
# ============================================================

tab_mom, tab_customer, tab_category = (
    st.tabs(
        [
            "📈 MOM Overview",
            "🏪 Customer Wise",
            "📦 Category Wise",
        ]
    )
)


# ============================================================
# MOM OVERVIEW
# ============================================================

with tab_mom:

    monthly = aggregate_month(
        filtered
    )

    # ========================================================
    # 1. FIRST CHART:
    # MONTH-ON-MONTH FILL RATE
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        'Month-on-Month Fill Rate Comparison'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Monthly comparison of Fill Rate by Quantity and Value."
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
        fr_long[
            "Metric"
        ]
        .replace(
            {
                "fr_qty":
                    "Fill Rate Qty",

                "fr_value":
                    "Fill Rate Value",
            }
        )
    )

    # --------------------------------------------------------
    # Line chart
    # --------------------------------------------------------

    fr_chart = (

        alt.Chart(
            fr_long
        )

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

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    fr_labels = (

        alt.Chart(
            fr_long
        )

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
        '<div class="section-title">'
        'Month-on-Month Table'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Choose the columns you want to see. You can change this anytime."
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

    default_columns = [

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

                "Columns",

                list(
                    mom_columns.keys()
                ),

                default=default_columns,

                key="mom_table_columns",
            )
        )

    if not selected_mom_columns:

        selected_mom_columns = (
            default_columns
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
    # Format
    # --------------------------------------------------------

    for col in mom_display.columns:

        if col == "Month":
            continue

        if (
            "Fill Rate"
            in col
        ):

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
            "Value"
            in col
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

    fr_compare = monthly[
        [
            "Month",
            "fr_qty",
            "fr_value",
        ]
    ].melt(

        id_vars=[
            "Month"
        ],

        var_name="Metric",

        value_name="Fill Rate",
    )

    fr_compare["Metric"] = (
        fr_compare[
            "Metric"
        ]
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

        p1, p2, p3, p4 = (
            st.columns(4)
        )

        p1.metric(

            "Fill Rate Qty",

            format_percent(
                current_mom[
                    "fr_qty"
                ]
            ),

            percentage_delta(
                current_mom[
                    "fr_qty"
                ],

                previous_mom[
                    "fr_qty"
                ],
            ),

            delta_color=(
                "normal"
                if current_mom[
                    "fr_qty"
                ]
                >
                previous_mom[
                    "fr_qty"
                ]
                else "inverse"
            ),
        )

        p2.metric(

            "Fill Rate Value",

            format_percent(
                current_mom[
                    "fr_value"
                ]
            ),

            percentage_delta(
                current_mom[
                    "fr_value"
                ],

                previous_mom[
                    "fr_value"
                ],
            ),

            delta_color=(
                "normal"
                if current_mom[
                    "fr_value"
                ]
                >
                previous_mom[
                    "fr_value"
                ]
                else "inverse"
            ),
        )

        p3.metric(

            "Pending Qty",

            format_number(
                current_mom[
                    "pending_qty"
                ]
            ),

            numeric_delta(
                current_mom[
                    "pending_qty"
                ],

                previous_mom[
                    "pending_qty"
                ],
            ),

            delta_color=(
                "normal"
                if current_mom[
                    "pending_qty"
                ]
                <
                previous_mom[
                    "pending_qty"
                ]
                else "inverse"
            ),
        )

        p4.metric(

            "Sale Loss",

            format_value(
                current_mom[
                    "sale_loss"
                ]
            ),

            currency_delta(
                current_mom[
                    "sale_loss"
                ],

                previous_mom[
                    "sale_loss"
                ],
            ),

            delta_color=(
                "normal"
                if current_mom[
                    "sale_loss"
                ]
                <
                previous_mom[
                    "sale_loss"
                ]
                else "inverse"
            ),
        )

        st.caption(
            f"{previous_mom['Month']} → "
            f"{current_mom['Month']}"
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
        '<div class="section-title">'
        'Customer Wise Performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Click a customer name to open the complete order-level details."
    )

    customer_summary = (
        build_customer_summary(
            filtered
        )
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    customer_search = st.text_input(
        "🔍 Search Customer",
        key="customer_search",
    )

    shop_view = (
        customer_summary.copy()
    )

    if customer_search:

        shop_view = shop_view[
            shop_view[
                CONFIG[
                    "customer"
                ]
            ]
            .astype(str)
            .str.contains(
                customer_search,
                case=False,
                na=False,
            )
        ]

    st.caption(
        f"{len(shop_view):,} of "
        f"{len(customer_summary):,} customers"
    )


    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    metric_options = [

        "Order (count)",

        "Invoice (count)",

        "Order Qty",

        "Invoice Qty",

        "Fill Rate",

        "Sale Loss (In Lacs)",

        "TAT (avg)",
    ]

    available_metric_options = []

    for metric in metric_options:

        if metric == "Order (count)":

            if (
                "order_count"
                in shop_view.columns
            ):

                available_metric_options.append(
                    metric
                )

        elif metric == "Invoice (count)":

            if (
                "invoice_count"
                in shop_view.columns
            ):

                available_metric_options.append(
                    metric
                )

        elif metric == "Sale Loss (In Lacs)":

            if (
                "sale_loss"
                in shop_view.columns
            ):

                available_metric_options.append(
                    metric
                )

        elif metric == "TAT (avg)":

            if (
                "tat_avg"
                in shop_view.columns
            ):

                available_metric_options.append(
                    metric
                )

        else:

            available_metric_options.append(
                metric
            )

    with st.expander(
        "⚙️ Choose Customer Table Columns",
        expanded=False,
    ):

        visible_metrics = (
            st.multiselect(

                "Columns",

                available_metric_options,

                default=available_metric_options,

                key="customer_visible_cols",
            )
        )

    if not visible_metrics:

        visible_metrics = (
            available_metric_options
        )


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    SORT_KEY_MAP = {

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


    if (
        "customer_sort_col"
        not in st.session_state
    ):

        st.session_state[
            "customer_sort_col"
        ] = None

        st.session_state[
            "customer_sort_dir"
        ] = None


    if (
        "selected_customer"
        not in st.session_state
    ):

        st.session_state[
            "selected_customer"
        ] = None


    def cycle_customer_sort(
        column
    ):

        current_col = (
            st.session_state[
                "customer_sort_col"
            ]
        )

        current_dir = (
            st.session_state[
                "customer_sort_dir"
            ]
        )

        if current_col != column:

            st.session_state[
                "customer_sort_col"
            ] = column

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
        column
    ):

        if (
            st.session_state[
                "customer_sort_col"
            ]
            != column
        ):

            return ""

        return (
            " ▲"
            if
            st.session_state[
                "customer_sort_dir"
            ]
            == "asc"
            else " ▼"
        )


    # --------------------------------------------------------
    # Apply sorting
    # --------------------------------------------------------

    active_sort = (
        st.session_state[
            "customer_sort_col"
        ]
    )

    active_direction = (
        st.session_state[
            "customer_sort_dir"
        ]
    )

    if active_sort:

        sort_column = (

            CONFIG[
                "customer"
            ]

            if active_sort
            == "__customer__"

            else active_sort
        )

        shop_view = (
            shop_view
            .sort_values(
                sort_column,

                ascending=(
                    active_direction
                    == "asc"
                ),

                na_position="last",
            )
        )


    # --------------------------------------------------------
    # TABLE WIDTHS
    # --------------------------------------------------------

    table_widths = (
        [3]
        +
        [1]
        *
        len(
            visible_metrics
        )
    )


    # ========================================================
    # CUSTOMER TABLE
    # ========================================================

    with st.container(
        key="fillrate_table"
    ):

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = st.columns(
            table_widths,
            gap="small",
        )

        if header[0].button(

            "Customer Name"
            +
            customer_arrow(
                "__customer__"
            ),

            key="customer_header",

            use_container_width=True,
        ):

            cycle_customer_sort(
                "__customer__"
            )

            st.rerun()


        for index, metric in enumerate(
            visible_metrics,
            start=1,
        ):

            sort_key = SORT_KEY_MAP[
                metric
            ]

            if header[index].button(

                metric
                +
                customer_arrow(
                    sort_key
                ),

                key=(
                    "customer_header_"
                    + sort_key
                ),

                use_container_width=True,
            ):

                cycle_customer_sort(
                    sort_key
                )

                st.rerun()


        # ----------------------------------------------------
        # Rows
        # ----------------------------------------------------

        for row_index, row in (
            shop_view
            .reset_index(
                drop=True
            )
            .iterrows()
        ):

            row_columns = st.columns(
                table_widths,
                gap="small",
            )

            # ----------------------------------------------
            # Customer name
            # ----------------------------------------------

            customer_name = str(
                row[
                    CONFIG[
                        "customer"
                    ]
                ]
            )

            if row_columns[
                0
            ].button(

                customer_name,

                key=(
                    "customer_row_"
                    f"{row_index}_"
                    f"{hash(customer_name)}"
                ),

                use_container_width=True,
            ):

                st.session_state[
                    "selected_customer"
                ] = customer_name

                st.rerun()


            # ----------------------------------------------
            # Metrics
            # ----------------------------------------------

            for col_index, metric in enumerate(
                visible_metrics,
                start=1,
            ):

                target = row_columns[
                    col_index
                ]

                if metric == "Order (count)":

                    center(
                        target,

                        format_number(
                            row[
                                "order_count"
                            ]
                        ),
                    )

                elif metric == "Invoice (count)":

                    center(
                        target,

                        format_number(
                            row[
                                "invoice_count"
                            ]
                        ),
                    )

                elif metric == "Order Qty":

                    center(
                        target,

                        format_number(
                            row[
                                "order_qty"
                            ]
                        ),
                    )

                elif metric == "Invoice Qty":

                    center(
                        target,

                        format_number(
                            row[
                                "invoice_qty"
                            ]
                        ),
                    )

                elif metric == "Fill Rate":

                    center(
                        target,

                        format_percent(
                            row[
                                "fill_rate"
                            ]
                        ),
                    )

                elif (
                    metric
                    == "Sale Loss (In Lacs)"
                ):

                    center(
                        target,

                        (
                            "—"
                            if pd.isna(
                                row[
                                    "sale_loss"
                                ]
                            )

                            else
                            f"₹ "
                            f"{row['sale_loss']:,.2f}"
                        ),
                    )

                elif metric == "TAT (avg)":

                    center(
                        target,

                        (
                            "—"
                            if pd.isna(
                                row[
                                    "tat_avg"
                                ]
                            )

                            else
                            f"{row['tat_avg']:.1f}"
                        ),
                    )


    # --------------------------------------------------------
    # Detail popup
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
            CONFIG[
                "category"
            ],

            dropna=False,
        )

        .agg(

            order_qty=(
                CONFIG[
                    "order_qty"
                ],

                "sum",
            ),

            invoice_qty=(
                CONFIG[
                    "invoice_qty"
                ],

                "sum",
            ),

            order_value=(
                CONFIG[
                    "order_value"
                ],

                "sum",
            ),

            invoice_value=(
                CONFIG[
                    "invoice_value"
                ],

                "sum",
            ),

            sale_loss=(
                CONFIG[
                    "sale_loss"
                ],

                "sum",
            ),

            orders=(
                CONFIG[
                    "order_id"
                ],

                "nunique",
            ),
        )

        .reset_index()
    )


    # --------------------------------------------------------
    # FR
    # --------------------------------------------------------

    category_summary[
        "fr_qty"
    ] = np.where(

        category_summary[
            "order_qty"
        ] != 0,

        category_summary[
            "invoice_qty"
        ]
        /
        category_summary[
            "order_qty"
        ]
        * 100,

        np.nan,
    )


    category_summary[
        "fr_value"
    ] = np.where(

        category_summary[
            "order_value"
        ] != 0,

        category_summary[
            "invoice_value"
        ]
        /
        category_summary[
            "order_value"
        ]
        * 100,

        np.nan,
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

                CONFIG[
                    "category"
                ],

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

                CONFIG[
                    "category"
                ]:
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
    # CATEGORY FR CHART
    # ========================================================

    st.markdown(
        '<div class="section-title">'
        'Category Fill Rate'
        '</div>',
        unsafe_allow_html=True,
    )

    category_chart = (

        alt.Chart(
            category_summary
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
                    labelAngle=0
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
            category_summary
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
        +
        category_labels,

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
    f"Filtered rows: "
    f"{len(filtered):,}"
    f"  |  "
    f"Updated: "
    f"{datetime.now().strftime('%d-%m-%Y %H:%M')}"
)
