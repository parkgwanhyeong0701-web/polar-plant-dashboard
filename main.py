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

PLOTLY_FONT = dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")

# =========================
# 유틸 함수
# =========================
def normalize_text(text):
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
    data_dir = Path("data")
    if not data_dir.exists():
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
            file_path = find_file_by_name(data_dir, fname)
            if file_path is None:
                st.error(f"{fname} 파일을 찾을 수 없습니다.")
                continue

            school = fname.split("_")[0]
            df = pd.read_csv(file_path)
            env_data[school] = df

    return env_data

@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    xlsx_path = None

    for f in data_dir.iterdir():
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
            df = pd.read_excel(xls, sheet_name=sheet)
            growth_data[sheet] = df

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

SCHOOL_COLORS = {
    "송도고": "#1f77b4",
    "하늘고": "#2ca02c",
    "아라고": "#ff7f0e",
    "동산고": "#d62728",
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
# Tab 1 : 실험 개요
# =========================
with tab1:
    st.subheader("연구 배경 및 목적")
    st.write(
        "본 연구는 서로 다른 EC 농도 조건에서 극지식물의 생육 차이를 비교 분석하여 "
        "최적의 EC 농도를 도출하는 것을 목표로 한다."
    )

    summary_rows = []
    total_plants = 0

    for school, df in growth_data.items():
        count = len(df)
        total_plants += count
        summary_rows.append([
            school,
            EC_INFO.get(school, None),
            count,
            SCHOOL_COLORS.get(school, "#000000")
        ])

    summary_df = pd.DataFrame(
        summary_rows,
        columns=["학교명", "EC 목표", "개체수", "색상"]
    )

    st.table(summary_df)

    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 개체수", total_plants)
    col2.metric("평균 온도", f"{avg_temp:.2f} ℃")
    col3.metric("평균 습도", f"{avg_hum:.2f} %")
    col4.metric("최적 EC", "2.0 (하늘고)")

# =========================
# Tab 2 : 환경 데이터
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

    st.subheader("학교별 시계열 데이터")
    for school in selected_schools:
        df = env_data[school]
        fig_ts = px.line(df, x="time", y=["temperature", "humidity", "ec"])
        fig_ts.add_hline(y=EC_INFO.get(school), line_dash="dash", annotation_text="목표 EC")
        fig_ts.update_layout(title=school, font=PLOTLY_FONT)
        st.plotly_chart(fig_ts, use_container_width=True)

    with st.expander("환경 데이터 원본"):
        for school, df in env_data.items():
            st.write(school)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                f"{school} CSV 다운로드",
                csv,
                file_name=f"{school}_환경데이터.csv",
                mime="text/csv"
            )

# =========================
# Tab 3 : 생육 결과
# =========================
with tab3:
    st.subheader("EC별 평균 생중량")

    weight_rows = []
    for school, df in growth_data.items():
        weight_rows.append([
            school,
            EC_INFO.get(school),
            df["생중량(g)"].mean()
        ])

    weight_df = pd.DataFrame(weight_rows, columns=["학교", "EC", "평균 생중량"])

    best_row = weight_df.loc[weight_df["평균 생중량"].idxmax()]
    st.metric("🥇 최적 EC 평균 생중량", f"{best_row['평균 생중량']:.2f} g", f"EC {best_row['EC']}")

    metrics = [
        ("생중량(g)", "평균 생중량"),
        ("잎 수(장)", "평균 잎 수"),
        ("지상부 길이(mm)", "평균 지상부 길이"),
    ]

    fig = make_subplots(rows=2, cols=2, subplot_titles=[m[1] for m in metrics] + ["개체수"])

    for i, (col, title) in enumerate(metrics):
        values = []
        for school, df in growth_data.items():
            values.append(df[col].mean())
        fig.add_bar(x=list(growth_data.keys()), y=values, row=i//2+1, col=i%2+1)

    counts = [len(df) for df in growth_data.values()]
    fig.add_bar(x=list(growth_data.keys()), y=counts, row=2, col=2)

    fig.update_layout(font=PLOTLY_FONT, height=700)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("학교별 생중량 분포")
    all_growth = pd.concat(
        [df.assign(학교=school) for school, df in growth_data.items()]
    )
    fig_box = px.box(all_growth, x="학교", y="생중량(g)")
    fig_box.update_layout(font=PLOTLY_FONT)
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("상관관계 분석")
    col1, col2 = st.columns(2)
    with col1:
        fig_sc1 = px.scatter(all_growth, x="잎 수(장)", y="생중량(g)", color="학교")
        fig_sc1.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig_sc1, use_container_width=True)
    with col2:
        fig_sc2 = px.scatter(all_growth, x="지상부 길이(mm)", y="생중량(g)", color="학교")
        fig_sc2.update_layout(font=PLOTLY_FONT)
        st.plotly_chart(fig_sc2, use_container_width=True)

    with st.expander("생육 데이터 원본 다운로드"):
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
