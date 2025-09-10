import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.prompts import ChatPromptTemplate 
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.output_parsers import StrOutputParser

from langchain.agents import AgentExecutor, create_tool_calling_agent # * 추가
from langchain_core.tools import tool # * 추가
from datetime import datetime # * 추가
from zoneinfo import ZoneInfo # * 추가
from pydantic import BaseModel, Field # * 추가
import yfinance as yf # * 추가

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=gemini_api_key)

st.title("도구 호출 챗봇")
st.caption("시계 + 주가 검색 도구 장착!") # 캡션 추가

# * 시계 도구 추가
@tool # @tool 데코레이터를 사용하여 함수를 도구로 등록
def get_current_time(timezone: str, location: str) -> str:
    """ 현재 시각을 반환하는 함수

    Args:
        timezone (str): 타임존 (예: 'Asia/Seoul') 실제 존재하는 타임존이어야 함
        location (str): 지역명. 타임존이 모든 지명에 대응되지 않기 때문에 이후 llm 답변 생성에 사용됨
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
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=gemini_api_key)

    # * 도구 바인딩
    tools = [get_current_time, get_yf_stock_history]

    # * 에이전트 프롬프트 정의
    prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 사용자의 질문에 답변을 하기 위해 tools를 사용할 수 있다."),
        ("human", "{question}"), # * input를 question으로 수정
        # AgentExecutor는 agent_scratchpad를 자동으로 채워 넣어,
        # 에이전트가 이전 단계의 행동과 결과를 기억하고 다음 행동을 결정할 수 있도록 함
        ("placeholder", "{agent_scratchpad}"),
    ])

    # * 에이전트 생성
    agent = create_tool_calling_agent(llm, tools, prompt)

    # * AgentExecutor 초기화
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    return agent_executor # * 수정

if clear_btn:
    st.session_state["messages"] = []

print_messages()

user_input = st.chat_input("시간 또는 주식에 대해 물어 보세요!")

if user_input:
    st.chat_message("user").write(user_input)
    add_message("user", user_input)  # st.session_state.messages에 사용자 입력값 추가

    chain = create_chain()

    ai_answer = chain.invoke({"question": user_input})
    st.chat_message("assistant").write(ai_answer['output']) # * 수정: 'output' 키의 값을 추출

    # 타이핑하듯이 답변 출력
    # ai_answer = chain.stream(
    #     {"question": user_input})
    # with st.chat_message("assistant"):
    #     container = st.empty()  # 페이지 전체를 다시 로드하지 않고도 콘텐츠를 동적으로 업데이트하는 빈 컨테이너 생성
    # ai_answer = ""
    # for token in response:  # response는 generator
    #     if isinstance(token, dict) and "output" in token:
    #         ai_answer += token["output"]
    #     elif isinstance(token, str):
    #         ai_answer += token
    #     container.markdown(ai_answer)

    add_message("assistant", ai_answer['output']) # * 수정: 'output' 키의 값을 추출

print(st.session_state["messages"])

# [질문 예시]
# 부산은 지금 몇시야?
# 테슬라는 한달 전에 비해 주가가 올랐나 내렸나?