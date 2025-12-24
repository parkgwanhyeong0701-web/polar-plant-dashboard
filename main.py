import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import io

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

# 한글 폰트
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

PLOTLY_FONT = dict(
    family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"
)

# =========================
# 경로 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# =========================
# 유틸 함수 (🔥 핵심 수정)
# =========================
def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def simplify_name(text: str) -> str:
    """공백, 언더바, 하이픈 제거 후 NFC 정규화"""
    text = normalize_text(text)
    return text.replace(" ", "").replace("_", "").replace("-", "")

def find_env_file(directory: Path, school_name: str):
    school_key = simplify_name(school_name)
    for file in directory.iterdir():
        if file.suffix.lower() != ".csv":
            continue
        fname = simplify_name(file.name)
        if school_key in fname:
            return file
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_environment_data():
    if not DATA_DIR.exists():
        st.error("data 폴더를 찾을 수 없습니다.")
        return {}

    schools = ["송도고", "하늘고", "아라고", "동산고"]
    env_data = {}

    with st.spinner("환경 데이터 로딩 중..."):
        for school in schools:
            file_path = find_env_file(DATA_DIR, school)
            if file_path is None:
                st.error(f"{school} 환경데이터 CSV 파일을 찾을 수 없습니다.")
                continue

            df = pd.read_csv(file_path)
            env_data[school] = df

    return env_data

@st.cache_data
def load_growth_data():
    if not DATA_DIR.exists():
        st.error("data 폴더를 찾을 수 없습니다.")
        return {}

    xlsx_path = None
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == ".xlsx":
            xlsx_path = f
            break

    if xlsx_path is None:
        st.error("생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(xlsx_path, engine="openpyxl")
        growth_data = {}
        for sheet in xls.sheet_names:
            growth_data[sheet] = pd.read_excel(xls, sheet_name=sheet)

    return growth_data

env_data = load_environment_data()
growth_data = load_growth_data()

# =========================
# 메타 정보
# =========================
EC_INFO = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# =========================
# 사이드바
# =========================
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체", "송도고", "하늘고", "아라고]()
