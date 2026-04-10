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
st.caption("⏰시계 + 📉주가 검색 + 🔍웹 검색 + 🧠메모리 + ⚡개선된 UX!")

# * 세션 상태 초기화 (thread_id 추가)
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(datetime.now().timestamp())

# * 시계 도구 추가
@tool
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
def get_web_search(query: str, search_period: str='w', region: str='kr-kr') -> str:
    """
    특정 지역과 기간을 설정하여 웹 검색(뉴스)을 수행합니다.

    Args:
        query (str): 검색어
        search_period (str): 검색 기간. 'd'(일간), 'w'(주간), 'm'(월간), 'y'(연간) 중 선택
        region (str): 검색 지역 코드. 한국('kr-kr'), 미국('us-en'), 일본('jp-jp'), 영국('uk-en') 등
    
    Returns:
        str: 검색된 뉴스 결과 리스트
    """
    # 1. 전달받은 region과 search_period로 API 설정
    wrapper = DuckDuckGoSearchAPIWrapper(
        region=region,
        time=search_period
    )

    print('\n----- WEB SEARCH (News) -----')
    print(f"QUERY  : {query}")
    print(f"REGION : {region}")
    print(f"PERIOD : {search_period}")

    search = DuckDuckGoSearchResults(
        api_wrapper=wrapper,
        # backend="news",
        results_separator=';\n'
    )

    try:
        searched = search.invoke(query)
        return searched
    except Exception as e:
        return f"검색 결과가 없거나 오류가 발생했습니다: {e}"

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

def clear_task():
    st.session_state["messages"] = []
    st.session_state["chain"] = None
    # 새로운 대화 세션을 위해 thread_id 초기화
    st.session_state["thread_id"] = str(datetime.now().timestamp())
    
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
        add_message("user", user_input)

        with st.chat_message("assistant"):
            # 1. 답변을 출력할 컨테이너를 status 외부(상단)에 생성
            ai_container = st.empty()
            
            # 2. 도구 호출 및 처리 과정을 보여주는 status box
            with st.status("답변을 생성하고 있습니다...", expanded=True) as status:
                # stream을 통해 중간 과정 및 최종 결과 수집
                final_state = None
                for state in st.session_state["chain"].stream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    {"configurable": {"thread_id": st.session_state["thread_id"]}},
                    stream_mode="values"
                ):
                    final_state = state
                    # 중간 과정에서 도구 호출 등의 메시지가 추가될 때마다 status 업데이트
                    last_msg = state["messages"][-1]
                    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                        for tool_call in last_msg.tool_calls:
                            status.write(f"🛠️ `{tool_call['name']}` 도구를 실행 중입니다...")
                
                status.update(label="답변 완료!", state="complete", expanded=False)

            # 3. 최종 답변 추출 및 컨테이너에 출력
            if final_state:
                last_message = final_state["messages"][-1]
                ai_content = ""
                
                if isinstance(last_message.content, str):
                    ai_content = last_message.content
                elif isinstance(last_message.content, list):
                    for content_part in last_message.content:
                        if isinstance(content_part, dict) and content_part.get("type") == "text":
                            ai_content += content_part.get("text", "")
                        elif isinstance(content_part, str):
                            ai_content += content_part
                
                ai_container.write(ai_content)
                add_message("assistant", ai_content)

# [질문 예시]
# 부산은 지금 몇시야?
# 테슬라(TSLA)는 한달 전에 비해 주가가 올랐나 내렸나?
# 현재 박스오피스 1위 영화는?