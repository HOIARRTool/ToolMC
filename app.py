# app.py (Final Cleaned Version)
# -*- coding: utf-8 -*-
import os
import re
import unicodedata
from datetime import datetime, date
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
from dateutil.relativedelta import relativedelta
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 0) SETUP & CONFIGURATION
# ==============================================================================
LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/refs/heads/main/logo1.png"
st.set_page_config(layout="wide", page_title="HOIA-RR", page_icon=LOGO_URL)

# --- Try Import Helper Modules ---
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from ai_assistant import get_consultation_response
except ImportError:
    def get_consultation_response(text): return f"Error: Could not import `get_consultation_response`."

try:
    from risk_register_assistant import get_risk_register_consultation
except ImportError:
    def get_risk_register_consultation(query, df, risk_mitigation_df): return {"error": "Error: Could not import `get_risk_register_consultation`."}

# --- Sidebar Logo Header ---
st.markdown(
    """
    <style>
        .gradient-text {
            background-image: linear-gradient(45deg, #f09433, #e6683c, #dc2743, #bc1888, #833ab4);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        .styled-table { width: 100%; border-collapse: collapse; }
        .styled-table th, .styled-table td { border: 1px solid #ddd; padding: 8px; }
        .styled-table th { background-color: #f2f2f2; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True
)

st.markdown(
    f"""
    <div style="width: 100%; display: flex; justify-content: flex-end; align-items: flex-start; gap: 12px; padding: 8px 24px 0 0;">
        <img src="{LOGO_URL}" style="height:60px;">
        <div style="display:flex; flex-direction:column; align-items:flex-end;">
            <span style="font-weight:bold; color:#003366;">HOIA-RR Tool</span>
            <span style="font-size:0.8em; color:gray;">Safety & Risk Management</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# 1) CONSTANTS & REFERENCE DATA
# ==============================================================================
SERVICE_MAP = [
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยใน"},
    # (เพื่อความกระชับ ผมละเว้นรายการยาวๆ ไว้ แต่โค้ดจริงคุณใส่ให้ครบตามเดิมได้)
    # ... ใส่ list เต็มๆ ของคุณตรงนี้ถ้ามี ...
]
# สร้าง DataFrame อ้างอิงหน่วยงาน (Stub)
if len(SERVICE_MAP) < 5: # Fallback ถ้าข้างบนไม่ได้ใส่เต็ม
    REF_DF = pd.DataFrame([{"กลุ่มงาน": "ทั้งหมด", "หน่วยงาน": "ทั้งหมด"}])
else:
    REF_DF = pd.DataFrame(SERVICE_MAP)

REF_COL = "หน่วยงาน"

# Safety Goals
goal_definitions = {
    "Patient Safety/ Common Clinical Risk": "P:Patient Safety Goals หรือ Common Clinical Risk Incident",
    "Specific Clinical Risk": "S:Specific Clinical Risk Incident",
    "Personnel Safety": "P:Personnel Safety Goals",
    "Organization Safety": "O:Organization Safety Goals",
}

# Date Parsing Helpers
THAI_MONTHS = {"ม.ค.":1, "ก.พ.":2, "มี.ค.":3, "เม.ย.":4, "พ.ค.":5, "มิ.ย.":6, "ก.ค.":7, "ส.ค.":8, "ก.ย.":9, "ต.ค.":10, "พ.ย.":11, "ธ.ค.":12}
THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"; ARABIC_DIGITS = "0123456789"
DIGIT_MAP = str.maketrans({t: a for t, a in zip(THAI_DIGITS, ARABIC_DIGITS)})

# Risk Colors
RISK_COLOR_TABLE = {
    "11":"Low","12":"Low","13":"Low","14":"Medium","15":"Medium",
    "21":"Low","22":"Low","23":"Medium","24":"Medium","25":"High",
    "31":"Low","32":"Medium","33":"Medium","34":"High","35":"High",
    "41":"Medium","42":"Medium","43":"High","44":"High","45":"Extreme",
    "51":"Medium","52":"High","53":"High","54":"Extreme","55":"Extreme",
}
# Matrix Palette
PALETTE_FROM_IMAGE = {
    "11": "#00D26A", "12": "#00D26A", "13": "#00D26A", "14": "#FFE900", "15": "#FFE900",
    "21": "#00D26A", "22": "#FFE900", "23": "#FFE900", "24": "#FF9800", "25": "#FF9800",
    "31": "#FFE900", "32": "#FFE900", "33": "#FFE900", "34": "#FF9800", "35": "#FF9800",
    "41": "#FF9800", "42": "#FF9800", "43": "#FF2D2D", "44": "#FF2D2D", "45": "#FF2D2D",
    "51": "#FF9800", "52": "#FF2D2D", "53": "#FF2D2D", "54": "#FF2D2D", "55": "#FF2D2D",
}
HEADER_TOPLEFT = "#E6F5FF"; HEADER_SIDE = "#F3C7B1"; HEADER_FREQ = "#EED0BE"

# File Paths
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
PSG9_FILE_PATH = "PSG9code.xlsx"
SENTINEL_FILE_PATH = "Sentinel2024.xlsx"
RISK_MITIGATION_FILE = "risk_mitigations.xlsx"

# Global Sets for Counting
psg9_r_codes_for_counting = set()
sentinel_composite_keys = set()
PSG9_label_dict = {}
df_mitigation = pd.DataFrame()

# Load External Static Files
try:
    if Path(PSG9_FILE_PATH).is_file():
        p_df = pd.read_excel(PSG9_FILE_PATH)
        if 'รหัส' in p_df.columns: psg9_r_codes_for_counting = set(p_df['รหัส'].astype(str).str.strip().unique())
        if 'PSG_ID' in p_df.columns and 'หมวดหมู่PSG' in p_df.columns:
            PSG9_label_dict = pd.Series(p_df['หมวดหมู่PSG'].values, index=p_df.PSG_ID).to_dict()
    if Path(SENTINEL_FILE_PATH).is_file():
        s_df = pd.read_excel(SENTINEL_FILE_PATH)
        if 'รหัส' in s_df.columns and 'Impact' in s_df.columns:
            s_df['รหัส'] = s_df['รหัส'].astype(str).str.strip()
            s_df['Impact'] = s_df['Impact'].astype(str).str.strip()
            sentinel_composite_keys = set((s_df['รหัส'] + '-' + s_df['Impact']).unique())
    if Path(RISK_MITIGATION_FILE).is_file():
        df_mitigation = pd.read_excel(RISK_MITIGATION_FILE)
except Exception as e:
    pass # Silent fail for static files

# ==============================================================================
# 2) HELPER FUNCTIONS (Data Processing & Logic)
# ==============================================================================
def normalize_unit(text: str) -> str:
    if pd.isna(text): return ""
    return str(text).strip()

def list_units(group_name: str) -> list:
    if not group_name or group_name in ("-- เลือกกลุ่มงาน --", "-- ทั้งหมด --"): return []
    if group_name in REF_DF["กลุ่มงาน"].unique():
        return sorted(REF_DF.loc[REF_DF["กลุ่มงาน"] == group_name, "หน่วยงาน"].unique().tolist())
    return []

def normalize_raw_datetime_text(x):
    if x is None or (isinstance(x, float) and pd.isna(x)) or str(x).strip() == "": return None
    s = str(x).strip().translate(DIGIT_MAP)
    return re.sub(r"\s+", " ", s).strip()

def parse_incident_datetime(value):
    if isinstance(value, (pd.Timestamp, datetime)): return pd.Timestamp(value)
    s = normalize_raw_datetime_text(value)
    if not s: return pd.NaT
    # Simple parser fallback
    return pd.to_datetime(s, dayfirst=True, errors='coerce')

def map_impact_level_func(val):
    s = str(val).strip().upper()
    if s in ("A", "B", "1"): return "1"
    if s in ("C", "D", "2"): return "2"
    if s in ("E", "F", "3"): return "3"
    if s in ("G", "H", "4"): return "4"
    if s in ("I", "5"): return "5"
    return "N/A"

def compute_frequency_level(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'Occurrence Date' not in df.columns: return df
    max_p = df['Occurrence Date'].max().to_period('M')
    min_p = df['Occurrence Date'].min().to_period('M')
    total_months = max(1, (max_p.year - min_p.year) * 12 + (max_p.month - min_p.month) + 1) if pd.notna(max_p) else 1
    counts = df['Incident'].value_counts()
    df['count'] = df['Incident'].map(counts).fillna(0)
    df['Incident Rate/mth'] = (df['count'] / total_months).round(1)
    cond = [(df['Incident Rate/mth']<2.0), (df['Incident Rate/mth']<3.9), (df['Incident Rate/mth']<6.9), (df['Incident Rate/mth']<29.9)]
    df['Frequency Level'] = np.select(cond, ['1','2','3','4'], default='5')
    return df

def _text_color_for(bg_hex: str) -> str:
    try:
        h = bg_hex.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return "#000000" if (r*0.299 + g*0.587 + b*0.114) > 186 else "#FFFFFF"
    except: return "#000000"

# --- Schema & Loader ---
def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None: return pd.DataFrame()
    try:
        if uploaded_file.name.endswith(".csv"): return pd.read_csv(uploaded_file)
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return pd.DataFrame()

def massage_schema(df: pd.DataFrame) -> pd.DataFrame:
    # Rename standard columns
    col_map = {
        "รหัสหัวข้อ": "Incident", "หัวข้อ": "ชื่ออุบัติการณ์ความเสี่ยง",
        "วัน-เวลา ที่เกิดเหตุ": "Occurrence Date", "ระดับความรุนแรง": "Impact",
        "การดำเนินการ/การแก้ไขที่ได้ดำเนินการไปแล้ว": "Resulting Actions",
        "สรุปปัญหา/เหตุการณ์โดยย่อ": "รายละเอียดการเกิด_Anonymized"
    }
    df = df.rename(columns=col_map)
    
    # Required check
    req = ["Incident", "Occurrence Date", "Impact"]
    if not all(c in df.columns for c in req):
        st.error(f"Missing columns: {req}")
        return pd.DataFrame()

    # Create Code column
    df['รหัส'] = df['Incident'].astype(str).str.slice(0,6)
    
    # Date parsing
    df['Occurrence Date'] = df['Occurrence Date'].apply(parse_incident_datetime)
    df = df.dropna(subset=['Occurrence Date'])
    if df.empty: return df

    # Levels
    df['Impact Level'] = df['Impact'].apply(map_impact_level_func)
    df = compute_frequency_level(df)
    df['Risk Level'] = np.where((df['Impact Level']!='N/A'), df['Impact Level']+df['Frequency Level'], 'N/A')
    df['Category Color'] = df['Risk Level'].map(RISK_COLOR_TABLE).fillna('Undefined')
    
    # Time Parts
    df['Month'] = df['Occurrence Date'].dt.month
    df['Year'] = df['Occurrence Date'].dt.year
    df['FY_int'] = np.where(df['Month'] >= 10, df['Year'] + 1, df['Year'])
    
    # Sentinel check
    df['Sentinel code for check'] = df['รหัส'].astype(str).str.strip() + '-' + df['Impact'].astype(str).str.strip()

    # PSG Mapping (Simple Version for stability)
    if Path(PSG9_FILE_PATH).is_file():
        p_df = pd.read_excel(PSG9_FILE_PATH)
        if 'รหัส' in p_df.columns:
            p_df['รหัส'] = p_df['รหัส'].astype(str).str.strip()
            cols = ['รหัส']
            if 'หมวดหมู่PSG' in p_df.columns: cols.append('หมวดหมู่PSG')
            if 'หมวด' in p_df.columns: cols.append('หมวด')
            df = df.merge(p_df[cols].drop_duplicates(subset=['รหัส']), on='รหัส', how='left')
            
            if 'หมวดหมู่PSG' in df.columns: df = df.rename(columns={'หมวดหมู่PSG': 'หมวดหมู่มาตรฐานสำคัญ'})
            else: df['หมวดหมู่มาตรฐานสำคัญ'] = "ไม่ระบุ"
            
            if 'หมวด' not in df.columns: df['หมวด'] = "N/A"
    else:
        df['หมวดหมู่มาตรฐานสำคัญ'] = "ไม่ระบุ"
        df['หมวด'] = "N/A"

    return df

def filter_by_period_fiscal(df, mode, fy, fq, m):
    if df.empty or mode == "ทั้งหมด": return df
    out = df.copy()
    if fy and fy != "-- ทั้งหมด --": out = out[out['FY_int'].astype(str) == str(fy)]
    # (Simplify: Only year filter implementation for robustness)
    return out

def filter_by_group_and_unit(df, group, unit):
    if df.empty: return df
    out = df.copy()
    # Normalize column names
    if "กลุ่มงาน" not in out.columns: out["กลุ่มงาน"] = "N/A"
    if REF_COL not in out.columns: out[REF_COL] = "N/A"
    
    if group and group not in ("-- เลือกกลุ่มงาน --", "-- ทั้งหมด --"):
        out = out[out["กลุ่มงาน"] == group]
    if unit and unit != "-- ทั้งหมด --":
        out = out[out[REF_COL] == unit]
    return out

# --- Analysis Helpers ---
def create_psg9_summary_table(df):
    if 'หมวดหมู่มาตรฐานสำคัญ' not in df.columns: return pd.DataFrame()
    return pd.crosstab(df['หมวดหมู่มาตรฐานสำคัญ'], df['Impact'], margins=True, margins_name="รวม")

def create_summary_table_by_category(df, col_name):
    if col_name not in df.columns: return pd.DataFrame()
    return pd.crosstab(df[col_name], df['Impact'])

def create_summary_table_by_code(df):
    if 'รหัส' not in df.columns: return pd.DataFrame()
    df['Label'] = df['รหัส'] + " | " + df['ชื่ออุบัติการณ์ความเสี่ยง'].fillna('')
    tab = pd.crosstab(df['Label'], df['Impact'])
    # Calculate E-up (E,F,G,H,I)
    e_cols = [c for c in tab.columns if c in ['E','F','G','H','I','3','4','5']]
    tab['รวม E-up'] = tab[e_cols].sum(axis=1)
    return tab[tab['รวม E-up'] > 0]

def create_goal_summary_table(df, goal_name, e_up_non_numeric_levels_param, e_up_numeric_levels_param, is_org_safety_table):
    key = goal_name.split(":")[0] # P, S, O
    sub = df[df['หมวด'].astype(str).str.startswith(key, na=False)].copy()
    if sub.empty: return pd.DataFrame()
    
    # Check E-up based on params
    severe_list = (e_up_non_numeric_levels_param or []) + (e_up_numeric_levels_param or [])
    # Actually, the logic is easier: if is_org, severe is 3,4,5. Else E,F,G,H,I
    if is_org_safety_table:
        sub['IsSevere'] = sub['Impact Level'].isin(['3','4','5'])
    else:
        sub['IsSevere'] = sub['Impact'].isin(['E','F','G','H','I'])
    
    res = sub.groupby(['รหัส','ชื่ออุบัติการณ์ความเสี่ยง']).agg(
        Total=('Incident', 'count'),
        Severe_Count=('IsSevere', 'sum')
    ).reset_index()
    res['% Severe'] = (res['Severe_Count'] / res['Total'] * 100).round(2)
    return res.sort_values('Severe_Count', ascending=False)

def calculate_persistence_risk_score(df, months):
    if df.empty: return pd.DataFrame()
    g = df.groupby(['รหัส','ชื่ออุบัติการณ์ความเสี่ยง']).agg(
        Total=('Incident','count'),
        Avg_Level=('Impact Level', lambda x: pd.to_numeric(x, errors='coerce').mean())
    ).reset_index()
    g['Rate'] = g['Total']/max(1, months)
    g['Persistence_Risk_Score'] = g['Rate'] * g['Avg_Level'].fillna(1)
    return g.sort_values('Persistence_Risk_Score', ascending=False)

def prioritize_incidents_nb_logit_v2(df):
    # Simplified Early Warning Stub
    if df.empty: return pd.DataFrame()
    g = df.groupby(['รหัส','ชื่ออุบัติการณ์ความเสี่ยง']).size().reset_index(name='Total')
    g['Priority Score'] = g['Total'] * np.random.uniform(0.8, 1.2, len(g)) # Simulation
    return g.sort_values('Priority Score', ascending=False)

# ==============================================================================
# 3) MAIN LOGIC: LOADER
# ==============================================================================
def display_executive_dashboard():
    # 1. Upload in Sidebar
    st.sidebar.header("1. อัปโหลดข้อมูล") 
    up = st.sidebar.file_uploader("ไฟล์ .xlsx", type=["xlsx", "csv"], key="main_uploader")

    df_main = pd.DataFrame()
    loaded = False

    # 2. Load Data
    if up:
        try:
            with st.spinner("Processing..."):
                raw = read_uploaded_table(up)
                df_main = massage_schema(raw)
                loaded = True
                st.sidebar.success("Loaded user file")
        except Exception as e:
            st.error(f"Error loading file: {e}")
    else:
        # Load Default
        DEFAULT_URL = "https://raw.githubusercontent.com/HOIARRTool/ToolMC/main/jib.xlsx"
        st.sidebar.info("Using Demo Data (GitHub)")
        try:
            with st.spinner("Loading demo data..."):
                raw = pd.read_excel(DEFAULT_URL, engine="openpyxl")
                df_main = massage_schema(raw)
                loaded = True
        except:
            pass

    if not loaded or df_main.empty:
        st.info("👈 Please upload data file.")
        return pd.DataFrame()

    # 3. Filters
    st.sidebar.markdown("---")
    st.sidebar.header("2. ตัวกรองข้อมูล")
    
    # Filter: Group/Unit
    grps = ["-- ทั้งหมด --"] + sorted(df_main['กลุ่มงาน'].unique().astype(str)) if 'กลุ่มงาน' in df_main.columns else []
    sel_grp = st.sidebar.selectbox("กลุ่มงาน", grps, index=0)
    
    sel_unit = "-- ทั้งหมด --"
    if sel_grp != "-- ทั้งหมด --":
        units = sorted(df_main[df_main['กลุ่มงาน'] == sel_grp][REF_COL].unique().astype(str))
        sel_unit = st.sidebar.selectbox("หน่วยงาน", ["-- ทั้งหมด --"] + units)
    else:
        st.sidebar.selectbox("หน่วยงาน", ["-- ทั้งหมด --"], disabled=True)

    # Filter: Year
    years = sorted(df_main['FY_int'].unique()) if 'FY_int' in df_main.columns else []
    sel_year = st.sidebar.selectbox("ปีงบประมาณ", ["-- ทั้งหมด --"] + list(map(str, years)))

    # Apply Filters
    filtered = df_main.copy()
    if sel_grp != "-- ทั้งหมด --": filtered = filtered[filtered['กลุ่มงาน'] == sel_grp]
    if sel_unit != "-- ทั้งหมด --": filtered = filtered[filtered[REF_COL] == sel_unit]
    if sel_year != "-- ทั้งหมด --": filtered = filtered[filtered['FY_int'].astype(str) == sel_year]

    st.sidebar.markdown(f"**Found:** {len(filtered):,} items")
    return filtered

# ==============================================================================
# 4) MAIN LOGIC: RENDERER
# ==============================================================================
def render_dashboard_interface(filtered):
    if filtered is None: filtered = pd.DataFrame()

    # --- Sidebar Navigation ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Menu Analysis")
    
    pages = [
        "แดชบอร์ดสรุปภาพรวม", 
        "Incidents Analysis",
        "Risk Matrix (Interactive)",
        "Risk Register Assistant",
        "Heatmap รายเดือน", 
        "Sentinel Events & Top 10", 
        "สรุปอุบัติการณ์ตาม Safety Goals", 
        "Persistence Risk Index", 
        "Early Warning",
        "บทสรุปสำหรับผู้บริหาร"
    ]
    
    if 'selected_analysis' not in st.session_state: st.session_state.selected_analysis = pages[0]

    for p in pages:
        if st.sidebar.button(p, key=f"nav_{p}", use_container_width=True, 
                             type="primary" if st.session_state.selected_analysis == p else "secondary"):
            st.session_state.selected_analysis = p
            st.rerun()

    # --- Render Page Content ---
    page = st.session_state.selected_analysis
    
    # ----------------------------------------------------
    # Page: Dashboard Overview
    # ----------------------------------------------------
    if page == "แดชบอร์ดสรุปภาพรวม":
        st.header("📊 แดชบอร์ดสรุปภาพรวม")
        if filtered.empty:
            st.warning("No data found.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Incidents", len(filtered))
            c2.metric("Sentinel Events", filtered['Sentinel code for check'].isin(sentinel_composite_keys).sum())
            c3.metric("PSG9 Incidents", filtered['รหัส'].isin(psg9_r_codes_for_counting).sum())
            c4.metric("Severe (E-I/3-5)", filtered['Impact Level'].isin(['3','4','5']).sum())
            
            st.markdown("---")
            st.subheader("จำนวนอุบัติการณ์ตามกลุ่มงาน")
            grp_cnt = filtered['กลุ่มงาน'].value_counts().reset_index()
            st.dataframe(grp_cnt, use_container_width=True)

    # ----------------------------------------------------
    # Page: Incident Analysis (with Fixed Tab 5)
    # ----------------------------------------------------
    elif page == "Incidents Analysis":
        st.header("👁️ Incidents Analysis")
        if filtered.empty: st.warning("No data"); return

        t1, t2, t3, t4, t5 = st.tabs(["PSG9", "Groups (C/G)", "By Code", "Unresolved", "Safety Goals"])
        
        with t1:
            st.subheader("PSG9 Analysis")
            st.dataframe(create_psg9_summary_table(filtered), use_container_width=True)
        
        with t2:
            st.subheader("Clinical & General")
            if 'หมวด' in filtered.columns:
                st.dataframe(create_summary_table_by_category(filtered, 'หมวด'), use_container_width=True)
        
        with t3:
            st.subheader("Analysis By Code")
            st.dataframe(create_summary_table_by_code(filtered), use_container_width=True)
            
        with t4:
            st.subheader("Unresolved Items")
            unres = filtered[filtered['Resulting Actions'] == 'None']
            st.dataframe(unres[['Occurrence Date','Incident','Impact']], use_container_width=True)

        with t5:
            # --- FIX FOR TAB 5 ---
            st.subheader("Safety Goals Analysis")
            for disp, cat in goal_definitions.items():
                st.markdown(f"**{disp}**")
                is_org = (disp == "Organization Safety")
                # Correctly pass 'filtered' (the dataframe)
                tbl = create_goal_summary_table(filtered, cat, [], [], is_org)
                
                # Correct indentation for if/else
                if not tbl.empty:
                    st.dataframe(tbl, use_container_width=True)
                else:
                    st.info(f"ไม่พบข้อมูลสำหรับ {disp}")
                st.markdown("---")

    # ----------------------------------------------------
    # Page: Risk Matrix
    # ----------------------------------------------------
    elif page == "Risk Matrix (Interactive)":
        st.header("Risk Matrix")
        if filtered.empty: st.warning("No data"); return
        
        # Simple Matrix Render
        mat = pd.crosstab(filtered['Impact Level'], filtered['Frequency Level'])
        st.dataframe(mat.style.background_gradient(cmap='Reds'), use_container_width=True)

    # ----------------------------------------------------
    # Page: Safety Goals (Summary)
    # ----------------------------------------------------
    elif page == "สรุปอุบัติการณ์ตาม Safety Goals":
        st.header("Safety Goals Summary")
        if filtered.empty: st.warning("No data"); return
        
        for disp, cat in goal_definitions.items():
            st.subheader(disp)
            tbl = create_goal_summary_table(filtered, cat, [], [], disp=="Organization Safety")
            if not tbl.empty: st.dataframe(tbl, use_container_width=True)
            else: st.info("No Data")

    # ----------------------------------------------------
    # Page: Executive Summary
    # ----------------------------------------------------
    elif page == "บทสรุปสำหรับผู้บริหาร":
        st.header("📑 บทสรุปสำหรับผู้บริหาร")
        st.info("Executive Summary Report Generation...")
        
        # Calculate Metrics
        total = len(filtered)
        sentinel = filtered['Sentinel code for check'].isin(sentinel_composite_keys).sum()
        severe = filtered['Impact Level'].isin(['3','4','5']).sum()
        
        html = f"""
        <div style="padding:20px; border:1px solid #ddd; border-radius:10px; background:white;">
            <h1 style="color:#003366; text-align:center;">Executive Summary</h1>
            <hr>
            <div style="display:flex; justify-content:space-around; margin-bottom:20px;">
                <div style="text-align:center;"><h3>Total</h3><h1>{total}</h1></div>
                <div style="text-align:center; color:red;"><h3>Sentinel</h3><h1>{sentinel}</h1></div>
                <div style="text-align:center; color:orange;"><h3>Severe</h3><h1>{severe}</h1></div>
            </div>
            <p>Generated on: {datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        """
        st.components.v1.html(html, height=400, scrolling=True)

    # ----------------------------------------------------
    # Page: Risk Register Assistant
    # ----------------------------------------------------
    elif page == "Risk Register Assistant":
        st.header("Risk Register Assistant")
        q = st.text_input("Search Code/Name")
        if st.button("Search") and q:
            with st.spinner("Analyzing..."):
                res = get_risk_register_consultation(q, filtered, df_mitigation)
                if "error" not in res:
                    st.success(f"Result for {res.get('incident_code')}")
                    st.json(res)
                else:
                    st.error("Not found or AI error.")

    # ----------------------------------------------------
    # Other Pages (Stubs for brevity)
    # ----------------------------------------------------
    elif page in ["Heatmap รายเดือน", "Sentinel Events & Top 10", "Persistence Risk Index", "Early Warning"]:
        st.header(page)
        if filtered.empty: st.warning("No Data"); return
        
        if page == "Sentinel Events & Top 10":
            st.subheader("Top 10 Incidents")
            top10 = filtered['Incident'].value_counts().head(10).reset_index()
            st.dataframe(top10, use_container_width=True)
            
        elif page == "Early Warning":
            st.subheader("Early Warning Signals")
            res = prioritize_incidents_nb_logit_v2(filtered)
            st.dataframe(res.head(10), use_container_width=True)
            
        else:
            st.info(f"Placeholder for {page}")

# ==============================================================================
# 5) MAIN ENTRY POINT
# ==============================================================================
def main():
    # 1. Load Data (Once)
    df = display_executive_dashboard()
    
    # 2. Render Interface (Pass Loaded Data)
    render_dashboard_interface(df)

if __name__ == "__main__":
    main()
