# 랭체인 메모리 없이 멀티턴 만들기
# 대화 내용을 리스트로 관리
# 대화 내용을 데이터베이스에 저장, 히스토리 수정시 유용
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# 모델 초기화
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=gemini_api_key)

# 사용자의 메시지 처리하기 위한 함수
def get_ai_response(messages):
    response = llm.stream(messages)

    for chunk in response:
        yield chunk


# Streamlit 앱
st.title("💬 Langchain Chat")

# 스트림릿 session_state에 메시지 저장
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        SystemMessage("너는 사용자를 돕기 위해 최선을 다하는 인공지능 봇이다. "),
        AIMessage("How can I help you?")
    ]

# 스트림릿 화면에 메시지 출력
for msg in st.session_state.messages:
    if msg.content:
        if isinstance(msg, SystemMessage):
            st.chat_message("system").write(msg.content)
        elif isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)

# 사용자 입력 처리
if prompt := st.chat_input():
    st.chat_message("user").write(prompt)  # 사용자 메시지 출력
    st.session_state.messages.append(HumanMessage(prompt))  # 사용자 메시지 저장

    response = get_ai_response(st.session_state["messages"])

    result = st.chat_message("assistant").write_stream(response)  # AI 메시지 출력
    st.session_state["messages"].append(AIMessage(result))  # AI 메시지 저장
