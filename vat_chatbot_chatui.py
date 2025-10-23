# -*- coding: utf-8 -*-
"""
🤖 부가가치세 차량공제 챗봇 (Chat UI) — 차량명 유지/표시 버전
변경점:
- 사이드바에 '현재 입력값' 패널 추가 (업종/차량/인원 항상 표시)
- 차량 입력 직후, 봇이 차량명을 다시 언급하여 승합차 인원 질문
- 최신 Streamlit 호환: st.rerun 사용
"""

import streamlit as st

# ---------------------------------------------
# 데이터 정의
# ---------------------------------------------
DEDUCTIBLE_INDUSTRIES = ["택시", "자동차학원", "자동차임대업"]
TAX_FREE_TYPES = ["경차", "화물", "승합"]

# ---------------------------------------------
# Streamlit 설정
# ---------------------------------------------
st.set_page_config(page_title="부가가치세 차량공제 챗봇", page_icon="🤖")
st.title("🤖 부가가치세 차량공제 챗봇")
st.caption("대화형으로 업종과 차량 정보를 입력하면 공제 여부를 안내합니다.")

# ---------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "industry" not in st.session_state:
    st.session_state.industry = ""
if "vehicle" not in st.session_state:
    st.session_state.vehicle = ""
if "passenger_count" not in st.session_state:
    st.session_state.passenger_count = None

# ---------------------------------------------
# 사이드바: 현재 입력값 요약 (항상 표시)
# ---------------------------------------------
with st.sidebar:
    st.header("🧾 현재 입력값")
    st.write(f"**업종:** {st.session_state.industry or '—'}")
    st.write(f"**차량:** {st.session_state.vehicle or '—'}")
    st.write(f"**승합 인원:** {st.session_state.passenger_count if st.session_state.passenger_count is not None else '—'}")
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        st.session_state.step = 0
        st.session_state.industry = ""
        st.session_state.vehicle = ""
        st.session_state.passenger_count = None
        st.rerun()

# ---------------------------------------------
# 기존 메시지 표시
# ---------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------
# 대화 유틸
# ---------------------------------------------
def bot_say(message: str):
    with st.chat_message("assistant"):
        st.markdown(message)
    st.session_state.messages.append({"role": "assistant", "content": message})

def user_say(message: str):
    st.session_state.messages.append({"role": "user", "content": message})

# ---------------------------------------------
# 최초 인사 & 업종 질문
# ---------------------------------------------
if st.session_state.step == 0:
    bot_say("안녕하세요! 😊 차량 관련 부가가치세 매입세액 공제 여부를 도와드릴게요.\n\n어떤 **업종**에 종사하시나요?")
    st.session_state.step = 1

# ---------------------------------------------
# 입력창
# ---------------------------------------------
if prompt := st.chat_input("메시지를 입력하세요..."):
    user_say(prompt)

    # Step 1️⃣: 업종 입력
    if st.session_state.step == 1:
        industry = prompt.strip()
        st.session_state.industry = industry

        if any(word in industry for word in DEDUCTIBLE_INDUSTRIES):
            bot_say("✅ 차량 관련 비용 부가가치세 매입공제 **공제가능합니다.**\n\n(택시·자동차학원·자동차임대업 등은 차량을 직접 사용하므로 공제대상입니다.)")
            st.session_state.step = 999
        else:
            bot_say("알겠습니다. 업종에 따라 직접 공제는 불가하네요.\n이제 **차량명**을 알려주세요. (예: 소나타, 스타렉스 9인승, 봉고 화물 등)")
            st.session_state.step = 2

    # Step 2️⃣: 차량 입력
    elif st.session_state.step == 2:
        vehicle = prompt.strip()
        st.session_state.vehicle = vehicle  # ✅ 세션에 보존 → 사이드바에 항상 표시

        if "승합" in vehicle:
            # ✅ 차량명을 다시 언급하면서 인원수 질문 (사용자 체감 '사라지지 않음')
            bot_say(f"입력하신 차량은 **{vehicle}** 이네요.\n몇 인승 차량인가요? 숫자만 입력해주세요 (예: 9)")
            st.session_state.step = 3
        elif any(keyword in vehicle for keyword in ["경차", "화물"]):
            bot_say(f"입력하신 차량은 **{vehicle}** 입니다.\n✅ 경차 또는 화물차이므로 차량 관련 비용 부가가치세 매입공제 **공제가능합니다.**")
            st.session_state.step = 999
        else:
            bot_say(f"입력하신 차량은 **{vehicle}** 입니다.\n❌ 개별소비세 과세 대상 차량이므로 부가가치세 매입세액 **공제 불가능합니다.**\n\n(일반 승용차는 공제 대상이 아닙니다.)")
            st.session_state.step = 999

    # Step 3️⃣: 승합차 인원수 입력
    elif st.session_state.step == 3:
        try:
            count = int(prompt)
            st.session_state.passenger_count = count  # ✅ 세션 보존 → 사이드바 표시
            if count > 8:
                bot_say(f"🚐 {count}인승 승합차는 8인승 초과이므로 ✅ **공제가능합니다.**")
            else:
                bot_say(f"🚐 {count}인승 승합차는 7인승 이하이므로 ❌ **공제불가능합니다.**")
            st.session_state.step = 999
        except ValueError:
            bot_say("숫자로 입력해주세요. (예: 9)")
    else:
        bot_say("대화를 다시 시작하려면 왼쪽 사이드바의 🔄 **대화 초기화** 버튼을 눌러주세요.")

