# * ch03\sec02\04_streamlit_langchain_lcel.py 코드 재사용
import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate 
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.output_parsers import StrOutputParser 

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=gemini_api_key)

# print(model.invoke([HumanMessage("부산은 지금 몇시야?")]))
# print(model.invoke([HumanMessage("테슬라는 한달 전에 비해 주가가 올랐나 내렸나?")]))

st.title("🛠️도구 호출 챗봇")
st.caption("⏰시계 + 📉주가 검색 도구 장착!")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:  
    clear_btn = st.button("초기화")

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
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=gemini_api_key)
    output_parsers = StrOutputParser()

    chain = prompt | model | output_parsers

    return chain

if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("시간 또는 주식에 대해 물어 보세요!")

if user_input:  # 수정
    st.chat_message("user").write(user_input)
    add_message("user", user_input)  # st.session_state.messages에 사용자 입력값 추가

    chain = create_chain()

    # 답변이 완전히 생성되면 출력
    # response = chain.invoke({"question": user_input}) # 질문만 넘김
    # response = chain.invoke(
    #     {"question": st.session_state.messages})  # 모든 대화 리스트를 넘김

    # st.chat_message("assistant").write(response)
    # add_message("assistant", response)


    # 타이핑하듯이 답변 출력
    response = chain.stream(
        {"question": st.session_state.messages})
    with st.chat_message("assistant"):
        container = st.empty()  # 페이지 전체를 다시 로드하지 않고도 콘텐츠를 동적으로 업데이트하는 빈 컨테이너 생성

        ai_answer = ""

        for token in response:  # response는 generator
            ai_answer += token
            container.markdown(ai_answer)

    add_message("assistant", ai_answer)

print(st.session_state["messages"])
