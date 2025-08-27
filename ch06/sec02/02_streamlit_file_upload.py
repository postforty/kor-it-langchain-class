import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import load_prompt
# from langchain import hub
import glob

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("PDF 기반 QA")

if not os.path.exists(".cache"):
    os.mkdir(".cache")

if not os.path.exists(".cache/files"):  # 폴더 앞에 .을 붙이면 숨김 처리함을 의미
    os.mkdir(".cache/files")

if not os.path.exists(".cache/embeddings"):
    os.mkdir(".cache/embeddings")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:
    clear_btn = st.button("대화 초기화")

    uploaded_file = st.file_uploader("파일 업로드", type=["pdf"])

    selected_prompt = "prompts/pdf-rag.yaml"

    # prompt_files = glob.glob("prompts/*.yaml")

    # selected_prompt = st.selectbox(
    #     "프롬프트를 선택해 주세요", prompt_files, index=0
    # )

    # task_input = st.text_input("TASK 입력", "")

print("selected_prompt:", selected_prompt)


def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


@st.cache_resource(show_spinner="업로드한 파일을 처리 중입니다...")
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)


if uploaded_file:
    embed_file(uploaded_file)


def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


# def create_chain(prompt_filepath, task=""):
def create_chain(prompt_filepath):
    prompt = load_prompt(prompt_filepath, encoding="utf-8")

    # if task:
    #     prompt = prompt.partial(task=task)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=gemini_api_key)

    output_parsers = StrOutputParser()

    chain = prompt | llm | output_parsers

    return chain


if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    # add_message("user", user_input)

    # chain = create_chain(selected_prompt, task=task_input)
    chain = create_chain(selected_prompt)
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


'''
[테스트]
프롬프트를 선택해 주세요: prompt-maker.yaml 선택
TASK 입력: 블러그 글 작성
입력 프롬프트: 대한민국이라는 주제로 글을 작성해 주세요
'''
