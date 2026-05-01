# 랭체인과 LCEL 적용한 예제
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage # * 수정
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # * 추가
from langchain.chat_models import init_chat_model # * 추가
from langchain_core.output_parsers import StrOutputParser  # * 추가

import os  # * 추가
from dotenv import load_dotenv  # * 추가
load_dotenv()  # * 추가

# gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("나만의 LangChain 챗봇 만들기")

if "messages" not in st.session_state:
    # 세션 상태에는 LangChain 메시지 객체(HumanMessage, AIMessage)들이 저장됩니다.
    st.session_state["messages"] = []

with st.sidebar:  # * 추가
    clear_btn = st.button("초기화")


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


def create_chain():  # * 체인
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage("당신은 친절하고 도움이 되는 AI 어시스턴트입니다."),
            # * 수정: 대화 기록(st.session_state.messages) 전체를 여기에 삽입합니다.
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


if clear_btn:  # 추가
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:  # 수정
    # 1. 사용자 메시지를 화면에 출력
    st.chat_message("user").write(user_input)
    # 2. 사용자 메시지를 세션에 저장 (HumanMessage 객체로 저장됨)
    add_message("user", user_input)

    chain = create_chain()

    # 3. 모델 호출: MessagesPlaceholder가 받는 키인 "messages"에 전체 대화 기록을 넘깁니다.
    #    (이 리스트에는 방금 add_message로 추가된 새로운 HumanMessage도 포함되어 있습니다.)
    response = chain.invoke(
        {
            "messages": st.session_state.messages
        }
    )

    # 4. 모델 응답을 화면에 출력
    st.chat_message("assistant").write(response)
    # 5. 모델 응답을 세션에 저장 (AIMessage 객체로 저장됨)
    add_message("assistant", response)

print(st.session_state["messages"])
