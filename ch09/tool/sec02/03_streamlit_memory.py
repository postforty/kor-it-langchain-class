import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver  # * 추가

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

st.title("🛠️도구 호출 챗봇")
st.caption("⏰시계 + 📉주가 검색 도구 + 🔍웹 검색 도구 + 메모리 기능 장착!")

# * 시계 도구 추가
@tool # @tool 데코레이터를 사용하여 함수를 도구로 등록
def get_current_time(timezone: str, location: str) -> str:
    """ 현재 시각을 반환하는 함수

    Args:
        timezone (str): 타임존 (예: 'Asia/Seoul') 실제 존재하는 타임존이어야 함
        location (str): 지역명. 타임존이 모든 지명에 대응되지 않기 때문에 이후 model 답변 생성에 사용됨
    """
    target_timezone = ZoneInfo(timezone)
    now = datetime.now(target_timezone).strftime("%Y-%m-%d %H:%M:%S")
    location_and_local_time = f'{timezone} ({location}) 현재시각 {now} ' # 타임존, 지역명, 현재시각을 문자열로 반환
    print(location_and_local_time)
    return location_and_local_time

# * 추가
class StockHistoryInput(BaseModel):
    ticker: str = Field(..., title="주식 코드", description="주식 코드 (예: AAPL)")
    period: str = Field(..., title="기간", description="주식 데이터 조회 기간 (예: 1d, 1mo, 1y)")

# * 주가 검색 도구 추가
@tool
def get_yf_stock_history(stock_history_input: StockHistoryInput) -> str:
    """ 주식 종목의 가격 데이터를 조회하는 함수"""
    stock = yf.Ticker(stock_history_input.ticker)
    history = stock.history(period=stock_history_input.period)
    history_md = history.to_markdown() 

    return history_md

@tool
def get_web_search(query: str, search_period: str='w') -> str:
    """
    웹 검색을 수행하는 함수.

    Args:
        query (str): 검색어
        search_period (str): 검색 기간 (e.g., "w" for past week (default), "m" for past month, "y" for past year, "d" for past day)

    Returns:
        str: 검색 결과
    """
    wrapper = DuckDuckGoSearchAPIWrapper(
        region="kr-kr",
        time=search_period
    )

    print('\n----- WEB SEARCH -----')
    print(query)
    print(search_period)

    search = DuckDuckGoSearchResults(
        api_wrapper=wrapper,
        source="news",
        results_separator=';\n'
    )

    searched = search.invoke(query)
    
    for i, result in enumerate(searched.split(';\n')):
        print(f'{i+1}. {result}')
    
    return searched

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
        if isinstance(chat_message, HumanMessage):
            with st.chat_message("user"):
                st.write(chat_message.content)
        elif isinstance(chat_message, AIMessage):
            with st.chat_message("assistant"):
                st.write(chat_message.content)

def add_message(role, message):
    if role == "user":
        st.session_state["messages"].append(HumanMessage(content=message))
    elif role == "assistant":
        st.session_state["messages"].append(AIMessage(content=message))
    
def create_chain():
    # * 도구 바인딩
    tools = [get_current_time, get_yf_stock_history, get_web_search]

    # * 에이전트 생성 및 반환
    return create_agent(
        model="google_genai:gemini-2.5-flash", 
        tools=tools, 
        checkpointer=InMemorySaver() # * 추가
    )

print_messages()

if st.session_state["chain"] is None:
    st.session_state["chain"] = create_chain()

if user_input := st.chat_input("시간 또는 주식 등에 대해 물어 보세요!"):
    if st.session_state["chain"] is not None:
        st.chat_message("user").write(user_input)
        add_message("user", user_input)  # st.session_state.messages에 사용자 입력값 추가

        # invoke 한번에 출력
        ai_answer = st.session_state["chain"].invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            {"configurable": {"thread_id": "1"}},
        )
        
        # AI 답변 내용 추출 (문자열 또는 리스트 형태 처리)
        last_message = ai_answer["messages"][-1]
        ai_content = ""
        
        if isinstance(last_message.content, str):
            ai_content = last_message.content
        elif isinstance(last_message.content, list):
            for content_part in last_message.content:
                if isinstance(content_part, dict) and content_part.get("type") == "text":
                    ai_content += content_part.get("text", "")
                elif isinstance(content_part, str):
                    ai_content += content_part

        print("ai_answer:", ai_answer["messages"])
        st.chat_message("assistant").write(ai_content) 

        add_message("assistant", ai_content)

# [질문 예시]
# 부산은 지금 몇시야?
# 테슬라(TSLA)는 한달 전에 비해 주가가 올랐나 내렸나?
# 현재 박스오피스 1위 영화는?