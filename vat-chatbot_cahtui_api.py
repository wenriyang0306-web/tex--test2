# -*- coding: utf-8 -*-
"""
외부 API(OpenAI) 연동 버전 – 부가가치세 차량공제 챗봇 (Streamlit Chat UI)
-----------------------------------------------------------------------------
기능
- 대화형(말풍선) UI
- 업종 질문 → (택시/자동차학원/자동차임대업) 즉시 공제
- 차량명 → OpenAI Responses API로 '차량유형/좌석수' 구조화 추출
- 승합이면 좌석수 규칙 적용(>8인승 공제, ≤7인승 불가)
- 경차/화물은 공제, 그 외(세단/SUV 등) 불가
- 사이드바: 현재 입력값/AI 추정 결과 표시
- 초기화 버튼

사전 준비
1) pip install streamlit openai
2) 환경변수 설정 (Windows PowerShell 예):
   $Env:OPENAI_API_KEY = "sk-..."
   (macOS/Linux): export OPENAI_API_KEY="sk-..."

실행: streamlit run vat_chatbot_chatui_openai.py
문서: OpenAI Responses API / Structured Outputs 참고
"""

import os
from typing import Dict, Any
import streamlit as st
from openai import OpenAI

# ------------------------------
# 상수 정의
# ------------------------------
DEDUCTIBLE_INDUSTRIES = ["택시", "자동차학원", "자동차임대업"]
SUPPORTED_TYPES = ["경차", "화물", "승합", "버스", "밴", "픽업", "SUV", "세단", "쿠페", "왜건", "트럭"]

# ------------------------------
# OpenAI 클라이언트
# ------------------------------
def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.stop()
    return OpenAI(api_key=api_key)


def classify_vehicle_external(vehicle_text: str) -> Dict[str, Any]:
    """OpenAI Responses API를 호출해 차량유형/좌석수/근거를 JSON으로 받음."""
    client = get_client()

    schema = {
        "type": "object",
        "properties": {
            "vehicle_type": {
                "type": "string",
                "description": "차량의 대표 분류",
                "enum": SUPPORTED_TYPES
            },
            "seats": {
                "type": "integer",
                "description": "좌석 수가 텍스트에 명시된 경우 정수, 없으면 -1",
                "minimum": -1
            },
            "rationale": {
                "type": "string",
                "description": "판단 근거 요약 (키워드/모델명/맥락)"
            }
        },
        "required": ["vehicle_type", "seats", "rationale"],
        "additionalProperties": False
    }

    prompt = (
        "사용자가 입력한 문자열에서 차량의 유형과 좌석수를 추출하세요.\n"
        "차량 유형은 다음 중 하나로만 답하세요: " + ", ".join(SUPPORTED_TYPES) + "\n"
        "좌석수가 언급되지 않으면 seats는 -1.\n"
        "예시 입력: '스타렉스 9인승' → vehicle_type='승합', seats=9\n"
        f"입력: {vehicle_text}"
    )

    try:
        resp = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "vehicle_extraction",
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        data = resp.output[0].content[0].text  # JSON 문자열
        import json
        return json.loads(data)
    except Exception as e:
        return {"vehicle_type": "세단", "seats": -1, "rationale": f"API 오류: {e}"}


# ------------------------------
# Streamlit 설정 및 상태
# ------------------------------
st.set_page_config(page_title="부가가치세 차량공제 챗봇", page_icon="🤖")
st.title("🤖 부가가치세 차량공제 챗봇 (OpenAI)")
st.caption("외부 API를 사용해 차량유형을 구조적으로 판별합니다.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "industry" not in st.session_state:
    st.session_state.industry = ""
if "vehicle" not in st.session_state:
    st.session_state.vehicle = ""
if "ai_result" not in st.session_state:
    st.session_state.ai_result = {}
if "passenger_count" not in st.session_state:
    st.session_state.passenger_count = None

# ------------------------------
# 사이드바
# ------------------------------
with st.sidebar:
    st.header("🧾 현재 입력값")
    st.write(f"**업종:** {st.session_state.industry or '—'}")
    st.write(f"**차량:** {st.session_state.vehicle or '—'}")
    if st.session_state.ai_result:
        st.write("**AI 추정 결과:**")
        st.json(st.session_state.ai_result, expanded=False)
    if st.button("🔄 대화 초기화"):
        st.session_state.clear()
        st.rerun()

# ------------------------------
# 메시지 렌더
# ------------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


def bot_say(msg: str):
    with st.chat_message("assistant"):
        st.markdown(msg)
    st.session_state.messages.append({"role": "assistant", "content": msg})


def user_say(msg: str):
    st.session_state.messages.append({"role": "user", "content": msg})

# ------------------------------
# 첫 질문
# ------------------------------
if st.session_state.step == 0:
    bot_say("안녕하세요! 😊 차량 관련 부가가치세 매입세액 공제 여부를 도와드릴게요.\n\n어떤 **업종**에 종사하시나요?")
    st.session_state.step = 1

# ------------------------------
# 입력 처리
# ------------------------------
if prompt := st.chat_input("메시지를 입력하세요..."):
    user_say(prompt)

    # Step 1: 업종
    if st.session_state.step == 1:
        st.session_state.industry = prompt.strip()
        if any(k in st.session_state.industry for k in DEDUCTIBLE_INDUSTRIES):
            bot_say("✅ 차량 관련 비용 부가가치세 매입공제 **공제가능합니다.**\n\n(택시·자동차학원·자동차임대업 등은 차량을 직접 사용하므로 공제대상입니다.)")
            st.session_state.step = 999
        else:
            bot_say("알겠습니다. 업종에 따라 직접 공제는 불가하네요.\n이제 **차량명**을 알려주세요. (예: 소나타, 스타렉스 9인승, 봉고 화물 등)")
            st.session_state.step = 2

    # Step 2: 차량 → 외부 API 분류
    elif st.session_state.step == 2:
        st.session_state.vehicle = prompt.strip()
        with st.chat_message("assistant"):
            st.markdown("🔎 차량 정보를 분석 중입니다… (OpenAI)")
        ai = classify_vehicle_external(st.session_state.vehicle)
        st.session_state.ai_result = ai

        vtype = ai.get("vehicle_type", "세단")
        seats = ai.get("seats", -1)
        rationale = ai.get("rationale", "")

        bot_say(f"입력하신 차량은 **{st.session_state.vehicle}** 입니다.\nAI 추정: **{vtype}**, 좌석수: **{seats if seats != -1 else '미기재'}**\n근거: {rationale}")

        if vtype in ("경차", "화물"):
            bot_say("✅ 경차/화물차로 분류되어 차량 관련 비용 부가가치세 매입공제 **공제가능합니다.**")
            st.session_state.step = 999
        elif vtype in ("승합", "버스"):
            if seats != -1:
                if seats > 8:
                    bot_say("✅ 8인승 초과 승합차이므로 공제대상입니다.")
                else:
                    bot_say("❌ 7인승 이하 승합차는 공제대상이 아닙니다.")
                st.session_state.step = 999
            else:
                bot_say("몇 인승 차량인가요? 숫자만 입력해주세요 (예: 9)")
                st.session_state.step = 3
        else:
            bot_say("❌ 개별소비세 과세 대상 차량(일반 승용 추정)으로 부가가치세 매입세액 **공제 불가능합니다.**")
            st.session_state.step = 999

    # Step 3: 좌석수 수집 (승합)
    elif st.session_state.step == 3:
        try:
            n = int(prompt)
            st.session_state.passenger_count = n
            if n > 8:
                bot_say("✅ 8인승 초과 승합차이므로 공제대상입니다.")
            else:
                bot_say("❌ 7인승 이하 승합차는 공제대상이 아닙니다.")
            st.session_state.step = 999
        except ValueError:
            bot_say("숫자로 입력해주세요. (예: 9)")
    else:
        bot_say("대화를 다시 시작하려면 사이드바의 🔄 **대화 초기화** 버튼을 눌러주세요.")
