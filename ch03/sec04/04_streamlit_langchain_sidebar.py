# 셀렉트 모드 변경시 즉시 언어가 반영되도록 개선함
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser

import os
from dotenv import load_dotenv
load_dotenv()

# gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("나만의 LangChain 챗봇 만들기")

if "messages" not in st.session_state:
    # 세션 상태에는 LangChain 메시지 객체(HumanMessage, AIMessage)들이 저장됩니다.
    st.session_state["messages"] = []

with st.sidebar:
    clear_btn = st.button("초기화")

    # * 추가
    selected_prompt = st.selectbox(
        "언어를 선택해 주세요", ("Korean", "English"), index=0
    )

# print(selected_prompt)


def print_messages():
    for lang_message in st.session_state["messages"]:
        # LangChain 메시지 객체의 .type 속성(human, ai 등)을 Streamlit 역할(user, assistant)로 매핑합니다.
        st_role = "user" if lang_message.type == "human" else "assistant"
        st.chat_message(st_role).write(lang_message.content)


def add_message(role, message):
    # 역할 문자열에 따라 적절한 LangChain 메시지 객체를 생성하여 저장합니다.
    if role == "user":
        msg_obj = HumanMessage(content=message)
    elif role == "assistant":
        msg_obj = AIMessage(content=message)
    else:
        return
        
    st.session_state["messages"].append(msg_obj)


def create_chain():
    if selected_prompt == "Korean":
        prompt = ChatPromptTemplate.from_messages(
            [
                # ("system", "당신은 한국어로 대답하는 친절한 AI 어시스턴트입니다."),
                # ("user", "#Question:\n{question}"),
                SystemMessage("당신은 한국어로 대답하는 친절한 AI 어시스턴트입니다."), # * 수정
                # 수정: 대화 기록(st.session_state.messages) 전체를 여기에 삽입합니다.
                MessagesPlaceholder(variable_name="messages"), # 대화의 연속성 유지
            ]
        )

    if selected_prompt == "English":
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage("당신은 영어로 대답하는 친절한 AI 어시스턴트입니다. 답변은 반드시 영어로 해야합니다."),
                MessagesPlaceholder(variable_name="messages"), # 대화의 연속성 유지
            ]
        )

    llm = init_chat_model(
        "google_genai:gemini-2.5-flash-lite",
        # google_api_key=gemini_api_key
    )

    output_parsers = StrOutputParser()

    chain = prompt | llm | output_parsers

    return chain


if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    add_message("user", user_input)

    chain = create_chain()
    
    # * 타이핑하듯이 답변 출력
    response = chain.stream(
        {
            "messages": st.session_state.messages
        }
    )

    with st.chat_message("assistant"):
        container = st.empty()

        ai_answer = ""

        for token in response:
            ai_answer += token
            container.markdown(ai_answer)

    # 대화 내용에 추가되는 부분
    add_message("assistant", ai_answer)

print(st.session_state["messages"])
