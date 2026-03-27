# 셀렉트 모드 변경시 즉시 언어가 반영되도록 개선함
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

vectorstore = FAISS.load_local(
    "./faiss_index",
    embeddings,
    allow_dangerous_deserialization=True # 데이터 역직렬화 허용
)

retriever = vectorstore.as_retriever()

@tool
def search_documents(query: str) -> str:
    """테크노빌드 주식회사 임직원 통합 가이드북 검색 도구입니다."""
    docs = retriever.invoke(query)

    print("--- docs.page_content ---\n\n")
    for doc in docs:
        print(doc.page_content)
    print("--- docs.page_content ---\n\n")

    return "\n\n".join([doc.page_content for doc in docs])

st.title("나만의 LangChain 챗봇 만들기")

if "messages" not in st.session_state:
    # 세션 상태에는 LangChain 메시지 객체(HumanMessage, AIMessage)들이 저장됩니다.
    st.session_state["messages"] = []

with st.sidebar:
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


def create_chain():
    system_prompt = """당신은 테크노빌드 주식회사 가이드북 정보를 친절하게 제공하는 어시스턴트입니다.

1. 정보가 필요할 경우 반드시 검색 도구를 사용하여 확인하세요.
2. 답변은 반드시 검색된 문서의 내용에만 기반하여 작성하세요.
3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 모른다고 답변하세요.
"""

    agent = create_agent(
        model="google_genai:gemini-2.5-flash-lite",
        tools=[search_documents],
        system_prompt=system_prompt,
    )

    # 딕셔너리에서 마지막 AI 메시지 추출 (메시지가 없을 경우 대비)
    def extract_ai_msg(data):
        if isinstance(data, dict) and "messages" in data:
            return data["messages"][-1]
        return AIMessage(content="")

    # 메시지 객체에서 텍스트 내용만 추출 (Gemini의 리스트 구조 대응)
    def extract_text(msg):
        if hasattr(msg, "content"):
            content = msg.content
            if isinstance(content, list) and len(content) > 0:
                if isinstance(content[0], dict) and "text" in content[0]:
                    return content[0]["text"]
            return content
        return str(msg)

    # 체인 구성: 에이전트 -> 메시지 추출 -> 텍스트 추출 -> 문자열 변환
    chain = agent | extract_ai_msg | extract_text | StrOutputParser()

    return chain


if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    add_message("user", user_input)

    chain = create_chain()
    
    # * invoke를 사용하여 전체 결과를 가져옵니다. (KeyError 방지)
    response = chain.invoke(
        {
            "messages": st.session_state.messages
        }
    )

    with st.chat_message("assistant"):
        container = st.empty()

        ai_answer = ""

        # 글자 단위로 출력하여 타이핑 효과를 구현합니다.
        import time
        for token in response:
            ai_answer += token
            container.markdown(ai_answer)
            time.sleep(0.01)

    # 대화 내용에 추가되는 부분
    add_message("assistant", ai_answer)

print(st.session_state["messages"])
