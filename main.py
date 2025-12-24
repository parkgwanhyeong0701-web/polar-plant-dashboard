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
    ["전체", "송도고", "하늘고", "아라고", "동산고"]
)

selected_schools = (
    list(env_data.keys()) if school_option == "전체" else [school_option]
)

# =========================
# 제목
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")

tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =========================
# Tab 1
# =========================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.write(
        "본 연구는 서로 다른 EC 농도 조건에서 극지식물의 생육 차이를 비교 분석하여 "
        "최적의 EC 농도를 도출하는 것을 목표로 한다."
    )

    rows = []
    total = 0
    for school, df in growth_data.items():
        rows.append([school, EC_INFO.get(school), len(df)])
        total += len(df)

    st.table(pd.DataFrame(
        rows, columns=["학교명", "EC 목표", "개체수"]
    ))

    if env_data:
        avg_temp = pd.concat(env_data.values())["temperature"].mean()
        avg_hum = pd.concat(env_data.values())["humidity"].mean()
    else:
        avg_temp = avg_hum = 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 개체수", total)
    c2.metric("평균 온도", f"{avg_temp:.2f} ℃")
    c3.metric("평균 습도", f"{avg_hum:.2f} %")
    c4.metric("최적 EC", "2.0 (하늘고)")

# =========================
# Tab 2
# =========================
with tab2:
    st.subheader("학교별 환경 평균 비교")

    avg_rows = []
    for school in selected_schools:
        df = env_data.get(school)
        if df is None:
            continue
        avg_rows.append([
            school,
            df["temperature"].mean(),
            df["humidity"].mean(),
            df["ph"].mean(),
            df["ec"].mean(),
            EC_INFO.get(school)
        ])

    avg_df = pd.DataFrame(
        avg_rows,
        columns=["학교", "온도", "습도", "pH", "실측 EC", "목표 EC"]
    )

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "목표 EC vs 실측 EC"]
    )

    fig.add_bar(x=avg_df["학교"], y=avg_df["온도"], row=1, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["습도"], row=1, col=2)
    fig.add_bar(x=avg_df["학교"], y=avg_df["pH"], row=2, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["실측 EC"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=avg_df["학교"], y=avg_df["목표 EC"], name="목표 EC", row=2, col=2)

    fig.update_layout(font=PLOTLY_FONT, height=600)
    st.plotly_chart(fig, use_container_width=True)

# =========================
# Tab 3
# =========================
with tab3:
    rows = []
    for school, df in growth_data.items():
        rows.append([school, EC_INFO.get(school), df["생중량(g)"].mean()])

    weight_df = pd.DataFrame(
        rows, columns=["학교", "EC", "평균 생중량"]
    )

    best = weight_df.loc[weight_df["평균 생중량"].idxmax()]
    st.metric(
        "🥇 최적 EC 평균 생중량",
        f"{best['평균 생중량']:.2f} g",
        f"EC {best['EC']}"
    )

    with st.expander("생육 데이터 XLSX 다운로드"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for school, df in growth_data.items():
                df.to_excel(writer, sheet_name=school, index=False)
        buffer.seek(0)

        st.download_button(
            "XLSX 다운로드",
            data=buffer,
            file_name="4개교_생육결과데이터.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
