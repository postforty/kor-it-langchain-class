import streamlit as st

st.title("나만의 챗봇 만들기")

# 처음 한 번만 session_state 생성
if "messages" not in st.session_state:
    st.session_state["messages"] = []

user_input = st.chat_input("궁금한 내용을 물어보세요!")

print(user_input)

if user_input:
    #   st.write(f"사용자 입력: {user_input}")

    #   아바타 추가
    #   대화를 입력할때마다 새로고침됨
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write(user_input)

    st.session_state["messages"].append(("user", user_input))
    st.session_state["messages"].append(("assistant", user_input))

print(st.session_state["messages"])
