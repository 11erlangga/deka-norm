import numpy as np
import pandas as pd
import streamlit as st

from src.queries import get_available_filters, get_norm_table, get_summary_stats


@st.cache_data
def load_norms(gender=None, ses=None, category=None, sub_category=None, year=None):
    """Load norm table dengan filter opsional. Parameter dikirim ke query layer."""
    return get_norm_table(
        gender=gender,
        ses=ses,
        category=category,
        sub_category=sub_category,
        year=year,
    )


@st.cache_data
def load_filters():
    """Load semua nilai unik untuk filter dropdown."""
    return get_available_filters()


@st.cache_data
def load_stats():
    """Load summary statistics (project/respondent/response/variable count)."""
    return get_summary_stats()


stats = load_stats()
filters = load_filters()

NORM_GRADES = [
    "Top 25%",
    "Average 50%",
    "Bottom 25%",
]

variable_names = filters["variable_names"]
scales = sorted(set(v["scale_max"] for v in filters["variables"]))

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Norm Database",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# COLOR TOKENS
# =========================================================
NAVY = "#1B2A57"
NAVY_DARK = "#141F42"
ORANGE = "#F5A623"
ORANGE_SOFT = "#FCEFD8"
BG = "#EEF2F8"
CARD_BG = "#FFFFFF"
TEXT_MUTED = "#9098AC"
TEXT_DARK = "#111827"
BORDER = "#E3E8F1"

# =========================================================
# SESSION STATE / FILTER DEFAULTS
# =========================================================
FILTER_DEFAULTS = {
    "f_parameter": [],
    "f_skala": "Semua",
    "f_norm_grade": "Semua",
    "f_category": "Semua",
    "f_sub_category": "Semua",
    "f_gender": "Semua",
    "f_ses": "Semua",
}

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
for k, v in FILTER_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_filters():
    for k, v in FILTER_DEFAULTS.items():
        st.session_state[k] = v


# =========================================================
# GLOBAL CSS
# =========================================================
st.markdown(
    f"""
<style>
.block-container {{ padding-top: 1.6rem; padding-bottom: 2rem; padding-left: 2.4rem; padding-right: 2.4rem; }}
[data-testid="stAppViewContainer"] {{ background-color: {BG}; }}

/* ---------- SIDEBAR ---------- */
[data-testid="stSidebar"] {{
    background-color: {NAVY};
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0rem; }}
[data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
    color: #D7DDEE;
}}
.brand {{
    font-size: 19px; font-weight: 800; color: #FFFFFF;
    padding: 22px 20px 18px 20px; letter-spacing: 0.2px;
}}

/* nav + reset buttons share stButton, base style = nav look */
[data-testid="stSidebar"] [data-testid="stButton"] button {{
    background-color: transparent;
    color: #C7CEE3;
    border: none;
    border-radius: 8px;
    text-align: left;
    justify-content: flex-start;
    font-weight: 600;
    font-size: 15px;
    padding: 9px 18px;
    margin: 0 14px 4px 14px;
    width: calc(100% - 28px);
    box-shadow: none;
}}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
    background-color: rgba(255,255,255,0.08);
    color: #FFFFFF;
}}
.st-key-reset_btn button {{
    background-color: transparent !important;
    color: {ORANGE} !important;
    border: 1.5px solid {ORANGE} !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    text-align: center !important;
    justify-content: center !important;
    margin-top: 6px !important;
}}
.st-key-reset_btn button:hover {{
    background-color: rgba(245,166,35,0.12) !important;
}}
.side-divider {{ border: none; border-top: 1px solid rgba(255,255,255,0.15); margin: 6px 14px 10px 14px; }}

/* sidebar filter expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {{
    background-color: transparent;
    border: 1px solid {ORANGE};
    border-radius: 8px;
    margin: 0 14px 10px 14px;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
    color: {ORANGE} !important;
    font-weight: 700;
}}
[data-testid="stSidebar"] [data-testid="stExpander"] svg {{ fill: {ORANGE}; }}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
    color: #C7CEE3 !important; font-size: 12.5px; font-weight: 700;
    margin-bottom: 2px;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    border-radius: 6px !important;
    border: 1px solid #FFFFFF !important;
    min-height: 34px !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] span {{ color: {TEXT_DARK} !important; font-size: 13px; }}

/* ---------- MAIN AREA ---------- */
.breadcrumb {{ font-size: 14px; margin-bottom: 8px; }}
.bc-muted {{ color: #A7AEC0; }}
.bc-sep {{ color: #A7AEC0; margin: 0 4px; }}
.bc-active {{ color: {TEXT_DARK}; font-weight: 700; }}

.page-title {{ color: {TEXT_DARK}; font-weight: 800; font-size: 28px; margin: 2px 0 2px 0; }}
.page-subtitle {{ color: {TEXT_MUTED}; font-size: 14.5px; margin-bottom: 22px; }}

[data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p {{
    color: {NAVY} !important; font-weight: 700 !important; font-size: 14px;
}}
[data-testid="stMainBlockContainer"] [data-baseweb="select"] > div {{
    background-color: #FFFFFF !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
    min-height: 42px !important;
}}
[data-baseweb="tag"] {{
    background-color: {ORANGE} !important;
    color: {NAVY} !important;
    border-radius: 5px !important;
}}
[data-baseweb="tag"] span {{ color: {NAVY} !important; font-weight: 700; }}

/* KPI cards */
.kpi-card {{
    background-color: {CARD_BG};
    border-radius: 14px;
    padding: 16px 20px 18px 20px;
    box-shadow: 0 2px 12px rgba(20,30,60,0.07);
    border: 1px solid #F1F3F9;
    min-height: 92px;
}}
.kpi-label {{ font-size: 13px; font-weight: 700; color: #A8AFC1; margin-bottom: 8px; }}
.kpi-value {{ font-size: 26px; font-weight: 800; color: {NAVY}; }}

/* Data table */
.norm-table-wrap {{
    background-color: {CARD_BG};
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(20,30,60,0.07);
    border: 1px solid #F1F3F9;
    overflow: hidden;
}}
.norm-table-scroll {{ max-height: 480px; overflow-y: auto; }}
table.norm-table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; }}
table.norm-table thead th {{
    position: sticky; top: 0;
    background-color: {CARD_BG};
    color: {NAVY}; font-weight: 800;
    text-align: left; padding: 14px 16px;
    border-bottom: 2px solid {BORDER};
    z-index: 1;
}}
table.norm-table tbody td {{
    padding: 11px 16px; color: #6B7280;
    border-bottom: 1px solid #F4D9A6;
    white-space: nowrap;
}}
table.norm-table tbody tr:hover td {{ background-color: #FFFBF2; }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SIDEBAR CONTENT
# =========================================================
with st.sidebar:
    st.markdown('<div class="brand">Norm Database</div>', unsafe_allow_html=True)

    for item in ["Dashboard", "Data", "About"]:
        if st.button(item, key=f"nav_{item.lower()}", use_container_width=True):
            st.session_state.page = item
            st.rerun()

    active_key = f"nav_{st.session_state.page.lower()}"
    st.markdown(
        f"""
    <style>
    .st-key-{active_key} button {{
        background-color: {ORANGE} !important;
        color: {NAVY} !important;
        font-weight: 800 !important;
    }}
    .st-key-{active_key} button:hover {{
        background-color: {ORANGE} !important;
        color: {NAVY} !important;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="side-divider">', unsafe_allow_html=True)

    if st.session_state.page == "Dashboard":
        st.button(
            "Reset filter",
            key="reset_btn",
            use_container_width=True,
            on_click=reset_filters,
        )

        with st.expander("Filter Data", expanded=False):
            st.selectbox(
                "Category",
                ["Semua"] + filters["categories"],
                key="f_category",
            )

            st.selectbox(
                "Sub-Category",
                ["Semua"] + filters["sub_categories"],
                key="f_sub_category",
            )

            st.selectbox(
                "Gender",
                ["Semua"] + filters["genders"],
                key="f_gender",
            )

            st.selectbox(
                "SES",
                ["Semua"] + filters["ses"],
                key="f_ses",
            )


# =========================================================
# HELPERS
# =========================================================
def fmt_int(n):
    return f"{n:,.0f}".replace(",", ".")


def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "None"
    return f"{v:.1f}%"


def fmt_score(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v:.2f}"


def render_table(table_df):
    cols = [
        "Parameter",
        "Skala",
        "Norm Grade",
        "Base (N)",
        "TB%",
        "TB2%",
        "TB3%",
        "Mean Score",
    ]
    html = [
        '<div class="norm-table-wrap"><div class="norm-table-scroll"><table class="norm-table"><thead><tr>'
    ]
    for c in cols:
        html.append(f"<th>{c}</th>")
    html.append("</tr></thead><tbody>")
    for _, r in table_df.iterrows():
        html.append("<tr>")
        html.append(f"<td>{r['Parameter']}</td>")
        html.append(f"<td>{r['Skala']}</td>")
        html.append(f"<td>{r['Norm Grade']}</td>")
        html.append(f"<td>{fmt_int(r['Base (N)'])}</td>")
        html.append(f"<td>{fmt_pct(r['TB%'])}</td>")
        html.append(f"<td>{fmt_pct(r['TB2%'])}</td>")
        html.append(f"<td>{fmt_pct(r['TB3%'])}</td>")
        html.append(f"<td>{fmt_score(r['Mean Score'])}</td>")
        html.append("</tr>")
    html.append("</tbody></table></div></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def kpi_card(col, label, value):
    col.markdown(
        f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def breadcrumb(page_name):
    st.markdown(
        f"""
    <div class="breadcrumb">
        <span class="bc-muted">Pages</span><span class="bc-sep">/</span><span class="bc-active">{page_name}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def weighted_avg(sub, col):
    valid = sub.dropna(subset=[col])
    if valid.empty or valid["Base (N)"].sum() == 0:
        return None
    return float((valid[col] * valid["Base (N)"]).sum() / valid["Base (N)"].sum())


# =========================================================
# PAGE: DASHBOARD
# =========================================================
if st.session_state.page == "Dashboard":
    breadcrumb("Dashboard")
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Top Box / Top 2 Boxes / Top 3 Boxes / Mean Score</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.multiselect(
            "Parameter",
            options=variable_names,
            key="f_parameter",
            placeholder="Semua",
        )
    with c2:
        st.selectbox("Skala", ["Semua"] + [f"{s}pts" for s in scales], key="f_skala")
    with c3:
        st.selectbox("Norm Grade", ["Semua"] + NORM_GRADES, key="f_norm_grade")

    # FIX: filter gender/ses/category/sub_category sekarang dikirim ke query layer
    # supaya filtering terjadi di SQL, bukan di DataFrame yang sudah pooled
    gender_val = (
        st.session_state.f_gender if st.session_state.f_gender != "Semua" else None
    )
    ses_val = st.session_state.f_ses if st.session_state.f_ses != "Semua" else None
    category_val = (
        st.session_state.f_category if st.session_state.f_category != "Semua" else None
    )
    sub_category_val = (
        st.session_state.f_sub_category
        if st.session_state.f_sub_category != "Semua"
        else None
    )

    df = load_norms(
        gender=gender_val,
        ses=ses_val,
        category=category_val,
        sub_category=sub_category_val,
    )

    # Filter in-memory: parameter, skala, norm_grade (kolom-kolom ini ada di DataFrame)
    fdf = df.copy()
    if st.session_state.f_parameter:
        fdf = fdf[fdf["Parameter"].isin(st.session_state.f_parameter)]
    if st.session_state.f_skala != "Semua":
        fdf = fdf[fdf["Skala"] == st.session_state.f_skala]
    if st.session_state.f_norm_grade != "Semua":
        fdf = fdf[fdf["Norm Grade"] == st.session_state.f_norm_grade]

    base_n = int(fdf["Base (N)"].sum()) if not fdf.empty else 0
    tb = weighted_avg(fdf, "TB%")
    tb2 = weighted_avg(fdf, "TB2%")
    tb3 = weighted_avg(fdf, "TB3%")
    mean_score = weighted_avg(fdf, "Mean Score")

    k1, k2, k3, k4, k5 = st.columns(5)
    kpi_card(k1, "Base (N)", fmt_int(base_n))
    kpi_card(k2, "Top Box %", fmt_pct(tb))
    kpi_card(k3, "Top 2 Box %", fmt_pct(tb2))
    kpi_card(k4, "Top 3 Box %", fmt_pct(tb3))
    kpi_card(k5, "Mean Score", fmt_score(mean_score))

    st.write("")
    if fdf.empty:
        st.info("Tidak ada data untuk kombinasi filter ini.")
    else:
        render_table(fdf)

# =========================================================
# PAGE: DATA
# =========================================================
elif st.session_state.page == "Data":
    breadcrumb("Data")
    st.markdown('<div class="page-title">Data</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Data respons survei</div>', unsafe_allow_html=True
    )

    k1, k2, k3, k4 = st.columns(4)
    kpi_card(k1, "Total Project", fmt_int(stats["projects"]))
    kpi_card(k2, "Total Responden", fmt_int(stats["respondents"]))
    kpi_card(k3, "Total Response", fmt_int(stats["responses"]))
    kpi_card(k4, "Total Parameter", fmt_int(stats["variables"]))

    st.write("")
    # Halaman Data selalu tampilkan data global (tanpa filter sidebar)
    render_table(load_norms())

# =========================================================
# PAGE: ABOUT
# =========================================================
else:
    breadcrumb("About")
    st.markdown('<div class="page-title">About</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Informasi Dashboard</div>', unsafe_allow_html=True
    )

    st.markdown(
        f"""
    <div class="kpi-card" style="min-height:auto;">
        <div style="color:{TEXT_DARK}; font-size:14.5px; line-height:1.7;">
            <b>Norm Database</b> adalah dashboard internal untuk menelusuri data norma hasil survei
            sensori &amp; konsumen lintas proyek. Gunakan menu <b>Dashboard</b> untuk melihat ringkasan
            Top Box / Top 2 Box / Top 3 Box / Mean Score per parameter, dan menu <b>Data</b> untuk
            melihat keseluruhan respons survei.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
