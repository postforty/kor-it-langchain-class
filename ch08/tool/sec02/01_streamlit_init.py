import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate 
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.output_parsers import StrOutputParser 
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from dotenv import load_dotenv
load_dotenv()

st.title("🛠️도구 호출 챗봇")
st.caption("⏰시계 + 📉주가 검색 도구 장착!")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

def clear_task():
    st.session_state["messages"] = []
    st.session_state["chain"] = None
    
with st.sidebar:  
    clear_btn = st.button("대화 초기화", on_click=clear_task)

def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)

def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))

def create_chain():
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="당신은 친절한 AI 어시스턴트입니다."),
        MessagesPlaceholder(variable_name="history"),
        HumanMessage(content="{input}"),
    ])
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    output_parsers = StrOutputParser()

    chain = prompt | model | output_parsers
    return chain

print_messages()

if st.session_state["chain"] is None:
    st.session_state["chain"] = create_chain()

if user_input := st.chat_input("시간 또는 주식에 대해 물어 보세요!"):
    if st.session_state["chain"] is not None:
        st.chat_message("user").write(user_input)
        add_message("user", user_input)

        # history: BaseMessage 리스트 생성
        history = []
        for msg in st.session_state.messages:
            if hasattr(msg, "role") and hasattr(msg, "content"):
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=msg.content))
            elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] == "user":
                    history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    history.append(AIMessage(content=msg["content"]))

        # MessagesPlaceholder 대응! history + input으로 stream
        response = st.session_state["chain"].stream({
            "history": history,
            "input": user_input
        })

        with st.chat_message("assistant"):
            container = st.empty()

            ai_answer = ""

            for token in response:
                ai_answer += token
                container.markdown(ai_answer)

        add_message("assistant", ai_answer)

print(st.session_state["messages"])