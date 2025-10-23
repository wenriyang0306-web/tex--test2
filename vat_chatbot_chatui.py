# -*- coding: utf-8 -*-
"""
🤖 부가가치세 차량공제 챗봇 (Chat UI)
+ 승합차 인원 질문
+ 초기화 버튼
+ "AI" 차량유형 추정(규칙·키워드·유사도 기반 간단 분류)

판단 로직 개요
1) 업종 질의 → (택시/자동차학원/자동차임대업) 포함 시 즉시 공제가능
2) 차량명 질의 → 간단 AI 추정으로 차량유형 태그 도출
   - 승합 포함/추정 → 인원 수 질문 (8인 초과 공제 / 7인 이하 불가)
   - 경차·화물 포함/추정 → 공제가능
   - 그 외(세단·SUV 등) → 공제불가
3) 사이드바에 현재 입력값/추정결과 표시

실행 방법: streamlit run vat_chatbot_chatui_ai.py
"""

import re
import difflib
from typing import List, Tuple, Dict
import streamlit as st

# ---------------------------------------------
# 데이터 정의
# ---------------------------------------------
DEDUCTIBLE_INDUSTRIES = ["택시", "자동차학원", "자동차임대업"]

# 차량 유형 태그 표준화 키
VEHICLE_TAGS_ORDER = ["경차", "화물", "승합", "버스", "밴", "픽업", "SUV", "세단", "쿠페", "왜건", "트럭"]

# 키워드 → 태그, 가중치
KEYWORD_RULES: Dict[str, Tuple[str, int]] = {
    # 공제 가산 가능성 높은 분류
    "경차": ("경차", 5),
    "라보": ("화물", 5),
    "봉고": ("화물", 5),
    "포터": ("화물", 5),
    "픽업": ("픽업", 4),
    "트럭": ("트럭", 4),
    "밴": ("밴", 4),
    "카고": ("화물", 4),
    "탑차": ("화물", 4),
    "적재": ("화물", 3),
    "화물": ("화물", 5),
    # 승합/버스
    "승합": ("승합", 6),
    "버스": ("버스", 6),
    "9인승": ("승합", 6),
    "10인승": ("승합", 6),
    "11인승": ("승합", 6),
    "12인승": ("승합", 6),
    "15인승": ("승합", 6),
    # 일반 승용 추정(공제 불가 측)
    "세단": ("세단", 3),
    "소나타": ("세단", 5),
    "아반떼": ("세단", 5),
    "K3": ("세단", 5),
    "K5": ("세단", 5),
    "K7": ("세단", 5),
    "그랜저": ("세단", 5),
    "제네시스": ("세단", 4),
    # SUV 계열(원칙적으로 승용 취급)
    "SUV": ("SUV", 4),
    "투싼": ("SUV", 4),
    "스포티지": ("SUV", 4),
    "쏘렌토": ("SUV", 4),
    "싼타페": ("SUV", 4),
    "캐스퍼": ("경차", 4),
    # 승합으로 자주 쓰이는 모델명
    "스타렉스": ("승합", 5),
    "스타리아": ("승합", 5),
    "카니발": ("승합", 5),
}

# 모델명 소규모 사전(유사도 매칭용)
MODEL_LEXICON = {
    # 승합/밴/화물 쪽
    "봉고": "화물", "포터": "화물", "라보": "화물", "스타렉스": "승합", "스타리아": "승합", "카니발": "승합",
    # 세단/승용
    "소나타": "세단", "그랜저": "세단", "아반떼": "세단", "K5": "세단", "K3": "세단", "K7": "세단",
    # SUV/크로스오버
    "스포티지": "SUV", "쏘렌토": "SUV", "싼타페": "SUV", "투싼": "SUV",
    # 경차
    "캐스퍼": "경차", "모닝": "경차", "레이": "경차",
}

# 좌석 수 패턴 추출용
SEAT_PAT = re.compile(r"(\d+)\s*인\s*승")


def ai_guess_vehicle_types(text: str) -> Tuple[List[str], Dict[str, int], int]:
    """간단 규칙/유사도 기반으로 차량 유형 태그 후보를 반환.
    return (tags_sorted, score_map, seats_detected)
    """
    s = text.strip()
    s_lower = s.lower()

    # 좌석수 추출 (예: 9인승)
    seats = None
    m = SEAT_PAT.search(s)
    if m:
        try:
            seats = int(m.group(1))
        except Exception:
            seats = None

    scores: Dict[str, int] = {}

    # 1) 키워드 규칙 매칭
    for kw, (tag, w) in KEYWORD_RULES.items():
        if kw.lower() in s_lower:
            scores[tag] = scores.get(tag, 0) + w

    # 2) 모델명 유사도(간단) - 가장 유사한 키 1~3개 가산
    keys = list(MODEL_LEXICON.keys())
    close = difflib.get_close_matches(s, keys, n=3, cutoff=0.78)
    for k in close:
        tag = MODEL_LEXICON[k]
        scores[tag] = scores.get(tag, 0) + 4  # 유사도 가중치

    # 3) 좌석 수가 9 이상이면 승합 가산
    if seats is not None and seats >= 9:
        scores["승합"] = scores.get("승합", 0) + 3

    # 정렬된 태그 목록
    tags = sorted(scores, key=lambda t: (-scores[t], VEHICLE_TAGS_ORDER.index(t) if t in VEHICLE_TAGS_ORDER else 999))
    return tags, scores, seats if seats is not None else -1


# ---------------------------------------------
# Streamlit 설정
# ---------------------------------------------
st.set_page_config(page_title="부가가치세 차량공제 챗봇", page_icon="🤖")
st.title("🤖 부가가치세 차량공제 챗봇 (AI 차량유형 추정)")
st.caption("대화형으로 업종/차량 정보를 입력하고, 간단 AI가 차량유형을 추정해 공제여부를 안내합니다.")

# ---------------------------------------------
# 세션 상태
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
if "tags" not in st.session_state:
    st.session_state.tags = []
if "scores" not in st.session_state:
    st.session_state.scores = {}

# ---------------------------------------------
# 사이드바: 상태/추정 결과
# ---------------------------------------------
with st.sidebar:
    st.header("🧾 현재 입력값")
    st.write(f"**업종:** {st.session_state.industry or '—'}")
    st.write(f"**차량:** {st.session_state.vehicle or '—'}")
    st.write(f"**승합 인원:** {st.session_state.passenger_count if st.session_state.passenger_count is not None else '—'}")
    if st.session_state.tags:
        st.write("**AI 추정 유형:** ")
        st.write(", ".join(st.session_state.tags))
    if st.session_state.scores:
        with st.expander("점수 자세히 보기"):
            for k, v in sorted(st.session_state.scores.items(), key=lambda x: -x[1]):
                st.write(f"{k}: {v}")
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        st.session_state.step = 0
        st.session_state.industry = ""
        st.session_state.vehicle = ""
        st.session_state.passenger_count = None
        st.session_state.tags = []
        st.session_state.scores = {}
        st.rerun()

# ---------------------------------------------
# 기존 메시지 표시
# ---------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------
# 유틸
# ---------------------------------------------
def bot_say(message: str):
    with st.chat_message("assistant"):
        st.markdown(message)
    st.session_state.messages.append({"role": "assistant", "content": message})


def user_say(message: str):
    st.session_state.messages.append({"role": "user", "content": message})

# ---------------------------------------------
# 대화 시작
# ---------------------------------------------
if st.session_state.step == 0:
    bot_say("안녕하세요! 😊 차량 관련 부가가치세 매입세액 공제 여부를 도와드릴게요.\n\n어떤 **업종**에 종사하시나요?")
    st.session_state.step = 1

# ---------------------------------------------
# 입력창
# ---------------------------------------------
prompt = st.chat_input("메시지를 입력하세요...")
if prompt:
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
        st.session_state.vehicle = vehicle

        # --- AI 차량유형 추정 ---
        tags, scores, seats_in_text = ai_guess_vehicle_types(vehicle)
        st.session_state.tags = tags
        st.session_state.scores = scores

        # 사용자에게 추정 결과 안내
        if tags:
            bot_say(f"입력하신 차량 **{vehicle}** 에 대한 AI 추정 유형: **{', '.join(tags)}**")
        else:
            bot_say(f"입력하신 차량 **{vehicle}** 의 유형을 확신하기 어렵습니다. (추가 정보가 있으면 함께 입력해주세요: 예 '9인승', '화물', '픽업' 등)")

        # 분기: 승합/경차/화물 우선 처리
        if any(t in tags for t in ["경차", "화물"]):
            bot_say("✅ 경차 또는 화물차로 추정되어 차량 관련 비용 부가가치세 매입공제 **공제가능합니다.**")
            st.session_state.step = 999
        elif "승합" in tags or "버스" in tags or ("9인승" in vehicle):
            # 좌석수가 텍스트에 있었으면 바로 판정, 없으면 질문
            if seats_in_text >= 0:
                if seats_in_text > 8:
                    bot_say(f"🚐 {seats_in_text}인승 승합차는 8인승 초과이므로 ✅ **공제가능합니다.**")
                else:
                    bot_say(f"🚐 {seats_in_text}인승 승합차는 7인승 이하이므로 ❌ **공제불가능합니다.**")
                st.session_state.step = 999
            else:
                bot_say("승합차로 추정됩니다. 몇 인승 차량인가요? 숫자만 입력해주세요 (예: 9)")
                st.session_state.step = 3
        else:
            # 나머지(세단/SUV 등) → 공제 불가
            bot_say("❌ 개별소비세 과세 대상 차량(일반 승용 추정)으로 부가가치세 매입세액 **공제 불가능합니다.**")
            st.session_state.step = 999

    # Step 3️⃣: 승합차 인원수 입력
    elif st.session_state.step == 3:
        try:
            cnt = int(prompt)
            st.session_state.passenger_count = cnt
            if cnt > 8:
                bot_say(f"🚐 {cnt}인승 승합차는 8인승 초과이므로 ✅ **공제가능합니다.**")
            else:
                bot_say(f"🚐 {cnt}인승 승합차는 7인승 이하이므로 ❌ **공제불가능합니다.**")
            st.session_state.step = 999
        except ValueError:
            bot_say("숫자로 입력해주세요. (예: 9)")
    else:
        bot_say("대화를 다시 시작하려면 왼쪽 사이드바의 🔄 **대화 초기화** 버튼을 눌러주세요.")
