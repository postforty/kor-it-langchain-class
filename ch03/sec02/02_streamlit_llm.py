import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# st.session_state
# - Streamlit에서 애플리케이션의 상태를 관리하는 데 사용되는 딕셔너리
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash")  # 새로운 채팅 세션을 생성 (대화의 연속성 유지)

st.title("나만의 LLM 챗봇 만들기")

if "messages" not in st.session_state:
    st.session_state["messages"] = []  # 채팅 기록을 저장할 리스트를 초기화

# 사이드바에 UI 요소를 배치
with st.sidebar:
    clear_btn = st.button("초기화")

# 저장된 모든 메시지를 반복하여 화면에 표시


def print_messages():
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])


# 새로운 채팅 세션을 다시 생성하고, 대화 기록을 완전히 초기화
if clear_btn:
    st.session_state["messages"] = []
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash")

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.session_state["messages"].append(
        {"role": "user", "content": user_input})
    # 사용자 채팅 메시지를 시각적으로 출력하는 기능
    with st.chat_message("user"):
        st.write(user_input)

    # Gemini API의 send_message 메서드를 호출
    # 사용자의 메시지를 API에 전달하고 응답을 받음
    response = st.session_state.chat_session.send_message(message=user_input)
    response_text = response.text

    st.session_state["messages"].append(
        {"role": "assistant", "content": response_text})
    # AI 채팅 메시지를 시각적으로 출력하는 기능
    with st.chat_message("assistant"):
        st.write(response_text)
