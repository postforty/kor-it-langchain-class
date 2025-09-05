import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate, load_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
# from langchain import hub
import glob

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("나만의 LangChain 챗봇")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "task_input" not in st.session_state:
    st.session_state["task_input"] = ""


def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


def clear_task():
    """
    콜백 함수: 버튼 클릭 시 st.session_state를 초기화한다.
    """
    st.session_state["messages"] = []
    st.session_state["task_input"] = ""


with st.sidebar:
    st.button("대화 초기화", on_click=clear_task)

    prompt_files = glob.glob("prompts/*.yaml")

    # 셀렉스 박스에 파일 경로 표시
    # print("prompt_files:", prompt_files)
    # selected_prompt = st.selectbox(
    #     "프롬프트를 선택해 주세요", prompt_files, index=0
    # )

    # 파일 경로를 사용자 친화적인 레이블로 매핑하는 딕셔너리 생성
    prompt_labels = {
        "prompts\\general.yaml": "일반 프롬프트",
        "prompts\\prompt-maker.yaml": "프롬프트 생성기",
        "prompts\\summary.yaml": "요약 프롬프트",
    }

    selected_prompt = st.selectbox(
        "프롬프트를 선택해 주세요",
        prompt_files,
        index=0,
        format_func=lambda x: prompt_labels.get(x, x),  # 파일 경로를 레이블로 변환
    )

    task_input = st.text_input(
        "TASK 입력", key="task_input", value=st.session_state["task_input"])

print("선택된 프롬프트:", selected_prompt)
print("선택된 프롬프트 내용:", load_prompt(selected_prompt, encoding="utf-8"))


def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


def create_chain(prompt_filepath, task=""):
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         ("system", "당신은 친절한 AI 어시스턴트입니다."),
    #         ("user", "#Question:\n{question}"),
    #     ]
    # )

    prompt = load_prompt(prompt_filepath, encoding="utf-8")

    if task:
        prompt = prompt.partial(task=task)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=gemini_api_key)

    output_parsers = StrOutputParser()

    chain = prompt | llm | output_parsers

    return chain


# print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    # add_message("user", user_input)

    chain = create_chain(selected_prompt, task=task_input)
    # response = chain.stream({"question": st.session_state.messages})
    response = chain.stream({"question": user_input})

    with st.chat_message("assistant"):
        container = st.empty()

        ai_answer = ""

        for token in response:
            ai_answer += token
            container.markdown(ai_answer)

    add_message("user", user_input)
    add_message("assistant", ai_answer)

print("st.session_state.messages:", st.session_state.messages)


# [테스트]
# 프롬프트를 선택해 주세요: prompt-maker.yaml 선택
# TASK 입력: 블러그 글 작성
# 입력 프롬프트: 랭체인이라는 주제로 글을 작성해 주세요
