import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain import hub  # 추가
from langchain_core.prompts import load_prompt  # 추가

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("나만의 챗봇 만들기")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:
    clear_btn = st.button("초기화")

    # 추가
    selected_prompt = st.selectbox(
        "프롬프트를 선택해 주세요", ("기본모드", "SNS 게시글", "요약"), index=0
    )

print(selected_prompt)


def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


def create_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 친절한 AI 어시스턴트입니다."),
            ("user", "#Question:\n{question}"),
        ]
    )

    if selected_prompt == "SNS 게시글":  # 추가
        prompt = load_prompt("", encoding="utf-8")  # 작동하는 코드 추가 요망

    if selected_prompt == "요약":  # 추가
        prompt = hub.pull("")  # 작동하는 코드 추가 요망

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=gemini_api_key)
    
    output_parsers = StrOutputParser()

    chain = prompt | llm | output_parsers

    return chain


if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    chain = create_chain()
    response = chain.stream({"question": user_input})

    with st.chat_message("assistant"):
        container = st.empty()

        ai_answer = ""

        for token in response:
            ai_answer += token
            container.markdown(ai_answer)

    add_message("user", user_input)
    add_message("assistant", ai_answer)

print(st.session_state["messages"])
