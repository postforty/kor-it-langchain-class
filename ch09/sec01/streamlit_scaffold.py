import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
# TODO: 메모리 저장을 위한 InMemorySaver 임포트
# from langgraph.checkpoint.memory import InMemorySaver 

from langchain.tools import tool 
from langchain.agents import create_agent 
from datetime import datetime 
from zoneinfo import ZoneInfo 
from pydantic import BaseModel, Field 
import yfinance as yf 
from langchain_community.tools import DuckDuckGoSearchResults 
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper 

from dotenv import load_dotenv
load_dotenv()

st.title("🛠️ 도구 & 메모리 실습 챗봇")
st.caption("안내에 따라 TODO 부분을 채워 기능을 완성해 보세요!")

# TODO: 세션 상태에 thread_id가 없으면 현재 시간을 기반으로 생성하세요.
if "thread_id" not in st.session_state:
    pass # st.session_state["thread_id"] = ...

# --- [실습 1] 도구(Tool) 정의하기 ---

@tool
def get_current_time(timezone: str, location: str) -> str:
    """ 현재 시각을 반환하는 함수
    Args:
        timezone (str): 타임존 (예: 'Asia/Seoul')
        location (str): 지역명
    """
    target_timezone = ZoneInfo(timezone)
    now = datetime.now(target_timezone).strftime("%Y-%m-%d %H:%M:%S")
    return f'{timezone} ({location}) 현재시각 {now}'

# TODO: 나만의 새로운 도구를 정의해 보세요. (예: 덧셈 도구, 간단한 인사 도구 등)
# @tool
# def my_custom_tool(...):
#     """ ... """
#     return ...


# --- [실습 2] 에이전트 및 메모리 설정 ---

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

def clear_task():
    st.session_state["messages"] = []
    st.session_state["chain"] = None
    # TODO: 대화 초기화 시 thread_id도 새롭게 갱신해 보세요.
    
with st.sidebar:  
    st.button("대화 초기화", on_click=clear_task)

def create_chain():
    # TODO: 사용할 도구들을 리스트에 담으세요.
    tools = [get_current_time] 

    # TODO: create_agent에 checkpointer 옵션을 추가하여 메모리 기능을 활성화하세요.
    return create_agent(
        model="google_genai:gemini-2.0-flash", 
        tools=tools,
        # checkpointer=...
    )

if st.session_state["chain"] is None:
    st.session_state["chain"] = create_chain()

# 메시지 출력 함수
for chat_message in st.session_state["messages"]:
    if isinstance(chat_message, HumanMessage):
        with st.chat_message("user"): st.write(chat_message.content)
    elif isinstance(chat_message, AIMessage):
        with st.chat_message("assistant"): st.write(chat_message.content)


# --- [실습 3] 대화 실행 및 메모리 참조 ---

if user_input := st.chat_input("질문을 입력하세요!"):
    st.chat_message("user").write(user_input)
    st.session_state["messages"].append(HumanMessage(content=user_input))

    with st.chat_message("assistant"):
        # TODO: 답변을 출력할 빈 컨테이너를 먼저 생성하세요 (ai_container = st.empty())
        
        # TODO: st.status를 사용하여 에이전트의 처리 과정을 시각화하세요.
        # with st.status("답변 생성 중...", expanded=True) as status:
        #     # TODO: st.session_state["chain"].stream()을 사용하여 대화를 실행하세요.
        #     # 'configurable' 설정을 통해 thread_id를 전달하는 것을 잊지 마세요!
            
        #     # TODO: 실행이 완료되면 status를 'complete' 상태로 업데이트하세요.
        #     pass

        # TODO: 최종 답변을 추출하여 ai_container에 출력하고 messages에 저장하세요.
        st.write("TODO: [실습 3] 대화 로직을 완성해 보세요!")
