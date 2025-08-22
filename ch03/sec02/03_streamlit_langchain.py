# 랭체인 적용
# user, assistant 모두 동일 대화 출력
import streamlit as st
from langchain_core.messages.chat import ChatMessage  # 추가

st.title("나만의 챗봇 만들기")

if "messages" not in st.session_state:
    st.session_state["messages"] = []


def print_messages():  # 모든 메시지 출력
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


def add_message(role, message):  # 메시지 저장
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


user_input = st.chat_input("궁금한 내용을 물어보세요!")

print_messages()

print(user_input)

if user_input:
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write(user_input)

    add_message("user", user_input)
    add_message("assistant", user_input)

print(st.session_state["messages"])
