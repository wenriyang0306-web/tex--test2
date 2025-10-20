import streamlit as st

# 제목
st.title("💰 소득에 따른 세금 계산기")

# 사용자 입력 (연소득)
income = st.number_input("연소득을 입력하세요 (원)", min_value=0, value=55000000, step=1000000)

# 세금 계산
if income >= 100000000:
    level = "고소득자"
    tax = income * 0.3  # 세율 30%
elif income >= 50000000:
    level = "중간소득자"
    tax = income * 0.2  # 세율 20%
else:
    level = "저소득자"
    tax = income * 0.1  # 세율 10%

# 결과 출력
st.subheader("📊 계산 결과")
st.write(f"**소득 수준:** {level}")
st.write(f"**소득 금액:** {income:,.0f}원")
st.write(f"**예상 세금:** {tax:,.0f}원")
