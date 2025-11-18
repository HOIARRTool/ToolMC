# app.py (Restored Full Code without Anonymizer, with Department Filter, fixed Safety Goals & indents)
# -*- coding: utf-8 -*-
import os
import re
import unicodedata
from datetime import datetime, date
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
import base64
from dateutil.relativedelta import relativedelta
import statsmodels.api as sm
# from sklearn.linear_model import LinearRegression # Not used currently
import plotly.express as px
import plotly.graph_objects as go

# Keep AI/Risk Register imports (assuming files exist)
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Ensure these helper python files exist in the same directory or adjust path
try:
    from ai_assistant import get_consultation_response
except ImportError:
    def get_consultation_response(text): return f"Error: Could not import `get_consultation_response` from `ai_assistant.py`."
try:
    from risk_register_assistant import get_risk_register_consultation
except ImportError:
    def get_risk_register_consultation(query, df, risk_mitigation_df): return {"error": "Error: Could not import `get_risk_register_consultation` from `risk_register_assistant.py`."}

# Set page config first
st.set_page_config(layout="wide", page_title="HOIA-RR")
# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/refs/heads/main/logo1.png"
st.set_page_config(page_title="HOIA-RR", page_icon=LOGO_URL, layout="wide")

# URLs ของโลโก้ทั้ง 4
logo_urls = [
    "https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018987241.jpg?raw=true",
    "https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018963411.jpg?raw=true",    
    "https://mfu.ac.th/fileadmin/_processed_/6/7/csm_logo_mfu_3d_colour_15e5a7a50f.png",
    "https://github.com/HOIARRTool/appqtbi/blob/main/logoSHS.png?raw=true"
]
st.set_page_config(page_title="HOIA-RR", page_icon=LOGO_URL, layout="wide")

st.markdown(
    """
    <div style="
        width: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        gap: 12px;
        padding: 8px 24px 0 0;
    ">
        <img src="https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018987241.jpg?raw=true" style="height:60px;">
        <img src="https://github.com/HOIARRTool/appqtbi/blob/main/messageImage_1763018963411.jpg?raw=true" 
            style="height:75px; margin-top:-4px;">
        <img src="https://mfu.ac.th/fileadmin/_processed_/6/7/csm_logo_mfu_3d_colour_15e5a7a50f.png"
             style="height:70px; margin-top:-1px;">
        <!-- ขยับโลโก้ SHS ลงมานิดหน่อยด้วย margin-top -->
        <img src="https://github.com/HOIARRTool/appqtbi/blob/main/logoSHS.png?raw=true"
             style="height:45px; margin-top:12px;">
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# 0) อ้างอิง กลุ่มงาน ↔ หน่วยงาน
# =========================
SERVICE_MAP = [
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขากุมารเวชศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาจักษุวิทยา"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาจิตเวชศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานนิติเวช"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานพยาธิวิทยากายวิภาค (PATHO)"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานพยาธิวิทยาคลินิก"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานธนาคารเลือด"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานรังสีวิทยา"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการพยาบาลวิสัญญี"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาวิสัญญีวิทยา"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานเวชกรรมสังคม"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาเวชศาสตร์ฉุกเฉิน"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานกายภาพบําบัด"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยตรวจเวชศาสตร์ฟื้นฟู"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาศัลยศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาออร์โธปิดิกส์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาสูติศาสตร์และนรีเวชวิทยา"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาโสต ศอ นาสิก"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์สาขาอายุรศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานการแพทย์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "คลินิกพิเศษเฉพาะทางนอกเวลา (SMC)"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "คลินิกแพทย์แผนไทย"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "คลินิกแพทย์แผนจีน"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "คลินิกแพทย์บูรณาการ"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "แผนกห้องยาสมุนไพร"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานเภสัชกรรม"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "คลังเวชภัณฑ์ที่มิใช่ยา"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานโภชนาการ"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "ศูนย์เครื่องมือแพทย์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยโลจิสติกส์และเคลื่อนย้ายผู้ป้วย"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานเวชภัณฑ์ปลอดเชื้อ(CSSD)"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานบริการผ้า"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยสังคมสงเคราะห์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "Admission center"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยประสานสิทธิ์การแพทย์"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยเวชสถิติ"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยเวชระเบียน"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "หน่วยจ่ายยาผู้ป่วย 11B"},
    {"กลุ่มงาน": "กลุ่มงานการแพทย์", "หน่วยงาน": "งานสนับสนุนทางการแพทย์"},
    {"กลุ่มงาน": "กลุ่มงานพัฒนาคุณภาพและการศึกษา", "หน่วยงาน": "งานพัฒนาคุณภาพ"},
    {"กลุ่มงาน": "กลุ่มงานพัฒนาคุณภาพและการศึกษา", "หน่วยงาน": "งานส่งเสริมวิจัยและนวัตกรรม"},
    {"กลุ่มงาน": "กลุ่มงานพัฒนาคุณภาพและการศึกษา", "หน่วยงาน": "ศูนย์รับเรื่องร้องเรียนและศูนย์ธรรมจริยธรรม"},
    {"กลุ่มงาน": "กลุ่มงานพัฒนาคุณภาพและการศึกษา", "หน่วยงาน": "ศูนย์บริการจัดการเรื่องร้องเรียนและยุติธรรมเชิงสมานฉันท์"},
    {"กลุ่มงาน": "กลุ่มงานนโยบายและยุทธศาสตร์", "หน่วยงาน": "งานวางแผนและบริหารยุทธศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานนโยบายและยุทธศาสตร์", "หน่วยงาน": "งานเทคโนโลยีสารสนเทศ"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "งานสารบรรณและอำนวยการ"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "งานโครงสร้างพื้นฐานและวิศวกรรม (งานอาคารสถานที่)"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "งานทรัพยากรบุคคล"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "หน่วยประชาสัมพันธ์และการตลาด"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "งานการเงินบัญชีและงบประมาณ"},
    {"กลุ่มงาน": "กลุ่มงานบริหาร", "หน่วยงาน": "งานพัสดุ"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยบริการผู้ป่วยฉุกเฉิน (ER)"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจรักษาทั่วไป"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจตา"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจหู คอ จมูก"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจหัวใจและหลอดเลือด ( OPD Heart )"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจสวนหัวใจและหลอดเลือด ( Cath Lab )"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจสูตินรีเวชศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "ห้องคลอด"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสูตินรีเวชศาสตร์และกุมารเวชศาสตร์ 12 B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจผู้ป่วยนอกศัลยศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจผู้ป่วยนอกออร์โธปิดิกส์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วย 8B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสามัญรวม 9A"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยพิเศษศัลยศาสตร์ 10A"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยพิเศษศัลยศาสตร์ 11A"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยพิเศษศัลยศาสตร์และออร์โธปิดิกส์ 12A"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจผู้ป่วยนอกอายุรศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วย CCU"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยไอซียูอายุรศาสตร์"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสามัญอายุรศาสตร์หญิง 7A"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสามัญอายุรศาสตร์ชาย 7B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยพิเศษรวม 10B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยเคมีบำบัด 11B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "ห้องไตเทียม"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยบำบัดทดแทนไต"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจเด็กสุขภาพดี"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจรักษาเด็กป่วย"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หออภิบาลทารกแรกเกิด (Nursery)"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจสุขภาพจิต"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสามัญจิตเวช (8A)"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "งานการพยาบาลผ่าตัด"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "ศูนย์ส่องกล้องระบบทางเดินอาหาร"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยส่งเสริมสุขภาพ"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยตรวจสุขภาพ (Check-up)"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "งานศูนย์ความเป็นเลิศทางการพยาบาล"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "งานป้องกันและควบคุมการติดเชื้อในโรงพยาบาล"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หน่วยผู้ป่วยวิกฤตอายุรกรรม"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "งานการพยาบาลห้องคลอดและทารกแรกเกิด (งานอาสาสมัคร)"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "หอผู้ป่วยสามัญเด็ก ชั้น 9B"},
    {"กลุ่มงาน": "กลุ่มงานการพยาบาล", "หน่วยงาน": "300503"},
]
REF_DF = pd.DataFrame(SERVICE_MAP)
REF_COL = "หน่วยงาน"  # Column name in the main data file for department

def list_units(group_name: str) -> list:
    if not group_name or group_name in ("-- เลือกกลุ่มงาน --", "-- ทั้งหมด --"):
        return []
    if group_name in REF_DF["กลุ่มงาน"].unique():
        return sorted(REF_DF.loc[REF_DF["กลุ่มงาน"] == group_name, "หน่วยงาน"].unique().tolist())
    return []

# =========================
# A) Normalization & Mapping
# =========================
INVIS_CHARS = {"\u200b": "", "\u200c": "", "\u200d": "", "\ufeff": ""}
PARENS = {"（": "(", "）": ")", "﹙": "(", "﹚": ")", "“": '"', "”": '"', "‘": "'", "’": "'"}
TRANS_INVIS = str.maketrans(INVIS_CHARS)
TRANS_PARENS = str.maketrans(PARENS)
ALIASES = {
    "หน่วยโลจิสติกส์และเคลื่อนย้ายผู้ป้วย": "หน่วยโลจิสติกส์และเคลื่อนย้ายผู้ป่วย",
}

def normalize_unit(text: str) -> str:
    if pd.isna(text): return ""
    s = str(text)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\xa0", " ").translate(TRANS_INVIS).translate(TRANS_PARENS)
    s = re.sub(r"\s+", " ", s.strip()).strip('\'"')
    return ALIASES.get(s, s)

service_map_norm = {normalize_unit(r["หน่วยงาน"]): r["กลุ่มงาน"] for r in SERVICE_MAP}

# === Safety Goals definitions (global) ===
goal_definitions = {
    "Patient Safety/ Common Clinical Risk": "P:Patient Safety Goals หรือ Common Clinical Risk Incident",
    "Specific Clinical Risk": "S:Specific Clinical Risk Incident",
    "Personnel Safety": "P:Personnel Safety Goals",
    "Organization Safety": "O:Organization Safety Goals",
}

# =========================
# 1) แปลงวันที่/เวลาไทย → Timestamp
# =========================
THAI_MONTHS = {
    "ม.ค.":1, "ก.พ.":2, "มี.ค.":3, "เม.ย.":4, "พ.ค.":5, "มิ.ย.":6,
    "ก.ค.":7, "ส.ค.":8, "ก.ย.":9, "ต.ค.":10, "พ.ย.":11, "ธ.ค.":12,
    "มกราคม":1, "กุมภาพันธ์":2, "มีนาคม":3, "เมษายน":4, "พฤษภาคม":5, "มิถุนายน":6,
    "กรกฎาคม":7, "สิงหาคม":8, "กันยายน":9, "ตุลาคม":10, "พฤศจิกายน":11, "ธันวาคม":12,
}
THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"; ARABIC_DIGITS = "0123456789"
DIGIT_MAP = str.maketrans({t: a for t, a in zip(THAI_DIGITS, ARABIC_DIGITS)})

def normalize_raw_datetime_text(x):
    if x is None or (isinstance(x, float) and pd.isna(x)) or (isinstance(x, str) and x.strip() == ""): return None
    s = str(x).strip().translate(DIGIT_MAP)
    s = re.sub(r"\bเวลา\b", "", s); s = re.sub(r"\s*น\.?\b", "", s); s = re.sub(r"\s+", " ", s).strip()
    return s if s else None

def parse_incident_datetime(value):
    # Handle direct Timestamp or datetime objects
    if isinstance(value, (pd.Timestamp, datetime)):
        ts = pd.Timestamp(value)
        if ts.year >= 2400:
            ts = ts - pd.DateOffset(years=543)
        return ts

    # Handle Excel numeric date format (days since 1899-12-30)
    try:
        if isinstance(value, (int, float)) and not pd.isna(value):
            return pd.to_datetime(value, unit="d", origin="1899-12-30", errors="coerce")
        # numeric string like "45678.0"
        v = str(value)
        if re.fullmatch(r"\d+(\.\d+)?", v):
            return pd.to_datetime(float(v), unit="d", origin="1899-12-30", errors="coerce")
    except Exception:
        pass

    # Handle string formats
    s = normalize_raw_datetime_text(value)
    if not s:
        return pd.NaT

    # Thai month: dd Mon yyyy [HH:MM[:SS]]
    # --- สำคัญ: ทำให้วงเล็บชั้นในเป็น non-capturing ด้วย (?::\d{2})? ---
    m_th = re.search(r"(\d{1,2})\s*([ก-๙\.]+)\s*(\d{4})\s*(\d{1,2}:\d{2}(?::\d{2})?)?", s)
    if m_th:
        dd_str = m_th.group(1)
        mon_txt = m_th.group(2)
        yyyy_str = m_th.group(3)
        hhmmss_str = m_th.group(4)  # อาจเป็น None
        dd = int(dd_str)
        yyyy = int(yyyy_str)
        hhmmss = hhmmss_str or "00:00:00"
        # เติมวินาทีถ้ายังไม่มี
        if len(hhmmss) == 5:
            hhmmss = hhmmss + ":00"
        mm = THAI_MONTHS.get(mon_txt.strip()) or THAI_MONTHS.get(mon_txt.strip() + ".")
        if mm:
            if yyyy >= 2400:
                yyyy -= 543
            try:
                return pd.to_datetime(f"{yyyy:04d}-{mm:02d}-{dd:02d} {hhmmss}",
                                      format="%Y-%m-%d %H:%M:%S", errors="coerce")
            except ValueError:
                pass

    # dd/mm/yyyy or dd-mm-yyyy [HH:MM[:SS]]
    m_sep = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})(?:\s+(\d{1,2}:\d{2}(?::\d{2})?))?", s)
    if m_sep:
        dd_str = m_sep.group(1)
        mm_str = m_sep.group(2)
        yyyy_str = m_sep.group(3)
        hhmmss_str = m_sep.group(4)  # อาจเป็น None
        dd = int(dd_str)
        mm = int(mm_str)
        yyyy = int(yyyy_str)
        hhmmss = hhmmss_str or "00:00:00"
        if len(hhmmss) == 5:
            hhmmss = hhmmss + ":00"
        if yyyy >= 2400:
            yyyy -= 543
        try:
            return pd.to_datetime(f"{yyyy:04d}-{mm:02d}-{dd:02d} {hhmmss}",
                                  format="%Y-%m-%d %H:%M:%S", errors="coerce")
        except ValueError:
            pass

    # Fallback: แปลงปี พ.ศ. เป็น ค.ศ. ถ้าพบ
    yr = re.search(r"\b(2\d{3})\b", s)
    if yr:
        y = int(yr.group(1))
        if y >= 2400:
            s = s.replace(str(y), str(y - 543), 1)

    # Final fallback
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


# =========================
# 2) Risk / สี
# =========================
def map_impact_level_func(val):
    s = str(val).strip().upper()
    if s in ("A", "B", "1"): return "1"
    if s in ("C", "D", "2"): return "2"
    if s in ("E", "F", "3"): return "3"
    if s in ("G", "H", "4"): return "4"
    if s in ("I", "5"): return "5"
    return "N/A"

RISK_COLOR_TABLE = {
    "11":"Low","12":"Low","13":"Low","14":"Medium","15":"Medium",
    "21":"Low","22":"Low","23":"Medium","24":"Medium","25":"High",
    "31":"Low","32":"Medium","33":"Medium","34":"High","35":"High",
    "41":"Medium","42":"Medium","43":"High","44":"High","45":"Extreme",
    "51":"Medium","52":"High","53":"High","54":"Extreme","55":"Extreme",
}

def compute_frequency_level(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'Occurrence Date' not in df.columns or df['Occurrence Date'].isna().all():
        return df.assign(**{'count':0, 'Incident Rate/mth':0.0, 'Frequency Level':'N/A'})
    max_p = df['Occurrence Date'].max().to_period('M'); min_p = df['Occurrence Date'].min().to_period('M')
    total_month_calc = max(1, (max_p.year - min_p.year) * 12 + (max_p.month - min_p.month) + 1)
    counts = df['Incident'].value_counts(); out = df.copy()
    out['count'] = out['Incident'].map(counts).fillna(0).astype(int)
    out['Incident Rate/mth'] = (out['count'] / total_month_calc).round(1)
    cond = [(out['Incident Rate/mth']<2.0), (out['Incident Rate/mth']<3.9), (out['Incident Rate/mth']<6.9), (out['Incident Rate/mth']<29.9)]
    out['Frequency Level'] = np.select(cond, ['1','2','3','4'], default='5')
    return out

def build_risk_matrix(df: pd.DataFrame) -> pd.DataFrame:
    idx = list("54321"); cols = list("12345"); empty_mat = pd.DataFrame(0, index=idx, columns=cols)
    if df.empty or 'Risk Level' not in df.columns: return empty_mat
    valid_df = df[(df['Risk Level'] != 'N/A') & df['Impact Level'].isin(idx) & df['Frequency Level'].isin(cols)]
    if valid_df.empty: return empty_mat
    mat = pd.crosstab(valid_df['Impact Level'], valid_df['Frequency Level'])
    return mat.reindex(index=idx, columns=cols, fill_value=0)

def summarize_max_risk_per_incident(df: pd.DataFrame) -> pd.DataFrame:
    cols=['Incident','ชื่ออุบัติการณ์ความเสี่ยง','Max Risk','Category Color']
    if df.empty or 'Risk Level' not in df.columns: return pd.DataFrame(columns=cols)
    order={'1':1,'2':2,'3':3,'4':4,'5':5}; d2 = df[df['Risk Level'] != 'N/A'].copy()
    if d2.empty: return pd.DataFrame(columns=cols)
    d2['I_num'] = d2['Impact Level'].map(order).fillna(0).astype(int); d2['F_num'] = d2['Frequency Level'].map(order).fillna(0).astype(int)
    d2['score'] = d2['I_num']*10 + d2['F_num']
    idx = d2.groupby(['Incident','ชื่ออุบัติการณ์ความเสี่ยง'], observed=True)['score'].idxmax()
    agg = d2.loc[idx, ['Incident','ชื่ออุบัติการณ์ความเสี่ยง','Risk Level','Category Color','Incident Rate/mth']].copy()
    agg = agg.rename(columns={'Risk Level':'Max Risk', 'Incident Rate/mth':'rate'})
    return agg.sort_values('rate', ascending=False).drop(columns='rate')

# =========================
# 3) อ่านไฟล์ & จัดสคีมา
# =========================
def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None: return pd.DataFrame()
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"): return pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")): return pd.read_excel(uploaded_file, engine="openpyxl")
        else: raise ValueError("รองรับ .csv, .xlsx, .xls")
    except Exception as e:
        st.error(f"Error reading file '{uploaded_file.name}': {e}")
        return pd.DataFrame()

def massage_schema(df: pd.DataFrame) -> pd.DataFrame:
    required = ["รหัสหัวข้อ","หัวข้อ","วัน-เวลา ที่เกิดเหตุ","ระดับความรุนแรง", REF_COL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("ไม่พบคอลัมน์จำเป็น: " + ", ".join(missing)); st.stop()

    df = df.copy()
    # Strip whitespace from all string columns first for consistency
    for col in df.select_dtypes(include='object').columns:
        if col not in ['Occurrence Date']:
            df[col] = df[col].astype(str).str.strip()

    df["รหัส: เรื่องอุบัติการณ์"] = df["รหัสหัวข้อ"] + ": " + df["หัวข้อ"]
    df["Incident"] = df["รหัสหัวข้อ"]
    df = df[df["Incident"] != ""].copy()
    df["รหัส"] = df["Incident"].astype(str).str.slice(0,6)
    df["ชื่ออุบัติการณ์ความเสี่ยง"] = df["หัวข้อ"]

    df.rename(columns={"วัน-เวลา ที่เกิดเหตุ": "Occurrence Date"}, inplace=True)
    converted = df["Occurrence Date"].apply(parse_incident_datetime)
    bad = converted.isna().sum()
    
    df["Occurrence Date"] = converted
    df.dropna(subset=["Occurrence Date"], inplace=True)
    if df.empty: st.error("ไม่พบข้อมูลที่มีวันที่ถูกต้อง"); st.stop()

    df["Impact"] = df["ระดับความรุนแรง"].astype(str).str.upper()
    df['Sentinel code for check'] = df['รหัส'].astype(str).str.strip() + '-' + df['Impact'].astype(str).str.strip()
    df['Impact Level'] = df['Impact'].apply(map_impact_level_func)
    df = compute_frequency_level(df)
    df['Risk Level'] = np.where((df['Impact Level']!='N/A') & (df['Frequency Level'].notna()), df['Impact Level']+df['Frequency Level'], 'N/A')
    df['Category Color'] = df['Risk Level'].map(RISK_COLOR_TABLE).fillna('Undefined')

    df['Incident Type'] = df['Incident'].astype(str).str[:3]
    df['Month'] = df['Occurrence Date'].dt.month
    month_label_map = {1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."}
    df['เดือน'] = df['Month'].map(month_label_map)
    df['Year'] = df['Occurrence Date'].dt.year.astype(str)

    # Normalize unit names before mapping
    df["หน่วยงาน_norm"] = df[REF_COL].apply(normalize_unit)
    df["กลุ่มงาน"] = df["หน่วยงาน_norm"].map(service_map_norm).fillna("N/A")

    action_col_original = "การดำเนินการ/การแก้ไขที่ได้ดำเนินการไปแล้ว"
    if "Resulting Actions" not in df.columns:
        if action_col_original in df.columns:
            df['Resulting Actions'] = df[action_col_original].astype(str).apply(
                lambda x: 'None' if x.strip() == '' or x.strip().lower() == 'none' or pd.isna(x) else x
            ).fillna('None')
        else:
            df["Resulting Actions"] = "None"

        # --- PSG9 & หมวด Mapping ---
        # (PSG9code_df_master เป็นตัวแปร global ที่โหลดไว้ใน Section 5)
        if 'PSG9code_df_master' in globals() and not PSG9code_df_master.empty and 'รหัส' in PSG9code_df_master.columns:

            # เตรียมไฟล์ PSG9 สำหรับ merge
            cols_to_merge = ['รหัส']
            if 'หมวดหมู่PSG' in PSG9code_df_master.columns:
                cols_to_merge.append('หมวดหมู่PSG')
            if 'หมวด' in PSG9code_df_master.columns:
                cols_to_merge.append('หมวด')

            psg9_to_merge = PSG9code_df_master[cols_to_merge].drop_duplicates(subset=['รหัส'])

            # ทำให้คอลัมน์ 'รหัส' เป็น str ทั้งคู่เพื่อ merge
            df['รหัส'] = df['รหัส'].astype(str)
            psg9_to_merge['รหัส'] = psg9_to_merge['รหัส'].astype(str)

            # --- ทำการ Merge ---
            df = df.merge(psg9_to_merge, on='รหัส', how='left')

            # --- 1. จัดการคอลัมน์ 'หมวดหมู่มาตรฐานสำคัญ' ---
            if 'หมวดหมู่PSG' in df.columns:
                # ถ้า merge สำเร็จ, ใช้ค่าที่ได้มา, ถ้าไม่ (ได้ค่า NaN) ให้เติม "ไม่จัดอยู่ใน..."
                df['หมวดหมู่มาตรฐานสำคัญ'] = df['หมวดหมู่PSG'].fillna("ไม่จัดอยู่ใน PSG9 Catalog")
                df = df.drop(columns=['หมวดหมู่PSG'])  # ลบคอลัมน์ที่ merge มาทิ้ง
            else:
                # ถ้าไฟล์ PSG9code.xlsx ไม่มีคอลัมน์ 'หมวดหมู่PSG'
                df["หมวดหมู่มาตรฐานสำคัญ"] = "ไม่สามารถระบุ (ไม่มี 'หมวดหมู่PSG' ใน PSG9code.xlsx)"

            # --- 2. จัดการคอลัมน์ 'หมวด' (สำหรับ Safety Goals / C,G analysis) ---
            if 'หมวด' in df.columns:
                # ถ้า merge สำเร็จ, ใช้ค่าที่ได้มา, ถ้าไม่ (ได้ค่า NaN) ให้เติม "N/A"
                df['หมวด'] = df['หมวด'].fillna("N/A")
            else:
                # ถ้าไฟล์ PSG9code.xlsx ไม่มีคอลัมน์ 'หมวด'
                df["หมวด"] = "N/A"
                st.warning("⚠️ ไม่พบคอลัมน์ 'หมวด' ใน PSG9code.xlsx - การวิเคราะห์ Safety Goals และ C/G อาจไม่แสดงผล")

        else:
            # ถ้าโหลดไฟล์ PSG9code.xlsx ไม่สำเร็จตั้งแต่แรก
            st.error("❌ PSG9 mapping ล้มเหลว: ไม่พบ 'PSG9code.xlsx' หรือไฟล์มีปัญหา")
            df["หมวดหมู่มาตรฐานสำคัญ"] = "ไม่สามารถระบุ (PSG9code.xlsx ไม่ได้โหลด/ข้อมูลไม่ครบถ้วน)"
            df["หมวด"] = "N/A"

        # --- END Mapping ---

    detail_col_original = "สรุปปัญหา/เหตุการณ์โดยย่อ"
    if detail_col_original in df.columns:
        df["รายละเอียดการเกิด_Anonymized"] = df[detail_col_original].fillna('')
    else:
        df["รายละเอียดการเกิด_Anonymized"] = ''
    df.rename(columns={detail_col_original: "รายละเอียดการเกิด"}, inplace=True, errors='ignore')

    cols_to_convert = ['self_report', 'potential_harm']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = df[col].replace(['None', ''], np.nan)
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if REF_COL not in df.columns: df[REF_COL] = "N/A"
    df[REF_COL] = df[REF_COL].astype(str).fillna("N/A")
    return df

# =========================
# 4) Time parts (Fiscal Year) + ฟิลเตอร์
# =========================
TH_MONTH_TINY = {1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."}

def add_time_parts_fiscal(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or 'Occurrence Date' not in df.columns: return df
    out=df.copy(); out['Year_int']=out['Occurrence Date'].dt.year.astype(int); out['Month_int']=out['Occurrence Date'].dt.month.astype(int)
    out['FY_int'] = np.where(out['Month_int'] >= 10, out['Year_int'] + 1, out['Year_int']).astype(int)
    def _fq(m): return 'Q1' if m in (10,11,12) else ('Q2' if m in (1,2,3) else ('Q3' if m in (4,5,6) else 'Q4'))
    out['FQuarter'] = out['Month_int'].apply(_fq).astype(str); out['FY_Quarter'] = out['FY_int'].astype(str) + '-' + out['FQuarter']
    return out

def filter_by_period_fiscal(df: pd.DataFrame, mode: str, fy: str|int|None=None, fq: str|None=None, m: int|None=None) -> pd.DataFrame:
    if df.empty or mode == "ทั้งหมด": return df
    out = df.copy()
    fy_str = str(fy) if fy not in (None, "", "-- ทั้งหมด --") else None
    if mode == "รายปี" and fy_str and 'FY_int' in out.columns: out = out[out['FY_int'].astype(str) == fy_str]
    elif mode == "รายไตรมาส":
        if fy_str and 'FY_int' in out.columns: out = out[out['FY_int'].astype(str) == fy_str]
        if fq and fq != "-- ทั้งหมด --" and 'FQuarter' in out.columns: out = out[out['FQuarter'] == fq]
    elif mode == "รายเดือน":
        if fy_str and 'FY_int' in out.columns: out = out[out['FY_int'].astype(str) == fy_str]
        if m and m != "-- ทั้งหมด --" and 'Month_int' in out.columns: out = out[out['Month_int'].astype(int) == int(m)]
    return out
def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    new_cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            c = " ".join([str(x) for x in c if x not in (None, "")])
        c = str(c).replace("\ufeff", "").strip()
        new_cols.append(c)
    df.columns = new_cols
    return df

def _rename_to_standard(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    candidates = {
        "กลุ่มงาน": ["กลุ่มงาน", "กลุ่ม", "Group", "กลุ่มงาน/ฝ่าย", "กลุ่มงาน (Group)"],
        "หน่วยงาน": ["หน่วยงาน", "หน่วย", "Unit", "ฝ่าย/หน่วยงาน", "หน่วยงาน/แผนก"],
    }
    for target, cands in candidates.items():
        if target not in df.columns:
            for c in cands:
                if c in df.columns:
                    df = df.rename(columns={c: target})
                    break
    return df
def filter_by_group_and_unit(df: pd.DataFrame, group_name: str, unit_name: str) -> pd.DataFrame:
    if df.empty:
        return df

    out = _normalize_columns(df)
    out = _rename_to_standard(out)

    required = ["กลุ่มงาน", REF_COL]  # REF_COL = "หน่วยงาน"
    missing = [c for c in required if c not in out.columns]
    if missing:
        st.warning(f"ไม่พบคอลัมน์ที่ต้องใช้ในการกรอง: {', '.join(missing)} — จะแสดงข้อมูลทั้งหมดแทน")
        return out

    def _norm(x): return str(x).strip().lower()

    if group_name not in (None, "", "-- เลือกกลุ่มงาน --", "-- ทั้งหมด --"):
        out = out[out["กลุ่มงาน"].astype(str).str.strip() == str(group_name).strip()]

    if unit_name not in (None, "", "-- ทั้งหมด --"):
        out = out[out[REF_COL].astype(str).str.strip() == str(unit_name).strip()]

    return out

# =========================
# 5) UI (Main Structure)
# =========================
LOGO_URL = "https://raw.githubusercontent.com/HOIARRTool/hoiarr/refs/heads/main/logo1.png"
month_label = {1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."}

# --- Static Definitions ---
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
PERSISTED_DATA_PATH = DATA_DIR / "processed_incident_data.parquet"
PSG9_FILE_PATH = "PSG9code.xlsx"
SENTINEL_FILE_PATH = "Sentinel2024.xlsx"
RISK_MITIGATION_FILE = "risk_mitigations.xlsx"
#DEPARTMENT_FILE_PATH = "service point.xlsx - 53 งาน (ทุกฝ่าย).csv"

psg9_r_codes_for_counting = set()
sentinel_composite_keys = set()
df_mitigation = pd.DataFrame()
department_list = []
PSG9_label_dict = {}

try:
    if Path(PSG9_FILE_PATH).is_file():
        PSG9code_df_master = pd.read_excel(PSG9_FILE_PATH)
        if 'รหัส' in PSG9code_df_master.columns:
            psg9_r_codes_for_counting = set(PSG9code_df_master['รหัส'].astype(str).str.strip().unique())
        if 'PSG_ID' in PSG9code_df_master.columns and 'หมวดหมู่PSG' in PSG9code_df_master.columns:
            PSG9_label_dict = pd.Series(PSG9code_df_master['หมวดหมู่PSG'].values,
                                        index=PSG9code_df_master.PSG_ID).to_dict()
        else:
            st.sidebar.warning(f"'{PSG9_FILE_PATH}' ไม่มี PSG_ID หรือ หมวดหมู่PSG")
    else:
        st.sidebar.warning(f"ไม่พบ '{PSG9_FILE_PATH}'")

    if Path(SENTINEL_FILE_PATH).is_file():
        Sentinel2024_df = pd.read_excel(SENTINEL_FILE_PATH)
        if 'รหัส' in Sentinel2024_df.columns and 'Impact' in Sentinel2024_df.columns:
            Sentinel2024_df['รหัส'] = Sentinel2024_df['รหัส'].astype(str).str.strip()
            Sentinel2024_df['Impact'] = Sentinel2024_df['Impact'].astype(str).str.strip()
            Sentinel2024_df.dropna(subset=['รหัส', 'Impact'], inplace=True)
            sentinel_composite_keys = set((Sentinel2024_df['รหัส'] + '-' + Sentinel2024_df['Impact']).unique())
    else:
        st.sidebar.warning(f"ไม่พบ '{SENTINEL_FILE_PATH}'")

    if Path(RISK_MITIGATION_FILE).is_file():
        df_mitigation = pd.read_excel(RISK_MITIGATION_FILE)
    else:
        st.sidebar.warning(f"ไม่พบ '{RISK_MITIGATION_FILE}'")

    #if Path(DEPARTMENT_FILE_PATH).is_file():
        #dept_df = pd.read_csv(DEPARTMENT_FILE_PATH)
        #if 'หน่วยงาน' in dept_df.columns:
            #department_list = sorted([dept for dept in dept_df['หน่วยงาน'].astype(str).unique()
                                      #if dept and pd.notna(dept) and dept.strip() != ''])
        #else:
            #st.sidebar.error(f"ไม่พบ 'หน่วยงาน' ใน '{DEPARTMENT_FILE_PATH}'")
    #else:
        #st.sidebar.error(f"ไม่พบ '{DEPARTMENT_FILE_PATH}'")

except Exception as e:
    st.sidebar.error(f"โหลดไฟล์นิยาม/หน่วยงานผิดพลาด: {e}")

# Other static vars
risk_color_data = {
    'Category Color': ["Critical", "Critical", "Critical", "Critical", "Critical", "High", "High", "Critical", "Critical", "Critical",
                       "Medium", "Medium", "High", "Critical", "Critical", "Low", "Medium", "Medium", "High", "High", "Low", "Low", "Low", "Medium", "Medium"],
    'Risk Level': ["51", "52", "53", "54", "55", "41", "42", "43", "44", "45", "31", "32", "33", "34", "35", "21", "22", "23", "24", "25", "11", "12", "13", "14", "15"]}
risk_color_df = pd.DataFrame(risk_color_data)
display_cols_common = ['Occurrence Date', 'รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Impact', 'Impact Level',
                       'รายละเอียดการเกิด_Anonymized', 'Resulting Actions', 'หน่วยงาน']
type_name = {'CPS': 'Safe Surgery', 'CPI': 'Infection Control', 'CPM': 'Medication & Blood Safety', 'CPP': 'Patient Care Process',
             'CPL': 'Line, Tube & Catheter, Lab', 'CPE': 'Emergency Response', 'CSG': 'Gyn & Obs', 'CSS': 'Surgical', 'CSM': 'Medical',
             'CSP': 'Pediatric', 'CSO': 'Orthopedic', 'CSD': 'Dental', 'GPS': 'Social Media & Comms', 'GPI': 'Infection & Exposure',
             'GPM': 'Mental Health & Mediation', 'GPP': 'Process of work', 'GPL': 'Lane & Legal', 'GPE': 'Environment & Working',
             'GOS': 'Strategy, Structure, Security', 'GOI': 'IT & Comms, Internal control', 'GOM': 'Manpower, Management',
             'GOP': 'Policy, Process & Operation', 'GOL': 'Licensed & Professional cert', 'GOE': 'Economy'}
colors2 = np.array([["#e1f5fe","#f6c8b6","#dd191d","#dd191d","#dd191d","#dd191d","#dd191d"],
                    ["#e1f5fe","#f6c8b6","#ff8f00","#ff8f00","#dd191d","#dd191d","#dd191d"],
                    ["#e1f5fe","#f6c8b6","#ffee58","#ffee58","#ff8f00","#dd191d","#dd191d"],
                    ["#e1f5fe","#f6c8b6","#42db41","#ffee58","#ffee58","#ff8f00","#ff8f00"],
                    ["#e1f5fe","#f6c8b6","#42db41","#42db41","#42db41","#ffee58","#ffee58"],
                    ["#e1f5fe","#f6c8b6","#f6c8b6","#f6c8b6","#f6c8b6","#f6c8b6","#f6c8b6"],
                    ["#e1f5fe","#e1f5fe","#e1f5fe","#e1f5fe","#e1f5fe","#e1f5fe","#e1f5fe"]])
def display_executive_dashboard():
    log_visit() 

    # --- 1. สร้าง Sidebar และเมนูเลือกหน้า ---
    st.sidebar.markdown(
        f"""<div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <img src="{LOGO_URL}" style="height: 32px; margin-right: 10px;">
        <h2 style="margin: 0; font-size: 1.7rem;">
            <span class="gradient-text">HOIA-RR Menu</span>
        </h2></div>""",
        unsafe_allow_html=True
    )

    # --- Upload and Filters ---
    st.header("อัปโหลดข้อมูล")
    up = st.file_uploader(
        "อัปโหลดไฟล์ (.xlsx)",
        type=["csv", "xlsx", "xls"],
        key="main_uploader"
    )

    # =========================
    # 6) ประมวลผล (Main Processing Logic)
    # =========================
    df_main = pd.DataFrame()
    processed_data_loaded = False  # ใช้ติดตามสถานะการโหลด

    # --- Logic 1: ตรวจสอบไฟล์ที่อัปโหลด (มีความสำคัญสูงสุด) ---
    if up is not None:
        try:
            raw_df = read_uploaded_table(up)
            with st.spinner(f"กำลังประมวลผลไฟล์ '{up.name}'..."):
                df_main = massage_schema(raw_df)
                df_main = add_time_parts_fiscal(df_main)
                processed_data_loaded = True
                st.sidebar.success(f"ประมวลผล '{up.name}' สำเร็จ")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างประมวลผลไฟล์: {e}")

    # ถ้าอยากแสดงตัวอย่างข้อมูลหลังประมวลผล
    if processed_data_loaded:
        st.subheader("ตัวอย่างข้อมูลหลังประมวลผล")
        st.write(df_main.head())

    # =========================
    # ตัวกรองหลัก
    # =========================
    st.header("ตัวกรองหลัก")
    GROUP_OPTIONS = ["-- เลือกกลุ่มงาน --", "-- ทั้งหมด --"] + sorted(
        REF_DF["กลุ่มงาน"].unique().tolist()
    )
    sel_group = st.selectbox("เลือกกลุ่มงาน", GROUP_OPTIONS, index=1)

    if sel_group == "-- ทั้งหมด --":
        sel_unit = "-- ทั้งหมด --"
        st.selectbox("เลือกหน่วยงาน", ["-- ทั้งหมด --"], index=0, disabled=True)
    else:
        unit_options = list_units(sel_group)
        sel_unit = st.selectbox(
            "เลือกหน่วยงาน",
            ["-- ทั้งหมด --"] + unit_options,
            index=0,
            disabled=(sel_group in ("", "-- เลือกกลุ่มงาน --"))
        )

    # =========================
    # ตัวกรองช่วงเวลา (ปีงบประมาณ)
    # =========================
    st.header("ตัวกรองช่วงเวลา (ปีงบประมาณ)")
    period_mode = st.selectbox(
        "โหมดช่วงเวลา",
        ["ทั้งหมด", "รายปี", "รายไตรมาส", "รายเดือน"],
        index=0
    )


if up is None: 
    DEFAULT_DATA_URL = "https://raw.githubusercontent.com/HOIARRTool/ToolMC/main/jib.xlsx" 
    st.sidebar.info("ไม่ได้อัปโหลดไฟล์, กำลังโหลดข้อมูลตั้งต้น...")
    try:
        with st.spinner("กำลังโหลดข้อมูลตั้งต้นจาก GitHub..."):
            raw_df = pd.read_excel(DEFAULT_DATA_URL, engine="openpyxl") 
            df_main = massage_schema(raw_df)
            df_main = add_time_parts_fiscal(df_main)
            processed_data_loaded = True
            st.sidebar.success("โหลดข้อมูลตั้งต้นสำเร็จ")
            # --- ลบการบันทึก .parquet ออก ---
            
    except Exception as e:
        st.sidebar.error(f"โหลดข้อมูลตั้งต้นจาก URL ไม่สำเร็จ: {e}")
        st.sidebar.caption(f"URL: {DEFAULT_DATA_URL}")
        df_main = pd.DataFrame()
        processed_data_loaded = False

# หลังจาก df_main ถูกโหลด (ไม่ว่าจะจาก upload หรือ URL)
# >>> PATCH: ensure required columns exist when loading old parquet
if processed_data_loaded and "หน่วยงาน" not in df_main.columns:
    # พยายามดึงจากชื่อใกล้เคียง ถ้าไม่มีจริงๆ ค่อยเติม N/A
    alt_names = ["หน่วยงาน/แผนก", "ฝ่าย/หน่วยงาน", "แผนก", "หน่วยงานที่เกิดเหตุ", "Department", "หน่วย"]
    found = None
    for c in alt_names:
        if c in df_main.columns:
            found = c
            break
    if found:
        df_main["หน่วยงาน"] = df_main[found].astype(str)
    else:
        df_main["หน่วยงาน"] = "N/A"

if processed_data_loaded and "กลุ่มงาน" not in df_main.columns:
    # ถ้าไม่มี ให้คำนวณจากหน่วยงาน_norm (ถ้ามี) หรือกำหนด N/A
    if "หน่วยงาน_norm" in df_main.columns:
        df_main["กลุ่มงาน"] = df_main["หน่วยงาน_norm"].map(service_map_norm).fillna("N/A")
    else:
        df_main["กลุ่มงาน"] = "N/A"

if df_main.empty:
    st.info("👈 กรุณาอัปโหลดไฟล์ข้อมูล (หรือระบบไม่สามารถโหลดข้อมูลตั้งต้นได้)")
    st.stop()
    
def _rename_to_standard(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    candidates = {
        "กลุ่มงาน": ["กลุ่มงาน", "กลุ่ม", "Group", "กลุ่มงาน/ฝ่าย", "กลุ่มงาน (Group)"],
        "หน่วยงาน": [
            "หน่วยงาน", "หน่วย", "Unit", "Department",
            "หน่วยงาน/แผนก", "ฝ่าย/หน่วยงาน", "หน่วยงานที่เกิดเหตุ",
            "ชื่อหน่วยงาน", "หน่วยที่เกี่ยวข้อง", "ภาควิชา/หน่วยงาน"
        ],
    }
    for target, cands in candidates.items():
        if target not in df.columns:
            for c in cands:
                if c in df.columns:
                    df = df.rename(columns={c: target})
                    break
    return df
# --- Apply Filters selected in Sidebar ---
fy_opts = ["-- ทั้งหมด --"] + sorted(df_main['FY_int'].astype(str).unique().tolist()) if 'FY_int' in df_main else ["-- ทั้งหมด --"]
month_order = [10, 11, 12] + list(range(1, 10))
month_opts = ["-- ทั้งหมด --"] + [f"{m:02d}-{TH_MONTH_TINY.get(m, '?')}" for m in month_order] if 'Month_int' in df_main else ["-- ทั้งหมด --"]

with st.sidebar:
    sel_fy = None; sel_fq = None; sel_month_num = None
    if period_mode == "รายปี":
        sel_fy = st.selectbox("เลือกปีงบประมาณ", fy_opts, index=0)
    elif period_mode == "รายไตรมาส":
        c1, c2 = st.columns(2)
        with c1: sel_fy = st.selectbox("ปีงบประมาณ", fy_opts, index=0, key="fq_year")
        with c2: sel_fq = st.selectbox("ไตรมาส", ["-- ทั้งหมด --", "Q1", "Q2", "Q3", "Q4"], index=0, key="fq_quarter")
    elif period_mode == "รายเดือน":
        c1, c2 = st.columns(2)
        with c1: sel_fy = st.selectbox("ปีงบประมาณ", fy_opts, index=0, key="fm_year")
        with c2:
            month_label_select = st.selectbox("เดือน", month_opts, index=0, key="fm_month")
            if month_label_select not in (None, "", "-- ทั้งหมด --"):
                sel_month_num = int(month_label_select.split("-")[0])

df_time = filter_by_period_fiscal(df_main, period_mode, fy=sel_fy, fq=sel_fq, m=sel_month_num)
filtered = filter_by_group_and_unit(df_time, sel_group, sel_unit)

# --- Update Sidebar Stats ---
sidebar_stats_placeholder = st.sidebar.empty()
if filtered.empty:
    sidebar_stats_placeholder.warning("ไม่พบข้อมูล")
    st.warning("ไม่พบข้อมูลตามตัวกรองที่เลือก")
else:
    min_date_filt = filtered['Occurrence Date'].min(); max_date_filt = filtered['Occurrence Date'].max()
    min_date_str_filt = min_date_filt.strftime('%d/%m/%Y') if pd.notna(min_date_filt) else "N/A"
    max_date_str_filt = max_date_filt.strftime('%d/%m/%Y') if pd.notna(max_date_filt) else "N/A"
    total_month_filt = 0
    if pd.notna(min_date_filt) and pd.notna(max_date_filt):
        max_p_filt = max_date_filt.to_period('M'); min_p_filt = min_date_filt.to_period('M')
        total_month_filt = max(1, (max_p_filt.year - min_p_filt.year) * 12 + (max_p_filt.month - min_p_filt.month) + 1)
    sidebar_stats_placeholder.markdown(f"**ช่วงข้อมูล (กรอง):** {min_date_str_filt} ถึง {max_date_str_filt}")
    sidebar_stats_placeholder.markdown(f"**จำนวนเดือน (กรอง):** {total_month_filt} เดือน")
    sidebar_stats_placeholder.markdown(f"**อุบัติการณ์ (กรองแล้ว):** {filtered.shape[0]:,} รายการ")
    app_functions_list = ["RCA Helpdesk (AI Assistant)"]
    st.sidebar.markdown("---");
    st.sidebar.markdown("เลือกส่วนที่ต้องการแสดงผล:")

    dashboard_pages_list = ["แดชบอร์ดสรุปภาพรวม", "Incidents Analysis","Risk Matrix (Interactive)","Risk level", "Risk Register Assistant", "Heatmap รายเดือน", "Sentinel Events & Top 10", "สรุปอุบัติการณ์ตาม Safety Goals", "Persistence Risk Index", "Early Warning: อุบัติการณ์ที่มีแนวโน้มสูงขึ้น", "บทสรุปสำหรับผู้บริหาร"]
    if 'selected_analysis' not in st.session_state: st.session_state.selected_analysis = "แดชบอร์ดสรุปภาพรวม"
    st.markdown("---")
    for option in app_functions_list:
        if st.sidebar.button(option, key=f"btn_{option}", type="primary" if st.session_state.selected_analysis == option else "secondary", use_container_width=True):
            st.session_state.selected_analysis = option; st.rerun()

    for option in dashboard_pages_list:
        if st.sidebar.button(option, key=f"btn_{option}", type="primary" if st.session_state.selected_analysis == option else "secondary", use_container_width=True):
            st.session_state.selected_analysis = option; st.rerun()

    # --- Sidebar Footer ---
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    **กิตติกรรมประกาศ:** ขอขอบพระคุณ 
    - Prof. Shin Ushiro
    - นพ.อนุวัฒน์ ศุภชุติกุล 
    - นพ.ก้องเกียรติ เกษเพ็ชร์ 
    - พญ.ปิยวรรณ ลิ้มปัญญาเลิศ 
    - ภก.ปรมินทร์ วีระอนันตวัฒน์    
    - ผศ.ดร.นิเวศน์ กุลวงค์ (อ.ที่ปรึกษา)

    เป็นอย่างสูง สำหรับการริเริ่ม เติมเต็ม สนับสนุน และสร้างแรงบันดาลใจ อันเป็นรากฐานสำคัญในการพัฒนาเครื่องมือนี้

    และขอขอบพระคุณโรงพยาบาลที่เข้าร่วมการวิจัยทุกแห่งเป็นอย่างสูง สำหรับความอนุเคราะห์และเอื้อเฟื้อข้อมูลอันเป็นประโยชน์ยิ่งต่องานวิจัยฉบับนี้ ได้แก่:
    - โรงพยาบาลบึงกาฬ จ.บึงกาฬ
    - โรงพยาบาลสมเด็จพระญาณสังวร จ.เชียงราย 
    - โรงพยาบาลสวนผึ้ง จ.ราชบุรี
    - โรงพยาบาลเจ้าคุณไพบูลย์ พนมทวน จ.กาญจนบุรี
    - โรงพยาบาลชะอวด จ.นครศรีธรรมราช
    - โรงพยาบาลอุบลรักษ์ ธนบุรี จ.อุบลราชานี
    - โรงพยาบาลเขาชะเมาเฉลิมพระเกียรติ ๘๐ พรรษา จ.ระยอง
    - โรงพยาบาลสมเด็จพระยุพราชเชียงของ จ. เชียงราย 
    - Kyushu University Hospital, Fukuoka, Japan (ศึกษาดูงาน)
    - โรงพยาบาลกรุงเทพ จันทบุรี, จ.จันทบุรี (ศึกษาดูงาน)
    - โรงพยาบาลศูนย์การแพทย์มหาวิทยาลัยแม่ฟ้าหลวง จ.เชียงราย (ต้นสังกัด)  
    """)  # <--- แก้ไขแล้ว (เนื้อหาชิดซ้าย)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<p style="font-size:12px; color:gray;">*เครื่องมือนี้เป็นส่วนหนึ่งของวิทยานิพนธ์ IMPLEMENTING THE  HOSPITAL OCCURRENCE/INCIDENT ANALYSIS & RISK REGISTER (HOIA-RR TOOL) IN THAI HOSPITALS: A STUDY ON EFFECTIVE ADOPTION โดย นางสาววิลาศินี  เขื่อนแก้ว นักศึกษาปริญญาโท สำนักวิชาวิทยาศาสตร์สุขภาพ มหาวิทยาลัยแม่ฟ้าหลวง</p>',
        unsafe_allow_html=True)
# =========================
# 7) Helper / Stubs (ปลอดภัย ไม่ให้หน้าอื่นพัง)
# =========================

# ========= สี/ฟังก์ชันสำหรับ Risk Matrix (Global Helpers) =========
HEADER_TOPLEFT = "#E6F5FF";
HEADER_SIDE = "#F3C7B1";
HEADER_FREQ = "#EED0BE"
GREEN = "#00D26A";
YELLOW = "#FFE900";
ORANGE = "#FF9800";
RED = "#FF2D2D"
PALETTE_FROM_IMAGE = {
    "11": GREEN, "12": GREEN, "13": GREEN, "14": YELLOW, "15": YELLOW,
    "21": GREEN, "22": YELLOW, "23": YELLOW, "24": ORANGE, "25": ORANGE,
    "31": YELLOW, "32": YELLOW, "33": YELLOW, "34": ORANGE, "35": ORANGE,
    "41": ORANGE, "42": ORANGE, "43": RED, "44": RED, "45": RED,
    "51": RED, "52": RED, "53": RED, "54": RED, "55": RED,
}


def _text_color_for(bg_hex: str) -> str:
    h = bg_hex.lstrip("#");
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    return "#000000" if (0.2126 * r + 0.7152 * g + 0.0722 * b) > 0.6 else "#FFFFFF"


# ========= จบส่วนสี Risk Matrix =========


def render_incidents_analysis(df: pd.DataFrame):
    st.markdown("<h4 style='color: #001f3f;'>Incidents Analysis</h4>", unsafe_allow_html=True)

    if 'Resulting Actions' not in df.columns or 'หมวดหมู่มาตรฐานสำคัญ' not in df.columns:
        st.error(
            "ไม่สามารถแสดงข้อมูลได้ เนื่องจากไม่พบคอลัมน์ 'Resulting Actions' หรือ 'หมวดหมู่มาตรฐานสำคัญ' ในข้อมูล")
    else:
        tab_psg9, tab_groups, tab_by_code, tab_waitlist = st.tabs(
            ["👁️ วิเคราะห์ตามหมวดหมู่ PSG9",
             "👁️ วิเคราะห์ตามกลุ่มหลัก (C/G)",
             "👁️ วิเคราะห์รายรหัส",
             "👁️ อุบัติการณ์ที่รอการแก้ไข(ตามความรุนแรง)"])

        # --- Tab ที่ 1: วิเคราะห์ตามหมวดหมู่ PSG9 ---
        with tab_psg9:
            st.subheader("ภาพรวมอุบัติการณ์ตามมาตรฐานสำคัญจำเป็นต่อความปลอดภัย (PSG9)")
            psg9_summary_table = create_psg9_summary_table(df)
            if psg9_summary_table is not None and not psg9_summary_table.empty:
                st.dataframe(psg9_summary_table, use_container_width=True)
            else:
                st.info("ไม่พบข้อมูลอุบัติการณ์ที่เกี่ยวข้องกับมาตรฐานสำคัญ 9 ข้อในช่วงเวลานี้")

            st.markdown("---")
            st.subheader("สถานะการแก้ไขในแต่ละหมวดหมู่ PSG9")

            # (PSG9_label_dict เป็นตัวแปร global ที่โหลดไว้ตอนเริ่มแอป)
            psg9_categories = {k: v for k, v in PSG9_label_dict.items() if
                               v in df['หมวดหมู่มาตรฐานสำคัญ'].unique()}

            for psg9_id, psg9_name in psg9_categories.items():
                psg9_df = df[df['หมวดหมู่มาตรฐานสำคัญ'] == psg9_name]
                total_count = len(psg9_df)
                resolved_df = psg9_df[~psg9_df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                resolved_count = len(resolved_df)
                unresolved_count = total_count - resolved_count

                expander_title = f"{psg9_name} (ทั้งหมด: {total_count} | แก้ไขแล้ว: {resolved_count} | รอแก้ไข: {unresolved_count})"
                with st.expander(expander_title):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("จำนวนทั้งหมด", f"{total_count:,}")
                    c2.metric("ดำเนินการแก้ไขแล้ว", f"{resolved_count:,}")
                    c3.metric("รอการแก้ไข", f"{unresolved_count:,}")

                    if total_count > 0:
                        tab_resolved, tab_unresolved = st.tabs(
                            [f"รายการที่แก้ไขแล้ว ({resolved_count})", f"รายการที่รอการแก้ไข ({unresolved_count})"])
                        with tab_resolved:
                            if resolved_count > 0:
                                st.dataframe(
                                    resolved_df[['Occurrence Date', 'Incident', 'Impact', 'Resulting Actions']],
                                    hide_index=True, use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.info("ไม่มีรายการที่แก้ไขแล้วในหมวดนี้")
                        with tab_unresolved:
                            if unresolved_count > 0:
                                st.dataframe(
                                    psg9_df[psg9_df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])][
                                        ['Occurrence Date', 'Incident', 'Impact', 'รายละเอียดการเกิด_Anonymized']],
                                    hide_index=True, use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.success("อุบัติการณ์ทั้งหมดในหมวดนี้ได้รับการแก้ไขแล้ว")

        # --- Tab ที่ 2: วิเคราะห์ตามกลุ่มหลัก (C/G) ---
        with tab_groups:
            # ------------------ ส่วนของกลุ่มอุบัติการณ์ทางคลินิก (C) ------------------
            st.markdown("#### กลุ่มอุบัติการณ์ทางคลินิก (รหัสขึ้นต้นด้วย C)")
            df_clinical = df[df['รหัส'].str.startswith('C', na=False)].copy()

            if df_clinical.empty:
                st.info("ไม่พบข้อมูลอุบัติการณ์กลุ่ม Clinical ในช่วงเวลานี้")
            else:
                st.subheader("ภาพรวมอุบัติการณ์กลุ่ม Clinical")
                clinical_summary_table = create_summary_table_by_category(df_clinical, 'หมวด')
                if not clinical_summary_table.empty:
                    st.dataframe(clinical_summary_table, use_container_width=True)
                else:
                    st.info("ไม่มีข้อมูลเพียงพอสำหรับสร้างตารางสรุป")
                st.markdown("---")

                st.subheader("เจาะลึกสถานะการแก้ไขตามหมวดย่อย (Clinical)")
                clinical_categories = sorted([cat for cat in df_clinical['หมวด'].unique() if cat and pd.notna(cat)])
                for category in clinical_categories:
                    category_df = df_clinical[df_clinical['หมวด'] == category]
                    total_count = len(category_df)
                    resolved_df = category_df[
                        ~category_df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                    resolved_count = len(resolved_df)
                    unresolved_count = total_count - resolved_count

                    expander_title = f"{category} (ทั้งหมด: {total_count} | แก้ไขแล้ว: {resolved_count} | รอแก้ไข: {unresolved_count})"
                    with st.expander(expander_title):
                        tab_resolved, tab_unresolved = st.tabs(
                            [f"รายการที่แก้ไขแล้ว ({resolved_count})", f"รายการที่รอการแก้ไข ({unresolved_count})"])
                        with tab_resolved:
                            if resolved_count > 0:
                                st.dataframe(
                                    resolved_df[['Occurrence Date', 'Incident', 'Impact', 'Resulting Actions']],
                                    hide_index=True, use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.info("ไม่มีรายการที่แก้ไขแล้วในหมวดนี้")
                        with tab_unresolved:
                            if unresolved_count > 0:
                                st.dataframe(category_df[category_df['Resulting Actions'].astype(str).isin(
                                    ['None', '', 'nan'])][['Occurrence Date', 'Incident', 'Impact',
                                                           'รายละเอียดการเกิด_Anonymized']], hide_index=True,
                                             use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.success("อุบัติการณ์ทั้งหมดในหมวดนี้ได้รับการแก้ไขแล้ว")

            st.markdown("---")

            # ------------------ ส่วนของกลุ่มอุบัติการณ์ทั่วไป (G) ------------------
            st.markdown("#### กลุ่มอุบัติการณ์ทั่วไป (รหัสขึ้นต้นด้วย G)")
            df_general = df[df['รหัส'].str.startswith('G', na=False)].copy()

            if df_general.empty:
                st.info("ไม่พบข้อมูลอุบัติการณ์กลุ่ม General ในช่วงเวลานี้")
            else:
                st.subheader("ภาพรวมอุบัติการณ์กลุ่ม General")
                general_summary_table = create_summary_table_by_category(df_general, 'หมวด')
                if not general_summary_table.empty:
                    st.dataframe(general_summary_table, use_container_width=True)
                else:
                    st.info("ไม่มีข้อมูลเพียงพอสำหรับสร้างตารางสรุป")
                st.markdown("---")

                st.subheader("เจาะลึกสถานะการแก้ไขตามหมวดย่อย (General)")
                general_categories = sorted([cat for cat in df_general['หมวด'].unique() if cat and pd.notna(cat)])
                for category in general_categories:
                    category_df = df_general[df_general['หมวด'] == category]
                    total_count = len(category_df)
                    resolved_df = category_df[
                        ~category_df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                    resolved_count = len(resolved_df)
                    unresolved_count = total_count - resolved_count

                    expander_title = f"{category} (ทั้งหมด: {total_count} | แก้ไขแล้ว: {resolved_count} | รอแก้ไข: {unresolved_count})"
                    with st.expander(expander_title):
                        tab_resolved, tab_unresolved = st.tabs(
                            [f"รายการที่แก้ไขแล้ว ({resolved_count})", f"รายการที่รอการแก้ไข ({unresolved_count})"])
                        with tab_resolved:
                            if resolved_count > 0:
                                st.dataframe(
                                    resolved_df[['Occurrence Date', 'Incident', 'Impact', 'Resulting Actions']],
                                    hide_index=True, use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.info("ไม่มีรายการที่แก้ไขแล้วในหมวดนี้")
                        with tab_unresolved:
                            if unresolved_count > 0:
                                st.dataframe(category_df[category_df['Resulting Actions'].astype(str).isin(
                                    ['None', '', 'nan'])][['Occurrence Date', 'Incident', 'Impact',
                                                           'รายละเอียดการเกิด_Anonymized']], hide_index=True,
                                             use_container_width=True, column_config={
                                        "Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                           format="DD/MM/YYYY")})
                            else:
                                st.success("อุบัติการณ์ทั้งหมดในหมวดนี้ได้รับการแก้ไขแล้ว")

        # --- Tab ที่ 3: วิเคราะห์รายรหัส ---
        with tab_by_code:
            st.subheader("ภาพรวมอุบัติการณ์จำแนกตามรหัส")
            st.info(
                "แสดงตารางสรุปจำนวนอุบัติการณ์ในแต่ละระดับความรุนแรงตามรหัส และกราฟแสดงเฉพาะอุบัติการณ์รุนแรง (E-I) ที่พบบ่อย")

            summary_table_code = create_summary_table_by_code(df)

            if summary_table_code.empty:
                st.warning("ไม่พบข้อมูลสำหรับสร้างตารางสรุปรายรหัส")
            else:
                st.markdown("##### ตารางสรุปอุบัติการณ์รายรหัส")
                st.dataframe(summary_table_code, use_container_width=True)
                st.markdown("---")

                st.markdown("##### กราฟแสดงอุบัติการณ์รุนแรง (ระดับ E-I) ที่พบบ่อย")
                chart_data = summary_table_code[summary_table_code['รวม E-up'] > 0].copy()
                
                if chart_data.empty:
                    st.success("ไม่พบอุบัติการณ์รุนแรง (E-I) ในช่วงข้อมูลที่เลือก")
                else:
                    max_n = min(30, len(chart_data))
                    if max_n <= 1:
                        # มีข้อมูล 1 รายการ (หรือกรณีสุดวิสัยที่น้อยกว่านั้น)
                        top_n_chart = 1
                        st.caption("มีข้อมูลเพียง 1 รหัส จึงแสดงทั้งหมดโดยไม่ต้องเลือกจำนวน")
                    else:
                        top_n_chart = st.slider(
                            "เลือกจำนวนรหัสที่ต้องการแสดงบนกราฟ:",
                            min_value=1,
                            max_value=max_n,
                            value=min(15, max_n),
                            step=1,
                            key="top_n_chart_slider_tab"
                        )
                
                    top_chart_data = chart_data.nlargest(top_n_chart, 'รวม E-up')
                    fig = px.bar(
                        top_chart_data.sort_values('รวม E-up', ascending=True),
                        x='รวม E-up', y=top_chart_data.index, orientation='h',
                        title=f'Top {top_n_chart} รหัสอุบัติการณ์ที่มีความรุนแรงสูง (E-I) สะสม',
                        labels={'รวม E-up': 'จำนวนครั้งสะสม (E-I)', 'y': 'รหัสอุบัติการณ์'},
                        text='รวม E-up', color='รวม E-up', color_continuous_scale='Reds'
                    )
                    fig.update_layout(height=max(400, len(top_chart_data) * 25), yaxis_title=None, coloraxis_showscale=False)
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)


        # --- Tab ที่ 4: รายการอุบัติการณ์ที่รอการแก้ไข ---
        with tab_waitlist:
            st.subheader("สรุปเปอร์เซ็นต์การแก้ไขอุบัติการณ์รุนแรง (E-I & 3-5)")

            # คำนวณค่าที่จำเป็นจาก 'df' ที่รับเข้ามาในฟังก์ชันนี้โดยตรง
            severe_impact_levels_list = ['3', '4', '5']
            severe_df = df[df['Impact Level'].isin(severe_impact_levels_list)].copy()
            total_severe_incidents = severe_df.shape[0]

            total_severe_psg9_incidents = severe_df[severe_df['รหัส'].isin(psg9_r_codes_for_counting)].shape[
                0] if psg9_r_codes_for_counting else 0

            total_severe_unresolved_incidents_val = 0
            total_severe_unresolved_psg9_incidents_val = 0

            if 'Resulting Actions' in df.columns:
                unresolved_severe_df = severe_df[severe_df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                total_severe_unresolved_incidents_val = unresolved_severe_df.shape[0]
                total_severe_unresolved_psg9_incidents_val = \
                unresolved_severe_df[unresolved_severe_df['รหัส'].isin(psg9_r_codes_for_counting)].shape[
                    0] if psg9_r_codes_for_counting else 0

            val_row3_total_pct = (
                    total_severe_unresolved_incidents_val / total_severe_incidents * 100) if total_severe_incidents > 0 else 0
            val_row3_psg9_pct = (
                    total_severe_unresolved_psg9_incidents_val / total_severe_psg9_incidents * 100) if total_severe_psg9_incidents > 0 else 0

            summary_action_data = [
                {"รายละเอียด": "1. จำนวนอุบัติการณ์รุนแรง E-I & 3-5", "ทั้งหมด": f"{total_severe_incidents:,}",
                 "เฉพาะ PSG9": f"{total_severe_psg9_incidents:,}"},
                {"รายละเอียด": "2. อุบัติการณ์ E-I & 3-5 ที่ยังไม่ได้รับการแก้ไข",
                 "ทั้งหมด": f"{total_severe_unresolved_incidents_val:,}",
                 "เฉพาะ PSG9": f"{total_severe_unresolved_psg9_incidents_val:,}"},
                {"รายละเอียด": "3. % อุบัติการณ์ E-I & 3-5 ที่ยังไม่ได้รับการแก้ไข",
                 "ทั้งหมด": f"{val_row3_total_pct:.2f}%", "เฉพาะ PSG9": f"{val_row3_psg9_pct:.2f}%"}
            ]
            st.dataframe(pd.DataFrame(summary_action_data).set_index('รายละเอียด'), use_container_width=True)

            st.subheader("รายการอุบัติการณ์ที่รอการแก้ไข (ตามความรุนแรง)")
            unresolved_df = df[df['Resulting Actions'].astype(str).isin(['None', '', 'nan'])].copy()

            if unresolved_df.empty:
                st.success("🎉 ไม่พบรายการที่รอการแก้ไขในช่วงเวลานี้ ยอดเยี่ยมมากครับ!")
            else:
                st.metric("จำนวนรายการที่รอการแก้ไขทั้งหมด", f"{len(unresolved_df):,} รายการ")
                severity_order = ['Critical', 'High', 'Medium', 'Low', 'Undefined']
                for severity in severity_order:
                    severity_df = unresolved_df[unresolved_df['Category Color'] == severity]
                    if not severity_df.empty:
                        with st.expander(f"ระดับความรุนแรง: {severity} ({len(severity_df)} รายการ)"):
                            display_cols = ['Occurrence Date', 'Incident', 'Impact',
                                            'รายละเอียดการเกิด_Anonymized']

                            st.dataframe(severity_df[display_cols], use_container_width=True, hide_index=True,
                                         column_config={"Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด",
                                                                                                           format="DD/MM/YYYY")})


def render_risk_matrix_interactive(df: pd.DataFrame, key_prefix: str = "main_rmx"):
    st.subheader("Risk Matrix (Interactive)")
    impact_level_keys = ['5', '4', '3', '2', '1'];
    freq_level_keys = ['1', '2', '3', '4', '5']
    matrix_df = df[
        df['Impact Level'].astype(str).isin(impact_level_keys) &
        df['Frequency Level'].astype(str).isin(freq_level_keys)
        ].copy()
    matrix_data_counts = np.zeros((5, 5), dtype=int)
    if not matrix_df.empty:
        risk_counts_df = matrix_df.groupby(['Impact Level', 'Frequency Level']).size().reset_index(name='counts')
        for _, row in risk_counts_df.iterrows():
            r = impact_level_keys.index(str(row['Impact Level']))
            c = freq_level_keys.index(str(row['Frequency Level']))
            matrix_data_counts[r, c] = int(row['counts'])

    impact_labels_display = {
        '5': "I / 5<br>Extreme / Death", '4': "G-H / 4<br>Major / Severe", '3': "E-F / 3<br>Moderate",
        '2': "C-D / 2<br>Minor / Low", '1': "A-B / 1<br>Insignificant / No Harm",
    }
    freq_labels_display_short = {"1": "F1", "2": "F2", "3": "F3", "4": "F4", "5": "F5"}
    freq_labels_display_long = {
        "1": "Remote<br>(<2/mth)", "2": "Uncommon<br>(2-3/mth)", "3": "Occasional<br>(4-6/mth)",
        "4": "Probable<br>(7-29/mth)", "5": "Frequent<br>(>=30/mth)",
    }

    cols_header = st.columns([2.2, 1, 1, 1, 1, 1])
    with cols_header[0]:
        st.markdown(
            f"<div style='background-color:{HEADER_TOPLEFT}; color:{_text_color_for(HEADER_TOPLEFT)}; "
            f"padding:8px; text-align:center; font-weight:bold; border-radius:3px; margin:1px; height:60px; "
            f"display:flex; align-itemsV:center; justify-content:center;'>Impact / Frequency</div>",
            unsafe_allow_html=True
        )
    for i, fl in enumerate(freq_level_keys):
        with cols_header[i + 1]:
            st.markdown(
                f"<div style='background-color:{HEADER_FREQ}; color:{_text_color_for(HEADER_FREQ)}; "
                f"padding:8px; text-align:center; font-weight:bold; border-radius:3px; margin:1px; height:60px; "
                f"display:flex; flex-direction:column; align-items:center; justify-content:center;'>"
                f"<div>{freq_labels_display_short[fl]}</div>"
                f"<div style='font-size:0.7em;'>{freq_labels_display_long[fl]}</div></div>",
                unsafe_allow_html=True
            )
    for r, il in enumerate(impact_level_keys):
        row_cols = st.columns([2.2, 1, 1, 1, 1, 1])
        with row_cols[0]:
            st.markdown(
                f"<div style='background-color:{HEADER_SIDE}; color:{_text_color_for(HEADER_SIDE)}; "
                f"padding:8px; text-align:center; font-weight:bold; border-radius:3px; margin:1px; height:70px; "
                f"display:flex; align-items:center; justify-content:center;'>{impact_labels_display[il]}</div>",
                unsafe_allow_html=True
            )
        for c, fl in enumerate(freq_level_keys):
            with row_cols[c + 1]:
                code = f'{il}{fl}'
                cell_bg = PALETTE_FROM_IMAGE.get(code, "#808080")
                cnt = int(matrix_data_counts[r, c])
                st.markdown(
                    f"<div style='background-color:{cell_bg}; color:{_text_color_for(cell_bg)}; "
                    f"padding:5px; margin:1px; border-radius:3px; text-align:center; font-weight:bold; "
                    f"min-height:40px; display:flex; align-items:center; justify-content:center;'>{cnt}</div>",
                    unsafe_allow_html=True
                )
                if cnt > 0:
                    if st.button("👁️", key=f"{key_prefix}_view_{code}", help=f"ดูรายการ - {cnt} รายการ",
                                 use_container_width=True):
                        st.session_state[f"{key_prefix}_il"] = il
                        st.session_state[f"{key_prefix}_fl"] = fl
                        st.session_state[f"{key_prefix}_show"] = True
                        st.rerun()
                else:
                    st.markdown("<div style='height:38px; margin-top:5px;'></div>", unsafe_allow_html=True)

    if st.session_state.get(f"{key_prefix}_show", False):
        il_selected = st.session_state.get(f"{key_prefix}_il")
        fl_selected = st.session_state.get(f"{key_prefix}_fl")
        df_incidents = df[
            (df['Impact Level'].astype(str) == str(il_selected)) &
            (df['Frequency Level'].astype(str) == str(fl_selected))
            ].copy()
        disp_cols_default = ['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Impact Level', 'Frequency Level', 'Risk Level',
                             'Occurrence Date', 'หน่วยงาน', 'กลุ่มงาน']
        display_cols = [c for c in disp_cols_default if c in df_incidents.columns]
        with st.expander(
                f"รายการอุบัติการณ์: Impact {il_selected} × Frequency {fl_selected} – {len(df_incidents)} รายการ",
                expanded=True):
            st.dataframe(df_incidents[display_cols], use_container_width=True, hide_index=True)
            if st.button("ปิดรายการ", key=f"{key_prefix}_close"):
                st.session_state[f"{key_prefix}_show"] = False
                st.session_state[f"{key_prefix}_il"] = None
                st.session_state[f"{key_prefix}_fl"] = None
                st.rerun()


def render_risk_level_summary(df: pd.DataFrame):
    st.subheader("ตารางสรุปสีตามระดับความเสี่ยงสูงสุดของแต่ละอุบัติการณ์")
    st.info("สีและป้ายกำกับ (I: Impact, F: Frequency) มาจากช่องที่มีความเสี่ยงสูงสุดของอุบัติการณ์ประเภทนั้นๆ")

    required = {'Impact Level', 'Frequency Level', 'รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง'}
    if not required.issubset(df.columns):
        st.warning("ไม่พบคอลัมน์ที่จำเป็น ('Impact Level','Frequency Level','รหัส','ชื่ออุบัติการณ์ความเสี่ยง')")
        return

    order = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5}
    tmp = df.copy()
    tmp['I_num'] = tmp['Impact Level'].map(order).fillna(0).astype(int)
    tmp['F_num'] = tmp['Frequency Level'].map(order).fillna(0).astype(int)
    tmp['score'] = tmp['I_num'] * 10 + tmp['F_num']  # ให้ Impact สำคัญกว่า

    idx = tmp.groupby(['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง'])['score'].idxmax()
    incident_risk_summary = (
        tmp.loc[idx, ['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Impact Level', 'Frequency Level', 'Incident Rate/mth']]
        .rename(columns={'Impact Level': 'max_impact_level',
                         'Frequency Level': 'frequency_level',
                         'Incident Rate/mth': 'total_occurrences'})
    )

    # ใช้ฟังก์ชัน _text_color_for() ที่เรานิยามไว้ข้างบน
    incident_risk_summary['risk_color_hex'] = incident_risk_summary.apply(
        lambda r: PALETTE_FROM_IMAGE.get(f"{str(r['max_impact_level'])}{str(r['frequency_level'])}", "#808080"), axis=1
    )
    if 'total_occurrences' in incident_risk_summary.columns:
        incident_risk_summary = incident_risk_summary.sort_values('total_occurrences', ascending=False)

    for _, row in incident_risk_summary.iterrows():
        color = row['risk_color_hex'];
        text_color = _text_color_for(color)
        risk_label = f"I: {row['max_impact_level']} | F: {row['frequency_level']}"
        c1, c2 = st.columns([1, 6])
        with c1:
            st.markdown(
                f'<div style="background-color:{color}; color:{text_color}; font-weight:bold; '
                f'text-align:center; padding:8px; border-radius:6px; height:100%; '
                f'display:flex; align-items:center; justify-content:center;">{risk_label}</div>',
                unsafe_allow_html=True
            )
        with c2:
            tot = row.get('total_occurrences', 0)
            st.markdown(f"**{row['รหัส']} | {row['ชื่ออุบัติการณ์ความเสี่ยง']}** "
                        f"(อัตราการเกิด: {float(tot):.2f} ครั้ง/เดือน)")


# --- START: Helper Functions for Incident Analysis ---

def create_psg9_summary_table(input_df):
    if not isinstance(input_df,
                      pd.DataFrame) or 'หมวดหมู่มาตรฐานสำคัญ' not in input_df.columns or 'Impact' not in input_df.columns: return None
    psg9_placeholders = ["ไม่จัดอยู่ใน PSG9 Catalog", "ไม่สามารถระบุ (Merge PSG9 ล้มเหลว)",
                         "ไม่สามารถระบุ (เช็คคอลัมน์ใน PSG9code.xlsx)",
                         "ไม่สามารถระบุ (PSG9code.xlsx ไม่ได้โหลด/ว่างเปล่า)",
                         "ไม่สามารถระบุ (Merge PSG9 ล้มเหลว - rename)", "ไม่สามารถระบุ (Merge PSG9 ล้มเหลว - no col)",
                         "ไม่สามารถระบุ (PSG9code.xlsx ไม่ได้โหลด/ข้อมูลไม่ครบถ้วน)"]
    df_filtered = input_df[
        ~input_df['หมวดหมู่มาตรฐานสำคัญ'].isin(psg9_placeholders) & input_df['หมวดหมู่มาตรฐานสำคัญ'].notna()].copy()
    if df_filtered.empty: return pd.DataFrame()
    try:
        summary_table = pd.crosstab(df_filtered['หมวดหมู่มาตรฐานสำคัญ'], df_filtered['Impact'], margins=True,
                                    margins_name='รวม A-I')
    except Exception:
        return pd.DataFrame()
    if 'รวม A-I' in summary_table.index: summary_table = summary_table.drop(index='รวม A-I')
    if summary_table.empty: return pd.DataFrame()
    all_impacts, e_up_impacts = list('ABCDEFGHI'), list('EFGHI')
    for impact_col in all_impacts:
        if impact_col not in summary_table.columns: summary_table[impact_col] = 0
    if 'รวม A-I' not in summary_table.columns: summary_table['รวม A-I'] = summary_table[
        [col for col in all_impacts if col in summary_table.columns]].sum(axis=1)
    summary_table['รวม E-up'] = summary_table[[col for col in e_up_impacts if col in summary_table.columns]].sum(axis=1)
    summary_table['ร้อยละ E-up'] = (summary_table['รวม E-up'] / summary_table['รวม A-I'] * 100).fillna(0)
    # (PSG9_label_dict เป็นตัวแปร global ที่โหลดไว้ตอนเริ่มแอป)
    psg_order = [PSG9_label_dict[i] for i in sorted(PSG9_label_dict.keys()) if i in PSG9_label_dict]
    summary_table = summary_table.reindex(psg_order).fillna(0)
    display_cols_order = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'รวม E-up', 'รวม A-I', 'ร้อยละ E-up']
    final_table = summary_table[[col for col in display_cols_order if col in summary_table.columns]].copy()
    for col in final_table.columns:
        if col != 'ร้อยละ E-up': final_table[col] = final_table[col].astype(int)
    final_table['ร้อยละ E-up'] = final_table['ร้อยละ E-up'].map('{:.2f}%'.format)
    return final_table


def create_summary_table_by_code(dataframe):
    """
    สร้างตารางสรุปจำนวนอุบัติการณ์ตาม 'รหัส' และระดับความรุนแรง
    โดยในแถวจะแสดงทั้งรหัสและชื่อของอุบัติการณ์
    """
    required_cols = ['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Impact']
    if not all(col in dataframe.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in dataframe.columns]
        st.warning(f"ไม่สามารถสร้างตารางได้ เนื่องจากขาดคอลัมน์: {', '.join(missing_cols)}")
        return pd.DataFrame()

    df_copy = dataframe.copy()
    df_copy['รหัส | ชื่ออุบัติการณ์'] = df_copy['รหัส'].astype(str) + " | " + df_copy[
        'ชื่ออุบัติการณ์ความเสี่ยง'].fillna('')
    df_valid = df_copy.dropna(subset=['รหัส | ชื่ออุบัติการณ์', 'Impact'])
    if df_valid.empty:
        return pd.DataFrame()

    summary = pd.crosstab(df_valid['รหัส | ชื่ออุบัติการณ์'], df_valid['Impact'])
    severity_levels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    summary = summary.reindex(columns=severity_levels, fill_value=0)
    e_to_i_cols = [col for col in ['E', 'F', 'G', 'H', 'I'] if col in summary.columns]
    summary['รวม E-up'] = summary[e_to_i_cols].sum(axis=1)
    total_e_up_incidents = summary['รวม E-up'].sum()

    if total_e_up_incidents > 0:
        summary['ร้อยละ E-up'] = (summary['รวม E-up'] / total_e_up_incidents * 100).map('{:.2f}%'.format)
    else:
        summary['ร้อยละ E-up'] = '0.00%'

    summary = summary[summary.drop(columns=['ร้อยละ E-up']).sum(axis=1) > 0]
    summary.index.name = "รหัส | ชื่ออุบัติการณ์"
    return summary


def create_summary_table_by_category(dataframe, category_column_name):
    """
    สร้างตารางสรุปจำนวนอุบัติการณ์ตามหมวดหมู่และระดับความรุนแรง
    """
    if category_column_name not in dataframe.columns or 'Impact' not in dataframe.columns:
        st.error(f"ไม่พบคอลัมน์ '{category_column_name}' หรือ 'Impact' ในข้อมูล")
        return pd.DataFrame()

    df_valid = dataframe.dropna(subset=[category_column_name, 'Impact'])
    if df_valid.empty:
        return pd.DataFrame()

    summary = pd.crosstab(df_valid[category_column_name], df_valid['Impact'])
    severity_levels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    summary = summary.reindex(columns=severity_levels, fill_value=0)
    e_to_i_cols = [col for col in ['E', 'F', 'G', 'H', 'I'] if col in summary.columns]
    summary['รวม E-up'] = summary[e_to_i_cols].sum(axis=1)
    total_e_up_incidents = summary['รวม E-up'].sum()

    if total_e_up_incidents > 0:
        summary['ร้อยละ E-up'] = (summary['รวม E-up'] / total_e_up_incidents * 100).map('{:.2f}%'.format)
    else:
        summary['ร้อยละ E-up'] = '0.00%'

    summary.index.name = "หมวดหมู่"
    return summary


# --- END: Helper Functions for Incident Analysis ---


def create_goal_summary_table(data_df_goal: pd.DataFrame, goal_category_name_param: str,
                              e_up_non_numeric_levels_param=None,
                              e_up_numeric_levels_param=None,
                              is_org_safety_table: bool = False) -> pd.DataFrame:
    """
    เวอร์ชันง่าย: เลือกแถวที่ 'หมวด' มีคำขึ้นต้นตรงกับตัวอักษรก่อน colon (P/S/O)
    แล้วสรุปจำนวนเหตุการณ์ต่อรหัส
    """
    if data_df_goal.empty or 'หมวด' not in data_df_goal.columns: return pd.DataFrame()
    key = goal_category_name_param.split(":")[0].strip()  # "P" / "S" / "O"
    sub = data_df_goal[data_df_goal['หมวด'].astype(str).str.startswith(key, na=False)].copy()
    if sub.empty: return pd.DataFrame()
    cnt = sub['รหัส'].value_counts().reset_index()
    cnt.columns = ['รหัส', 'จำนวน']
    if 'ชื่ออุบัติการณ์ความเสี่ยง' in sub.columns:
        names = sub[['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง']].drop_duplicates()
        cnt = cnt.merge(names, on='รหัส', how='left')
        cnt = cnt[['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'จำนวน']]
    return cnt


@st.cache_data
def calculate_persistence_risk_score(_df: pd.DataFrame, total_months: int):
    risk_level_map_to_score = {"51": 21, "52": 22, "53": 23, "54": 24, "55": 25, "41": 16, "42": 17, "43": 18, "44": 19,
                               "45": 20, "31": 11, "32": 12, "33": 13, "34": 14, "35": 15, "21": 6, "22": 7, "23": 8,
                               "24": 9, "25": 10, "11": 1, "12": 2, "13": 3, "14": 4, "15": 5}
    if _df.empty or 'รหัส' not in _df.columns or 'Risk Level' not in _df.columns: return pd.DataFrame()
    analysis_df = _df[['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Risk Level']].copy()
    analysis_df['Ordinal_Risk_Score'] = analysis_df['Risk Level'].astype(str).map(risk_level_map_to_score)
    analysis_df.dropna(subset=['Ordinal_Risk_Score'], inplace=True)
    if analysis_df.empty: return pd.DataFrame()
    persistence_metrics = analysis_df.groupby('รหัส').agg(Average_Ordinal_Risk_Score=('Ordinal_Risk_Score', 'mean'),
                                                          Total_Occurrences=('รหัส', 'size')).reset_index()
    total_months = max(1, total_months)
    persistence_metrics['Incident_Rate_Per_Month'] = persistence_metrics['Total_Occurrences'] / total_months
    max_rate = max(1, persistence_metrics['Incident_Rate_Per_Month'].max()) if not persistence_metrics.empty else 1
    persistence_metrics['Frequency_Score'] = persistence_metrics['Incident_Rate_Per_Month'] / max_rate
    persistence_metrics['Avg_Severity_Score'] = persistence_metrics['Average_Ordinal_Risk_Score'] / 25.0
    persistence_metrics['Persistence_Risk_Score'] = persistence_metrics['Frequency_Score'] + persistence_metrics[
        'Avg_Severity_Score']
    incident_names = _df[['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง']].drop_duplicates()
    final_df = pd.merge(persistence_metrics, incident_names, on='รหัส', how='left')
    return final_df.sort_values(by='Persistence_Risk_Score', ascending=False)


def prioritize_incidents_nb_logit_v2(_df: pd.DataFrame, horizon: int = 3,
                                     w_freq: float = 0.34, w_sev: float = 0.33, w_trend: float = 0.33) -> pd.DataFrame:
    # Stub ง่าย: เรียงความถี่ย้อนหลัง + ความรุนแรงเฉลี่ย
    if _df.empty: return pd.DataFrame()
    tmp = _df.copy()
    tmp['RiskScore'] = tmp['Risk Level'].map(lambda x: int(x) if str(x).isdigit() else 0)
    agg = tmp.groupby(['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง']).agg(
        total=('รหัส', 'size'),
        avg_risk=('RiskScore', 'mean')
    ).reset_index()
    agg['score'] = w_freq * (agg['total'] / max(1, agg['total'].max())) + w_sev * (
                agg['avg_risk'] / max(1, agg['avg_risk'].max()))
    return agg.sort_values('score', ascending=False)

# =========================
# 8) MAIN DISPLAY AREA
# =========================
selected_page = st.session_state.get('selected_analysis', "แดชบอร์ดสรุปภาพรวม")

if selected_page == "RCA Helpdesk (AI Assistant)":
    st.markdown("<h4 style='color: #001f3f;'>AI Assistant: ที่ปรึกษาเคสอุบัติการณ์</h4>", unsafe_allow_html=True)
    AI_IS_CONFIGURED = False
    if genai:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key); AI_IS_CONFIGURED = True
            except Exception as e:
                st.error(f"⚠️ ตั้งค่า AI ผิดพลาด: {e}")
        else:
            st.error("⚠️ ไม่พบ GOOGLE_API_KEY")
        if not AI_IS_CONFIGURED:
            st.warning("AI ไม่ได้ตั้งค่า")

    if AI_IS_CONFIGURED:
        st.info("อธิบายรายละเอียดเคสที่ต้องการปรึกษา (ไม่ระบุตัวตนผู้ป่วย)")
        incident_description = st.text_area("รายละเอียดเหตุการณ์", height=150, key="rca_incident_input")
        if st.button("ขอคำปรึกษา AI", type="primary", use_container_width=True):
            if not incident_description.strip():
                st.warning("กรุณาป้อนรายละเอียด")
            else:
                with st.spinner("AI กำลังวิเคราะห์..."):
                    consultation = get_consultation_response(incident_description)
                    st.markdown("--- \n ### ผลปรึกษา AI:")
                    st.markdown(consultation)
    else:
        st.info("AI Assistant ยังไม่เปิดใช้งาน")

elif selected_page == "แดชบอร์ดสรุปภาพรวม":
    st.markdown("<h4 style='color: #001f3f;'>สรุปภาพรวมอุบัติการณ์:</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:

        # --- START: เพิ่มโค้ดคำนวณและแสดงผลช่วงข้อมูล ---
        min_date_filt = filtered['Occurrence Date'].min(); max_date_filt = filtered['Occurrence Date'].max()
        min_date_str = min_date_filt.strftime('%d/%m/%Y') if pd.notna(min_date_filt) else "N/A"
        max_date_str = max_date_filt.strftime('%d/%m/%Y') if pd.notna(max_date_filt) else "N/A"
        total_month = 0
        if pd.notna(min_date_filt) and pd.notna(max_date_filt):
            max_p_filt = max_date_filt.to_period('M'); min_p_filt = min_date_filt.to_period('M')
            total_month = max(1, (max_p_filt.year - min_p_filt.year) * 12 + (max_p_filt.month - min_p_filt.month) + 1)

        st.markdown(f"**ช่วงข้อมูลที่วิเคราะห์:** {min_date_str} ถึง {max_date_str} (รวม {total_month} เดือน)")
        st.markdown("---") # เพิ่มเส้นคั่น
        # --- END: เพิ่มโค้ด ---

        cA, cB, cC, cD, cE = st.columns(5)
        # จำนวนเหตุการณ์ (แถว)
        cA.metric("จำนวนเหตุการณ์ (แถว)", f"{len(filtered):,}")
        # ชนิดอุบัติการณ์ (Incident)
        incident_unique = filtered['Incident'].nunique() if 'Incident' in filtered.columns else 0
        cB.metric("ชนิดอุบัติการณ์ (Incident)", f"{incident_unique:,}")
        # จำนวนหน่วยงาน
        unit_unique = filtered[REF_COL].nunique() if REF_COL in filtered.columns else 0
        cC.metric("จำนวนหน่วยงาน", f"{unit_unique:,}")
        # จำนวนกลุ่มงาน
        group_unique = filtered['กลุ่มงาน'].nunique() if 'กลุ่มงาน' in filtered.columns else 0
        cD.metric("จำนวนกลุ่มงาน", f"{group_unique:,}")

        # --- เพิ่ม Metric ใหม่สำหรับ Self-Report ---
        if 'self_report' in filtered.columns:
            total_self_reports = int(filtered['self_report'].sum())
            cE.metric("Self-Reports (นับ 1)", f"{total_self_reports:,}")
        else:
            cE.metric("Self-Reports", "N/A")
        st.markdown("#### เหตุการณ์ต่อกลุ่มงาน")
        if 'กลุ่มงาน' in filtered.columns and not filtered['กลุ่มงาน'].isna().all():
            group_counts = (
                filtered
                .groupby("กลุ่มงาน", observed=True)
                .size()
                .reset_index(name="จำนวนเหตุการณ์")
                .sort_values("จำนวนเหตุการณ์", ascending=False)
            )
            st.dataframe(group_counts, use_container_width=True)
        else:
            st.info("ไม่พบคอลัมน์ 'กลุ่มงาน' หรือไม่มีข้อมูล")

            # --- START: เพิ่มตารางสรุป Self-Report ---
        st.markdown("---")  # เพิ่มเส้นคั่น

        # 1. สรุปตามกลุ่มงาน
        st.markdown("#### Self-Report ต่อกลุ่มงาน")
        if 'self_report' in filtered.columns and filtered['self_report'].sum() > 0:
            self_report_group_counts = (
                filtered.groupby("กลุ่มงาน", observed=True)['self_report']
                .sum()
                .reset_index(name="จำนวน Self-Report")
                .astype({"จำนวน Self-Report": int})  # แปลงเป็นเลขจำนวนเต็ม
            )
            # กรองเอาเฉพาะกลุ่มงานที่มี report
            self_report_group_counts = self_report_group_counts[self_report_group_counts["จำนวน Self-Report"] > 0]
            self_report_group_counts = self_report_group_counts.sort_values("จำนวน Self-Report", ascending=False)

            st.dataframe(self_report_group_counts, use_container_width=True, hide_index=True)
        else:
            st.info("ไม่พบข้อมูล Self-Report ในกลุ่มงานที่เลือก")

        # 2. สรุปตามหน่วยงาน (REF_COL คือ "หน่วยงาน")
        st.markdown("#### Self-Report ต่อหน่วยงาน (Top 20)")
        if 'self_report' in filtered.columns and filtered['self_report'].sum() > 0:
            self_report_unit_counts = (
                filtered.groupby(REF_COL, observed=True)['self_report']
                .sum()
                .reset_index(name="จำนวน Self-Report")
                .astype({"จำนวน Self-Report": int})  # แปลงเป็นเลขจำนวนเต็ม
            )
            # กรองเอาเฉพาะหน่วยงานที่มี report
            self_report_unit_counts = self_report_unit_counts[self_report_unit_counts["จำนวน Self-Report"] > 0]
            self_report_unit_counts = self_report_unit_counts.sort_values("จำนวน Self-Report", ascending=False)

            # แสดงแค่ Top 20 เพราะอาจจะยาวมาก
            st.dataframe(self_report_unit_counts.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("ไม่พบข้อมูล Self-Report ในหน่วยงานที่เลือก")
        # --- END: เพิ่มตารางสรุป Self-Report ---

    date_format_config = {"Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด", format="DD/MM/YYYY HH:mm")}

    metrics_data_filt = {}
    metrics_data_filt['total_processed_incidents'] = filtered.shape[0]
    metrics_data_filt['total_psg9_incidents_for_metric1'] = filtered[filtered['รหัส'].isin(psg9_r_codes_for_counting)].shape[0] if psg9_r_codes_for_counting else 0

    if sentinel_composite_keys and 'รหัส' in filtered.columns and 'Impact' in filtered.columns:
        filtered['Sentinel code for check'] = filtered['รหัส'].astype(str).str.strip() + '-' + filtered['Impact'].astype(str).str.strip()
        metrics_data_filt['total_sentinel_incidents_for_metric1'] = filtered[filtered['Sentinel code for check'].isin(sentinel_composite_keys)].shape[0]
    else:
        metrics_data_filt['total_sentinel_incidents_for_metric1'] = 0
        if 'Sentinel code for check' not in filtered.columns: filtered['Sentinel code for check'] = ""

        severe_impact_levels_list = ['3', '4', '5']
        df_severe_filt = filtered[filtered['Impact Level'].isin(severe_impact_levels_list)].copy()
        metrics_data_filt['total_severe_incidents'] = df_severe_filt.shape[0]
        if 'Resulting Actions' in filtered.columns:
            unresolved_filt = df_severe_filt[df_severe_filt['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
            metrics_data_filt['total_severe_unresolved_incidents_val'] = unresolved_filt.shape[0]
            metrics_data_filt['total_severe_unresolved_psg9_incidents_val'] = unresolved_filt[unresolved_filt['รหัส'].isin(psg9_r_codes_for_counting)].shape[0] if psg9_r_codes_for_counting else 0
        else:
            metrics_data_filt['total_severe_unresolved_incidents_val'] = "N/A"
            metrics_data_filt['total_severe_unresolved_psg9_incidents_val'] = "N/A"

        total_processed_incidents = metrics_data_filt.get("total_processed_incidents", 0)
        total_psg9_incidents_for_metric1 = metrics_data_filt.get("total_psg9_incidents_for_metric1", 0)
        total_sentinel_incidents_for_metric1 = metrics_data_filt.get("total_sentinel_incidents_for_metric1", 0)
        total_severe_incidents = metrics_data_filt.get("total_severe_incidents", 0)
        total_severe_unresolved_incidents_val = metrics_data_filt.get("total_severe_unresolved_incidents_val", "N/A")
        total_severe_unresolved_psg9_incidents_val = metrics_data_filt.get("total_severe_unresolved_psg9_incidents_val", "N/A")
        df_severe_incidents = filtered[filtered['Impact Level'].isin(['3', '4', '5'])].copy()
        total_severe_psg9_incidents = df_severe_incidents[df_severe_incidents['รหัส'].isin(psg9_r_codes_for_counting)].shape[0] if psg9_r_codes_for_counting else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PSG9", f"{total_psg9_incidents_for_metric1:,}")
            with st.expander(f"ดูรายละเอียด ({total_psg9_incidents_for_metric1})"):
                psg9_df = filtered[filtered['รหัส'].isin(psg9_r_codes_for_counting)]
                cols_to_show_expander = [col for col in display_cols_common if col in psg9_df.columns]
                if not psg9_df.empty: st.dataframe(psg9_df[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)
                else: st.info("ไม่มีรายการ PSG9")
        with col2:
            st.metric("Sentinel", f"{total_sentinel_incidents_for_metric1:,}")
            with st.expander(f"ดูรายละเอียด ({total_sentinel_incidents_for_metric1})"):
                if 'Sentinel code for check' in filtered.columns and not filtered['Sentinel code for check'].empty:
                    sentinel_df = filtered[filtered['Sentinel code for check'].isin(sentinel_composite_keys)]
                    if not sentinel_df.empty:
                        cols_to_show_expander = [col for col in display_cols_common if col in sentinel_df.columns]
                        st.dataframe(sentinel_df[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)
                    else:
                        st.info("ไม่พบรายการ Sentinel")
                else:
                    st.info("ตรวจสอบ Sentinel ไม่ได้")
        with col3:

            st.metric("E-I & 3-5 [all]", f"{total_severe_incidents:,}")
            with st.expander(f"ดูรายละเอียด ({total_severe_incidents})"):
                cols_to_show_expander = [col for col in display_cols_common if col in df_severe_incidents.columns]
                if not df_severe_incidents.empty: st.dataframe(df_severe_incidents[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)
                else: st.info("ไม่มีรายการรุนแรง")
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("E-I & 3-5 [PSG9]", f"{total_severe_psg9_incidents:,}")
            with st.expander(f"ดูรายละเอียด ({total_severe_psg9_incidents})"):
                severe_psg9_df = df_severe_incidents[df_severe_incidents['รหัส'].isin(psg9_r_codes_for_counting)]
                cols_to_show_expander = [col for col in display_cols_common if col in severe_psg9_df.columns]
                if not severe_psg9_df.empty: st.dataframe(severe_psg9_df[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)
                else: st.info("ไม่มีรายการ PSG9 รุนแรง")
        with col5:
            val_unresolved_all = f"{total_severe_unresolved_incidents_val:,}" if isinstance(total_severe_unresolved_incidents_val, int) else "N/A"
            st.metric(f"E-I & 3-5 [all] ที่ยังไม่แก้ไข", val_unresolved_all)
            if isinstance(total_severe_unresolved_incidents_val, int) and total_severe_unresolved_incidents_val > 0:
                with st.expander(f"ดูรายละเอียด ({total_severe_unresolved_incidents_val})"):
                    unresolved_df_all = filtered[filtered['Impact Level'].isin(['3', '4', '5']) & filtered['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                    cols_to_show_expander = [col for col in display_cols_common if col in unresolved_df_all.columns]
                    st.dataframe(unresolved_df_all[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)
        with col6:
            val_unresolved_psg9 = f"{total_severe_unresolved_psg9_incidents_val:,}" if isinstance(total_severe_unresolved_psg9_incidents_val, int) else "N/A"
            st.metric(f"E-I & 3-5 [PSG9] ที่ยังไม่แก้ไข", val_unresolved_psg9)
            if isinstance(total_severe_unresolved_psg9_incidents_val, int) and total_severe_unresolved_psg9_incidents_val > 0:
                with st.expander(f"ดูรายละเอียด ({total_severe_unresolved_psg9_incidents_val})"):
                    unresolved_df_all = filtered[filtered['Impact Level'].isin(['3', '4', '5']) & filtered['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
                    unresolved_df_psg9 = unresolved_df_all[unresolved_df_all['รหัส'].isin(psg9_r_codes_for_counting)]
                    cols_to_show_expander = [col for col in display_cols_common if col in unresolved_df_psg9.columns]
                    st.dataframe(unresolved_df_psg9[cols_to_show_expander], use_container_width=True, hide_index=True, column_config=date_format_config)

        st.markdown("---")
        monthly_counts = filtered.copy(); monthly_counts['เดือน-ปี'] = monthly_counts['Occurrence Date'].dt.strftime('%Y-%m')
        incident_trend = monthly_counts.groupby('เดือน-ปี').size().reset_index(name='จำนวนอุบัติการณ์').sort_values(by='เดือน-ปี')
        if not incident_trend.empty:
            fig_trend = px.line(incident_trend, x='เดือน-ปี', y='จำนวนอุบัติการณ์', title='จำนวนอุบัติการณ์ (กรองแล้ว) รายเดือน', markers=True, labels={'เดือน-ปี': 'เดือน', 'จำนวนอุบัติการณ์': 'จำนวนครั้ง'}, line_shape='spline')
            fig_trend.update_traces(line=dict(width=3)); st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลแนวโน้มรายเดือน")

        st.markdown("---")
        total_incidents_filt = metrics_data_filt.get('total_processed_incidents', 0)
        resolved_incidents_filt = filtered[~filtered['Resulting Actions'].astype(str).isin(['None', '', 'nan'])].shape[0] if 'Resulting Actions' in filtered else 0
        status_data = pd.DataFrame({'สถานะ': ['อุบัติการณ์ (กรองแล้ว)', 'ที่แก้ไขแล้ว'],'จำนวน': [total_incidents_filt, resolved_incidents_filt]})
        if total_incidents_filt > 0:
            fig_status = px.bar(status_data, x='จำนวน', y='สถานะ', orientation='h', title='ภาพรวมเทียบกับที่แก้ไขแล้ว (กรองแล้ว)', text='จำนวน', color='สถานะ',
                                color_discrete_map={'อุบัติการณ์ (กรองแล้ว)': '#1f77b4', 'ที่แก้ไขแล้ว': '#2ca02c'}, labels={'สถานะ': '', 'จำนวน': 'จำนวน'})
            fig_status.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False); st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลสถานะการแก้ไข")

elif selected_page == "Incidents Analysis":
    if filtered.empty: st.info("ไม่มีข้อมูลตามตัวกรอง")
    else: render_incidents_analysis(filtered)

elif selected_page == "Risk Matrix (Interactive)":
    if filtered.empty: st.info("ไม่มีข้อมูลตามตัวกรอง")
    else: render_risk_matrix_interactive(filtered, key_prefix="main_rmx")

elif selected_page == "Risk level":
    if filtered.empty: st.info("ไม่มีข้อมูลตามตัวกรอง")
    else: render_risk_level_summary(filtered)

elif selected_page == "Risk Register Assistant":
    st.markdown("<h4 style='color: #001f3f;'>Risk Register Assistant</h4>", unsafe_allow_html=True)
    st.info("ป้อน 'รหัส' หรือ 'ชื่ออุบัติการณ์' เพื่อค้นหาข้อมูลเชิงลึก")
    query = st.text_input("ระบุรหัส หรือ คำค้นหา:", key="risk_register_query")
    if st.button("ค้นหา", type="primary", use_container_width=True):
        if not query.strip(): st.warning("กรุณาป้อนคำค้นหา")
        elif filtered.empty: st.warning("ไม่มีข้อมูลให้ค้นหา (ตามตัวกรองปัจจุบัน)")
        else:
            with st.spinner("กำลังค้นหา..."):
                result = get_risk_register_consultation(query=query, df=filtered, risk_mitigation_df=df_mitigation)
                st.markdown("---")
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.subheader("Result Review")
                    st.markdown(f"**{result.get('incident_code','N/A')} - {result.get('incident_name','N/A')}**")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("จำนวนครั้ง", f"{result.get('total_occurrences', 0)} ครั้ง")
                    c2.metric("Impact Level สูงสุด", result.get('max_impact_level', 'N/A'))
                    c3.metric("Frequency Level", result.get('frequency_level', 'N/A'))

                    st.markdown("---")
                    st.markdown(f"##### Review Result: พบ {result.get('total_occurrences', 0)} ครั้ง:")
                    incident_details_df = result.get('incident_df', pd.DataFrame())
                    if not incident_details_df.empty:
                        incident_details_df = incident_details_df.sort_values(by='Occurrence Date', ascending=False)
                        for _, row in incident_details_df.iterrows():
                            event_date = row['Occurrence Date'].strftime('%d %b %Y, %H:%M') if pd.notna(row['Occurrence Date']) else 'N/A'
                            impact = row.get('Impact', 'N/A'); impact_level = row.get('Impact Level', 'N/A')
                            details = row.get('รายละเอียดการเกิด_Anonymized', 'ไม่มีรายละเอียด')
                            st.markdown(f"""<div style="border-left: 4px solid #eee; padding-left: 15px; margin-bottom: 15px;">
                            <b>{event_date}</b> • {impact} (ระดับ {impact_level})<br><em>{details}</em>
                            </div>""", unsafe_allow_html=True)
                    else:
                        st.info("ไม่พบรายละเอียดเหตุการณ์")

                    st.markdown("---")
                    st.markdown("**Risk Transfer & Prevention:**")
                    st.info(result.get('existing_prevention', 'N/A'))
                    st.markdown("**Risk Monitor:**")
                    st.info(result.get('existing_monitor', 'N/A'))

elif selected_page == "Heatmap รายเดือน":
    st.markdown("<h4 style='color: #001f3f;'>Heatmap: จำนวนอุบัติการณ์รายเดือน</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        st.info("💡 Heatmap นี้แสดงความถี่ของอุบัติการณ์รายเดือนสำหรับ Top N รหัส")
        heatmap_req_cols = ['รหัส', 'เดือน', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Incident']
        if not all(col in filtered.columns for col in heatmap_req_cols):
            st.warning("ขาดคอลัมน์ที่จำเป็นสำหรับ Heatmap")
        else:
            df_heat = filtered.copy();
            df_heat['incident_label'] = df_heat['รหัส'] + " | " + df_heat['ชื่ออุบัติการณ์ความเสี่ยง'].fillna('')
            total_counts = df_heat['incident_label'].value_counts().reset_index();
            total_counts.columns = ['incident_label', 'total_count']

            # --- START: แก้ไข Slider ---
            total_incident_types = len(total_counts)
            SLIDER_MIN = 5  # ค่าต่ำสุดที่ Slider จะเริ่ม

            if total_incident_types <= SLIDER_MIN:
                # ถ้าน้อยกว่าหรือเท่ากับ 5 (เช่น 2) ไม่ต้องแสดง slider
                top_n = total_incident_types
                if total_incident_types > 0:
                    st.caption(f"แสดงอุบัติการณ์ทั้งหมด {top_n} รายการ (เนื่องจากมีจำนวนน้อยกว่า {SLIDER_MIN})")
            else:
                # ถ้ามากกว่า 5 (เช่น 6) ถึงจะแสดง slider
                slider_max = min(50, total_incident_types)
                slider_default = min(20, total_incident_types)
                top_n = st.slider("เลือก Top N:", SLIDER_MIN, slider_max, slider_default, 5, key="top_n_slider")
            # --- END: แก้ไข Slider ---

            if top_n == 0:
                st.info("ไม่พบข้อมูลอุบัติการณ์ในกลุ่มนี้")
                df_heat_filtered_view = pd.DataFrame(columns=df_heat.columns)  # สร้าง df ว่าง
            else:
                top_incident_labels = total_counts.nlargest(top_n, 'total_count')['incident_label']
                df_heat_filtered_view = df_heat[df_heat['incident_label'].isin(top_incident_labels)]

            try:
                heatmap_pivot = pd.pivot_table(df_heat_filtered_view, values='Incident', index='incident_label',
                                               columns='เดือน', aggfunc='count', fill_value=0)
                sorted_month_names = [v for k, v in sorted(month_label.items())]
                available_months = [m for m in sorted_month_names if m in heatmap_pivot.columns]
                if available_months:
                    heatmap_pivot = heatmap_pivot[available_months].reindex(top_incident_labels).dropna(
                        how='all').fillna(0)
                    if not heatmap_pivot.empty:
                        fig_heatmap = px.imshow(heatmap_pivot, labels=dict(x="เดือน", y="อุบัติการณ์", color="จำนวน"),
                                                text_auto=True, aspect="auto", color_continuous_scale='Reds')
                        fig_heatmap.update_layout(title_text=f"Top {top_n}",
                                                  height=max(600, len(heatmap_pivot.index) * 25));
                        fig_heatmap.update_xaxes(side="top")
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                    else:
                        st.info("ไม่มีข้อมูล Heatmap")
                else:
                    st.info("ไม่มีข้อมูลรายเดือน")

            except Exception as e:
                    st.error(f"สร้าง Heatmap ผิดพลาด: {e}")
            st.markdown("---")
            st.markdown("<h5 style='color: #003366;'>Heatmap แยกตาม Safety Goal</h5>", unsafe_allow_html=True)
            goal_search_terms = {"Patient Safety/...": "Patient Safety", "Specific Clinical": "Specific Clinical", "Personnel Safety": "Personnel Safety", "Organization Safety": "Organization Safety"}
            for display_name, search_term in goal_search_terms.items():
                df_goal_filtered = df_heat[df_heat['หมวด'].astype(str).str.contains(search_term, na=False, case=False)].copy()
                if df_goal_filtered.empty:
                    st.markdown(f"**{display_name}**: ไม่พบข้อมูล"); st.markdown("---"); continue
                try:
                    goal_pivot = pd.pivot_table(df_goal_filtered, values='Incident', index='incident_label', columns='เดือน', aggfunc='count', fill_value=0)
                    if not goal_pivot.empty:
                        sorted_month_names = [v for k, v in sorted(month_label.items())]
                        available_months_goal = [m for m in sorted_month_names if m in goal_pivot.columns]
                        if available_months_goal:
                            goal_pivot = goal_pivot[available_months_goal]
                            incident_counts_in_goal = df_goal_filtered['incident_label'].value_counts()
                            goal_pivot = goal_pivot.reindex(incident_counts_in_goal.index).dropna(how='all').fillna(0)
                            if not goal_pivot.empty:
                                fig_goal = px.imshow(goal_pivot, labels=dict(x="เดือน", y="อุบัติการณ์", color="จำนวน"), text_auto=True, aspect="auto", color_continuous_scale='Oranges')
                                fig_goal.update_layout(title_text=f"<b>{display_name}</b>", height=max(500, len(goal_pivot.index)*28)); fig_goal.update_xaxes(side="top")
                                st.plotly_chart(fig_goal, use_container_width=True)
                            else:
                                st.info(f"ไม่มีข้อมูล Pivot '{display_name}'")
                        else:
                            st.info(f"ไม่มีข้อมูลรายเดือน '{display_name}'")
                    else:
                        st.info(f"ไม่มีข้อมูล Pivot '{display_name}'")
                    st.markdown("---")
                except Exception as e:
                    st.error(f"สร้าง Heatmap '{display_name}' ผิดพลาด: {e}")

elif selected_page == "Sentinel Events & Top 10":
    st.markdown("<h4 style='color: #001f3f;'>รายการ Sentinel Events</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    elif 'Sentinel code for check' in filtered.columns:
        sentinel_events = filtered[filtered['Sentinel code for check'].isin(sentinel_composite_keys)].copy()
        if not sentinel_events.empty:
            if 'Sentinel2024_df' in globals() and not Sentinel2024_df.empty and 'ชื่ออุบัติการณ์ความเสี่ยง' in Sentinel2024_df.columns:
                try:
                    sentinel_events = pd.merge(sentinel_events, Sentinel2024_df[['รหัส', 'Impact', 'ชื่ออุบัติการณ์ความเสี่ยง']].rename(columns={'ชื่ออุบัติการณ์ความเสี่ยง': 'Sentinel Event Name'}), on=['รหัส', 'Impact'], how='left')
                    if 'Sentinel Event Name' not in display_cols_common: display_cols_common.insert(2, 'Sentinel Event Name')
                except Exception as e:
                    st.warning(f"Merge Sentinel name failed: {e}")
            cols_to_show_sentinel = [col for col in display_cols_common if col in sentinel_events.columns]
            date_format_config = {"Occurrence Date": st.column_config.DatetimeColumn("วันที่เกิด", format="DD/MM/YYYY HH:mm")}
            st.dataframe(sentinel_events[cols_to_show_sentinel], use_container_width=True, hide_index=True, column_config=date_format_config)
        else:
            st.info("ไม่พบ Sentinel Events")
    else:
        st.warning("ตรวจสอบ Sentinel ไม่ได้")

    st.markdown("---")
    st.subheader("Top 10 อุบัติการณ์ (ตามความถี่)")
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        df_freq_filt = filtered['Incident'].value_counts().reset_index(); df_freq_filt.columns = ['Incident', 'count']
        if not df_freq_filt.empty:
            top10_df = df_freq_filt.nlargest(10, 'count')
            incident_names_filt = filtered[['Incident', 'ชื่ออุบัติการณ์ความเสี่ยง']].drop_duplicates()
            top10_df = pd.merge(top10_df, incident_names_filt, on='Incident', how='left')
            st.dataframe(top10_df[['Incident', 'ชื่ออุบัติการณ์ความเสี่ยง', 'count']], hide_index=True, use_container_width=True, column_config={"Incident": "รหัส", "count":"จำนวน"})
        else:
            st.warning("แสดง Top 10 ไม่ได้")

elif selected_page == "สรุปอุบัติการณ์ตาม Safety Goals":
    st.markdown("<h4 style='color: #001f3f;'>สรุปอุบัติการณ์ตาม Safety Goals</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        # --- Part 1: Summary Tables ---
        for display_name, cat_name in goal_definitions.items():
            st.subheader(display_name)
            try:
                summary_table = create_goal_summary_table(
                    data_df_goal=filtered,
                    goal_category_name_param=cat_name
                )
                if summary_table is not None and not summary_table.empty:
                    st.dataframe(summary_table, use_container_width=True, hide_index=True)
                else:
                    st.info(f"ไม่พบข้อมูลสำหรับ {display_name}")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการสร้างตาราง {display_name}: {e}")

        # จุดสำหรับเพิ่มกราฟ/ sunburst ภายหลัง (ปัจจุบันตัดออกเพื่อความเสถียร)

elif selected_page == "Persistence Risk Index":
    st.markdown("<h4 style='color: #001f3f;'>ดัชนีความเสี่ยงเรื้อรัง</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        st.info("ตารางนี้ให้คะแนนอุบัติการณ์ที่เกิดซ้ำ โดยรวมความถี่และความรุนแรงเฉลี่ย")
        min_date_filt = filtered['Occurrence Date'].min(); max_date_filt = filtered['Occurrence Date'].max()
        total_month_filt = 0
        if pd.notna(min_date_filt) and pd.notna(max_date_filt):
            max_p_filt = max_date_filt.to_period('M'); min_p_filt = min_date_filt.to_period('M')
            total_month_filt = max(1, (max_p_filt.year - min_p_filt.year) * 12 + (max_p_filt.month - min_p_filt.month) + 1)

        persistence_df = calculate_persistence_risk_score(filtered, total_month_filt)
        if not persistence_df.empty:
            display_df_persistence = persistence_df.rename(columns={
                'รหัส': 'Incident Code',
                'ชื่ออุบัติการณ์ความเสี่ยง': 'Incident Name',
                'Average_Ordinal_Risk_Score': 'Avg Ordinal Risk',
                'Total_Occurrences': 'Total',
                'Incident_Rate_Per_Month': 'Rate/Month',
                'Persistence_Risk_Score': 'Persistence Score'
            })
            st.dataframe(display_df_persistence[['Incident Code','Incident Name','Total','Avg Ordinal Risk','Rate/Month','Persistence Score']],
                         use_container_width=True, hide_index=True)
            st.markdown("---"); st.markdown("##### กราฟวิเคราะห์")
            fig = px.scatter(persistence_df,
                             x='Incident_Rate_Per_Month', y='Average_Ordinal_Risk_Score',
                             size='Total_Occurrences', hover_name='รหัส',
                             color='Persistence_Risk_Score',
                             labels={'Incident_Rate_Per_Month':'อุบัติการณ์/เดือน', 'Average_Ordinal_Risk_Score':'ความรุนแรงเฉลี่ย (ordinal)'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("ไม่มีข้อมูลเพียงพอสำหรับคำนวณ Persistence Risk")

elif selected_page == "Early Warning: อุบัติการณ์ที่มีแนวโน้มสูงขึ้น":
    st.markdown("<h4 style='color:#001f3f;'>Early Warning</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: horizon = st.slider("ช่วงคาดการณ์ (เดือน)", 1, 12, 3)
        with c2: w1 = st.slider("น้ำหนักความถี่", 0.0, 1.0, 0.34)
        with c3: w2 = st.slider("น้ำหนักความรุนแรง", 0.0, 1.0, 0.33)
        w3 = max(0.0, 1.0 - (w1 + w2))
        st.caption(f"น้ำหนักแนวโน้ม = {w3:.2f}")
        try:
            res = prioritize_incidents_nb_logit_v2(_df=filtered, horizon=horizon, w_freq=w1, w_sev=w2, w_trend=w3)
        except Exception as e:
            st.error(f"คำนวณผิดพลาด: {e}")
            res = pd.DataFrame()
        if res.empty:
            st.info("ไม่มีข้อมูลเพียงพอสำหรับ Early Warning")
        else:
            st.dataframe(res.rename(columns={'รหัส':'Incident Code','ชื่ออุบัติการณ์ความเสี่ยง':'Incident Name','total':'Total','avg_risk':'Avg Risk','score':'Priority Score'}),
                         use_container_width=True, hide_index=True)

elif selected_page == "บทสรุปสำหรับผู้บริหาร":
    st.markdown("<h4 style='color: #001f3f;'>บทสรุปสำหรับผู้บริหาร</h4>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("ไม่มีข้อมูลตามตัวกรอง")
    else:
        # --- START: Dependency Injection (คำนวณค่าที่จำเป็นก่อน) ---
        # 1. คำนวณช่วงเวลา
        min_date_filt = filtered['Occurrence Date'].min();
        max_date_filt = filtered['Occurrence Date'].max()
        min_date_str = min_date_filt.strftime('%d/%m/%Y') if pd.notna(min_date_filt) else "N/A"
        max_date_str = max_date_filt.strftime('%d/%m/%Y') if pd.notna(max_date_filt) else "N/A"
        total_month = 0
        if pd.notna(min_date_filt) and pd.notna(max_date_filt):
            max_p_filt = max_date_filt.to_period('M');
            min_p_filt = min_date_filt.to_period('M')
            total_month = max(1, (max_p_filt.year - min_p_filt.year) * 12 + (max_p_filt.month - min_p_filt.month) + 1)

        # 2. คำนวณ Metrics (ดึงมาจากหน้า Dashboard)
        metrics_data = {}
        metrics_data['total_processed_incidents'] = filtered.shape[0]
        metrics_data['total_psg9_incidents_for_metric1'] = \
        filtered[filtered['รหัส'].isin(psg9_r_codes_for_counting)].shape[0] if psg9_r_codes_for_counting else 0
        metrics_data['total_sentinel_incidents_for_metric1'] = \
        filtered[filtered['Sentinel code for check'].isin(sentinel_composite_keys)].shape[
            0] if 'Sentinel code for check' in filtered.columns and sentinel_composite_keys else 0

        severe_impact_levels_list = ['3', '4', '5']
        df_severe_filt = filtered[filtered['Impact Level'].isin(severe_impact_levels_list)].copy()
        metrics_data['total_severe_incidents'] = df_severe_filt.shape[0]

        if 'Resulting Actions' in filtered.columns:
            unresolved_filt = df_severe_filt[df_severe_filt['Resulting Actions'].astype(str).isin(['None', '', 'nan'])]
            metrics_data['total_severe_unresolved_incidents_val'] = unresolved_filt.shape[0]
        else:
            metrics_data['total_severe_unresolved_incidents_val'] = "N/A"

        # 3. คำนวณ Top 10 (ดึงมาจากหน้า Sentinel)
        df_freq = filtered['Incident'].value_counts().reset_index()
        df_freq.columns = ['Incident', 'count']
        # --- END: Dependency Injection ---

        st.markdown(f"**เรื่อง:** รายงานสรุปอุบัติการณ์โรงพยาบาล")
        st.markdown(f"**ช่วงข้อมูลที่วิเคราะห์:** {min_date_str} ถึง {max_date_str} (รวม {total_month} เดือน)")
        st.markdown(f"**จำนวนอุบัติการณ์ที่พบทั้งหมด:** {metrics_data.get('total_processed_incidents', 0):,} รายการ")
        st.markdown("---")

        # --- 1. แดชบอร์ดสรุปภาพรวม ---
        st.subheader("1. แดชบอร์ดสรุปภาพรวม")
        col1_m, col2_m, col3_m, col4_m, col5_m = st.columns(5)
        with col1_m:
            st.metric("อุบัติการณ์ทั้งหมด", f"{metrics_data.get('total_processed_incidents', 0):,}")
        with col2_m:
            st.metric("Sentinel Events", f"{metrics_data.get('total_sentinel_incidents_for_metric1', 0):,}")
        with col3_m:
            st.metric("มาตรฐานสำคัญฯ 9 ข้อ", f"{metrics_data.get('total_psg9_incidents_for_metric1', 0):,}")
        with col4_m:
            st.metric("ความรุนแรงสูง (E-I & 3-5)", f"{metrics_data.get('total_severe_incidents', 0):,}")
        with col5_m:
            val_unresolved = metrics_data.get('total_severe_unresolved_incidents_val', 'N/A')
            st.metric("รุนแรงสูง & ยังไม่แก้ไข",
                      f"{val_unresolved:,}" if isinstance(val_unresolved, int) else val_unresolved)
        st.markdown("---")

        # --- 2. Risk Matrix และ Top 10 อุบัติการณ์ ---
        st.subheader("2. Risk Matrix และ Top 10 อุบัติการณ์")
        col_matrix, col_top10 = st.columns(2)
        with col_matrix:
            st.markdown("##### Risk Matrix")
            impact_level_keys = ['5', '4', '3', '2', '1']
            freq_level_keys = ['1', '2', '3', '4', '5']
            matrix_df = filtered[
                filtered['Impact Level'].isin(impact_level_keys) & filtered['Frequency Level'].isin(
                    freq_level_keys)]
            if not matrix_df.empty:
                matrix_data = pd.crosstab(matrix_df['Impact Level'], matrix_df['Frequency Level'])
                matrix_data = matrix_data.reindex(index=impact_level_keys, columns=freq_level_keys, fill_value=0)
                impact_labels = {'5': "5 (Extreme)", '4': "4 (Major)", '3': "3 (Moderate)", '2': "2 (Minor)",
                                 '1': "1 (Insignificant)"}
                freq_labels = {'1': "F1", '2': "F2", '3': "F3", '4': "F4", '5': "F5"}
                st.table(matrix_data.rename(index=impact_labels, columns=freq_labels))
            else:
                st.info("ไม่มีข้อมูลสำหรับ Risk Matrix")
        with col_top10:
            st.markdown("##### Top 10 อุบัติการณ์ (ตามความถี่)")
            if not df_freq.empty:
                df_freq_top10 = df_freq.nlargest(10, 'count').copy()
                display_top10 = pd.merge(df_freq_top10,
                                         filtered[['Incident', 'ชื่ออุบัติการณ์ความเสี่ยง']].drop_duplicates(),
                                         on='Incident', how='left')
                # แสดงแค่ รหัส และ จำนวน (ตามโค้ดเดิม)
                st.dataframe(display_top10[['Incident', 'count']], hide_index=True,
                             use_container_width=True,
                             column_config={"Incident": "รหัส",
                                            "count": "จำนวน"})
            else:
                st.info("ไม่มีข้อมูล Top 10")
        st.markdown("---")

        # --- 3. รายการ Sentinel Events ---
        st.subheader("3. รายการ Sentinel Events")
        if 'Sentinel code for check' in filtered.columns:
            sentinel_events_df = filtered[filtered['Sentinel code for check'].isin(sentinel_composite_keys)]
            if not sentinel_events_df.empty:
                st.dataframe(
                    sentinel_events_df[['Occurrence Date', 'Incident', 'Impact', 'รายละเอียดการเกิด_Anonymized']],
                    hide_index=True, use_container_width=True,
                    column_config={"Occurrence Date": "วันที่เกิด", "Incident": "รหัส", "Impact": "ระดับ",
                                   "รายละเอียดการเกิด_Anonymized": "รายละเอียด"})
            else:
                st.info("ไม่พบ Sentinel Events ในช่วงเวลาที่เลือก")
        else:
            st.warning("ตรวจสอบ Sentinel ไม่ได้")
        st.markdown("---")

        # --- 4. PSG9 Summary ---
        st.subheader("4. วิเคราะห์ตามหมวดหมู่ มาตรฐานสำคัญจำเป็นต่อความปลอดภัย 9 ข้อ")
        # (เรียกใช้ฟังก์ชัน Helper ที่เราซ่อมไปแล้ว)
        psg9_summary_table = create_psg9_summary_table(filtered)
        if psg9_summary_table is not None and not psg9_summary_table.empty:
            st.table(psg9_summary_table)
        else:
            st.info("ไม่พบข้อมูลอุบัติการณ์ที่เกี่ยวข้องกับ PSG9 ในช่วงเวลานี้")
        st.markdown("---")

        # --- 5. รายการอุบัติการณ์รุนแรงที่ยังไม่ถูกแก้ไข ---
        st.subheader("5. รายการอุบัติการณ์รุนแรง (E-I & 3-5) ที่ยังไม่ถูกแก้ไข")
        if 'Resulting Actions' in filtered.columns:
            unresolved_severe_df = filtered[
                filtered['Impact Level'].isin(['3', '4', '5']) &
                filtered['Resulting Actions'].astype(str).isin(['None', '', 'nan'])
                ]
            if not unresolved_severe_df.empty:
                display_cols_unresolved = ['Occurrence Date', 'Incident', 'Impact', 'รายละเอียดการเกิด_Anonymized']
                st.dataframe(
                    unresolved_severe_df[display_cols_unresolved],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Occurrence Date": st.column_config.DatetimeColumn(
                            "วันที่เกิด",
                            format="DD/MM/YYYY",
                        ),
                        "Incident": "รหัส",
                        "Impact": "ระดับ",
                        "รายละเอียดการเกิด_Anonymized": "รายละเอียด"
                    }
                )
            else:
                st.info("ไม่พบอุบัติการณ์รุนแรงที่ยังไม่ถูกแก้ไขในช่วงเวลานี้")
        st.markdown("---")

        # --- 6. สรุปอุบัติการณ์ตามเป้าหมาย Safety Goals ---
        st.subheader("6. สรุปอุบัติการณ์ตามเป้าหมาย Safety Goals")
        # (goal_definitions ถูกนิยามไว้ใน Section 5)
        for display_name, cat_name in goal_definitions.items():
            st.markdown(f"##### {display_name}")

            # --- ปรับแก้ ---
            # เรียกใช้ฟังก์ชันเวอร์ชัน "ง่าย" ที่เรามีใน Section 7
            # โดยตัดพารามิเตอร์ที่ไม่มีในฟังก์ชัน (e_up..., is_org_safety) ทิ้งไป
            summary_table = create_goal_summary_table(filtered, cat_name)

            if summary_table is not None and not summary_table.empty:
                # ใช้ st.dataframe แทน st.table เพื่อให้รองรับตารางยาวๆ ได้ดีกว่า
                st.dataframe(summary_table, use_container_width=True, hide_index=True)
            else:
                st.info(f"ไม่มีข้อมูลสำหรับ '{display_name}'")
        st.markdown("---")

        # --- 7. Early Warning (Top 5) ---
        st.subheader("7. Early Warning: อุบัติการณ์ที่มีแนวโน้มสูงขึ้น (Top 5)")
        st.write(
            "แสดง Top 5 อุบัติการณ์ที่ถูกจัดลำดับความสำคัญสูงสุด โดยพิจารณาจากความถี่และความรุนแรงเฉลี่ย")

        # --- ปรับแก้ ---
        # เรียกใช้ฟังก์ชันเวอร์ชัน "ง่าย" (stub) ที่เรามีใน Section 7
        # โดยตัดพารามิเตอร์ที่ไม่มี (min_months, min_total) ทิ้ง
        early_warning_df = prioritize_incidents_nb_logit_v2(filtered, horizon=3)

        if not early_warning_df.empty:
            top_ew_incidents = early_warning_df.head(5).copy()

            # ปรับแก้คอลัมน์ที่แสดงผล ให้ตรงกับผลลัพธ์จากฟังก์ชันเวอร์ชัน "ง่าย"
            display_ew_df = top_ew_incidents.rename(
                columns={'ชื่ออุบัติการณ์ความเสี่ยง': 'ชื่ออุบัติการณ์',
                         'score': 'คะแนนความสำคัญ'})

            # ตัดคอลัมน์ 'คาดการณ์เหตุรุนแรง (3 ด.)' ที่ไม่มีในเวอร์ชันง่ายทิ้งไป
            st.dataframe(
                display_ew_df[['รหัส', 'ชื่ออุบัติการณ์', 'คะแนนความสำคัญ']],
                column_config={
                    "คะแนนความสำคัญ": st.column_config.ProgressColumn("คะแนนความสำคัญ", format="%.3f", min_value=0,
                                                                      max_value=float(
                                                                          display_ew_df['คะแนนความสำคัญ'].max())),
                },
                use_container_width=True, hide_index=True
            )
        else:
            st.info("ไม่มีข้อมูลเพียงพอสำหรับวิเคราะห์ Early Warning")
        st.markdown("---")

        # --- 8. สรุปอุบัติการณ์ที่เป็นปัญหาเรื้อรัง (Top 5) ---
        st.subheader("8. สรุปอุบัติการณ์ที่เป็นปัญหาเรื้อรัง (Persistence Risk - Top 5)")
        st.write("แสดง Top 5 อุบัติการณ์ที่เกิดขึ้นบ่อยและมีความรุนแรงเฉลี่ยสูง ซึ่งควรทบทวนเชิงระบบ")
        persistence_df_exec = calculate_persistence_risk_score(filtered, total_month)
        if not persistence_df_exec.empty:
            top_persistence_incidents = persistence_df_exec.head(5)
            display_df_persistence = top_persistence_incidents.rename(
                columns={'Persistence_Risk_Score': 'ดัชนีความเรื้อรัง',
                         'Average_Ordinal_Risk_Score': 'คะแนนเสี่ยงเฉลี่ย'})
            st.dataframe(
                display_df_persistence[['รหัส', 'ชื่ออุบัติการณ์ความเสี่ยง', 'คะแนนเสี่ยงเฉลี่ย', 'ดัชนีความเรื้อรัง']],
                column_config={
                    "คะแนนเสี่ยงเฉลี่ย": st.column_config.NumberColumn(format="%.2f"),
                    "ดัชนีความเรื้อรัง": st.column_config.ProgressColumn("ดัชนีความเรื้อรัง", min_value=0, max_value=2,
                                                                         format="%.2f")
                },
                use_container_width=True,
                hide_index=True  # เพิ่ม hide_index
            )
        else:
            st.info("ไม่มีข้อมูลเพียงพอสำหรับวิเคราะห์ความเสี่ยงเรื้อรัง")

# =========================
# 9) Download ผลลัพธ์ (Main Area, uses 'filtered')
# =========================
@st.cache_data
def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    cols_for_download = [
        'เลขที่รับ', 'หน่วยงาน', 'วัน-เวลา ที่รายงาน', 'สถานที่เกิดเหตุ',
        'Occurrence Date', 'Incident', 'ชื่ออุบัติการณ์ความเสี่ยง', 'Impact', 'Impact Level',
        'Frequency Level', 'Risk Level', 'Category Color', 'กลุ่มงาน', 'หมวด',
        'รายละเอียดการเกิด', 'Resulting Actions', 'หน่วยงาน_norm',
        'FY_int', 'FQuarter', 'FY_Quarter',
        'รหัส',
    ]
    cols_present_for_download = [c for c in cols_for_download if c in df.columns]
    try:
        return df[cols_present_for_download].to_csv(index=False).encode("utf-8-sig")
    except Exception as e:
        st.error(f"Error creating CSV for download: {e}")
        return b""

if not filtered.empty:
    st.markdown("---")
    st.download_button(
        "ดาวน์โหลดผลลัพธ์ที่กรองแล้ว (CSV)",
        data=_to_csv_bytes(filtered),
        file_name="filtered_result.csv",
        mime="text/csv"
    )
