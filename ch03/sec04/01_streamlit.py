# 공식 문서: https://streamlit.io/playground?example=llm_chat
# user, assistant 동일 대화 출력
# 실행 명령: uv run streamlit run 01_streamlit.py
# 종료 방법: ctrl + c
import streamlit as st

st.title("나만의 챗봇 만들기")

# 스트림릿에서 관리하는 대화 내용(세션 상태)을 저장하는 리스트
# 처음 한 번만 session_state 생성하기 위한 조건문 (스트림릿은 대화가 추가될 때마다 새로고침됨)
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# * 저장된 모든 메시지를 반복하여 화면에 표시
def print_messages():
    for role, message in st.session_state["messages"]:
        with st.chat_message(role):
            st.write(message)

print_messages()

if user_input := st.chat_input("궁금한 내용을 물어보세요!"):
    #   st.write(f"사용자 입력: {user_input}")

    #   아바타 추가
    #   대화를 입력할 때마다 새로고침됨
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write(user_input)

    # 대화 내용을 세션 상태에 저장
    st.session_state["messages"].append(("user", user_input))
    st.session_state["messages"].append(("assistant", user_input))

print(st.session_state["messages"])
