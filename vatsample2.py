# app.py
import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="폐업 시 고정자산 잔존가치 계산기", layout="centered")

st.title("폐업 시 고정자산 잔존가치 계산기 (부가가치세법 가정)")
st.caption("초보자용 · Streamlit 데모 | 경과 과세기간: 구입 과세기간과 폐업 과세기간을 포함(기본)하여 계산")

# -----------------------------
# 유틸 함수
# -----------------------------
def period_to_index(year: int, half: str) -> int:
    """상반기=0, 하반기=1 로 하여 연-반기를 단일 인덱스로 변환"""
    half_idx = 0 if half == "상반기" else 1
    return year * 2 + half_idx

def calc_elapsed(purchase_idx: int, close_idx: int, include_purchase: bool = True) -> int:
    if close_idx < purchase_idx:
        raise ValueError("폐업 과세기간이 구입 과세기간보다 앞설 수 없습니다.")
    base = close_idx - purchase_idx
    return base + (1 if include_purchase else 0)

def format_currency(v: float) -> str:
    return f"{v:,.0f}"

# -----------------------------
# 입력 UI
# -----------------------------
st.subheader("1) 과세기간 선택")

years = list(range(2000, 2051))
half_options = ["상반기", "하반기"]

c1, c2 = st.columns(2)
with c1:
    buy_year = st.selectbox("구입 연도", years, index=years.index(2025) if 2025 in years else 0)
    buy_half = st.radio("구입 과세기간", half_options, horizontal=True, key="buy_half")
with c2:
    close_year = st.selectbox("폐업 연도", years, index=years.index(2025) if 2025 in years else 0)
    close_half = st.radio("폐업 과세기간", half_options, horizontal=True, key="close_half")

include_purchase = st.checkbox("구입 과세기간을 경과기간에 포함", value=True,
                               help="체크 시 구입 과세기간과 폐업 과세기간을 모두 포함하여 경과 과세기간을 계산합니다.")

st.divider()

st.subheader("2) 자산 구분 및 매입가액")
asset_type = st.radio(
    "자산 종류",
    ["1. 건물·구축물 등 고정자산", "2. 그 외 자산"],
    help="감가율: 건물·고정자산 5%/과세기간, 그 외 자산 25%/과세기간",
)
price = st.number_input("매입가액(원)", min_value=0.0, step=1000.0, format="%.0f")

# 자산별 감가율
rate = 0.05 if asset_type.startswith("1.") else 0.25
rate_label = "5%" if rate == 0.05 else "25%"

# -----------------------------
# 계산
# -----------------------------
if st.button("계산하기", type="primary"):
    try:
        p_idx = period_to_index(buy_year, buy_half)
        c_idx = period_to_index(close_year, close_half)
        elapsed = calc_elapsed(p_idx, c_idx, include_purchase=include_purchase)

        # 이론상 최대 차감 가능한 과세기간(정액, 원금의 100% 한도)
        max_periods = math.ceil(1.0 / rate)  # 5%->20, 25%->4
        used_periods = min(elapsed, max_periods)

        total_depr = price * rate * used_periods
        residual = max(0.0, price - total_depr)

        # 결과 표시
        st.success("계산 완료")

        st.markdown("### 결과 요약")
        colA, colB = st.columns(2)
        with colA:
            st.metric("경과 과세기간(회)", value=f"{elapsed:,}")
            st.metric("적용 감가율/과세기간", value=rate_label)
        with colB:
            st.metric("총 감가상각액(원)", value=format_currency(total_depr))
            st.metric("잔존가액(원)", value=format_currency(residual))

        with st.expander("상세 보기 (기간별 누적 감가상각 표)"):
            rows = []
            remaining = price
            for i in range(1, elapsed + 1):
                # 정액: 매 기간 감가액 = price * rate, 다만 잔액이 부족하면 0까지
                depreciation = min(remaining, price * rate)
                remaining = max(0.0, remaining - depreciation)
                rows.append({
                    "회차(과세기간)": i,
                    "당기 감가상각액": depreciation,
                    "누적 감가상각액": price - remaining,
                    "기말 잔존가액": remaining
                })
            df = pd.DataFrame(rows)
            df["당기 감가상각액"] = df["당기 감가상각액"].round(0)
            df["누적 감가상각액"] = df["누적 감가상각액"].round(0)
            df["기말 잔존가액"] = df["기말 잔존가액"].round(0)
            st.dataframe(df, use_container_width=True)

        st.info(
            "참고: 본 계산기는 사용자 제공 규칙(정액 감가: 건물/고정자산 5%, 그 외 25%)에 따라 "
            "구입 과세기간부터 폐업 과세기간까지(기본 설정) 감가 후 잔존가액을 단순 계산합니다. "
            "세법상 특례나 실제 신고 시 해석 차이는 별도 검토가 필요할 수 있습니다."
        )

    except ValueError as e:
        st.error(str(e))
