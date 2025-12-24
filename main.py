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

# 한글 폰트 (Streamlit)
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
# 경로 설정 (🔥 중요 수정)
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# =========================
# 유틸 함수
# =========================
def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)

def find_file_by_name(directory: Path, target_name: str):
    target_nfc = normalize_text(target_name)
    for file in directory.iterdir():
        if normalize_text(file.name) == target_nfc:
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

    env_files = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    env_data = {}

    with st.spinner("환경 데이터 로딩 중..."):
        for fname in env_files:
            file_path = find_file_by_name(DATA_DIR, fname)
            if file_path is None:
                st.error(f"{fname} 파일을 찾을 수 없습니다.")
                continue

            school = fname.split("_")[0]
            df = pd.r
