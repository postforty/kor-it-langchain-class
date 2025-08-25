# 랭체인과 LCEL 적용한 예제
# 메모리 기능 없음
import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate  # 추가
from langchain_google_genai import ChatGoogleGenerativeAI  # 추가
from langchain_core.output_parsers import StrOutputParser  # 추가
import os  # 추가
from dotenv import load_dotenv  # 추가
load_dotenv()  # 추가

gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("나만의 LangChain 챗봇 만들기")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:  # 추가
    clear_btn = st.button("초기화")


def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)


def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))


def create_chain():  # 체인
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 친절한 AI 어시스턴트입니다."),
            ("user", "#Question:\n{question}"),
        ]
    )
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=gemini_api_key)
    output_parsers = StrOutputParser()

    chain = prompt | llm | output_parsers

    return chain


if clear_btn:  # 추가
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:  # 수정
    st.chat_message("user").write(user_input)
    add_message("user", user_input) # st.session_state.messages에 사용자 입력값 추가
    
    chain = create_chain()
    # response = chain.stream({"question": user_input}) # 질문만 넘김
    response = chain.stream({"question": st.session_state.messages}) # 모든 대화 리스트를 넘김

    with st.chat_message("assistant"):
        container = st.empty()

        ai_answer = ""

        for token in response:
            ai_answer += token
            container.markdown(ai_answer)

    add_message("assistant", ai_answer)

print(st.session_state["messages"])
