# 소득(income)과 세금(tax) 변수 선언
income = 55000000  # 연소득 (단위: 원)
tax = 0  # 세금 초기값

# 소득 수준 분류 및 세금 계산
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
print(f"소득 수준: {level}")
print(f"소득 금액: {income:,}원")
print(f"예상 세금: {tax:,.0f}원")
