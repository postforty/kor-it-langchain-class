import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# print("도구 호출 가능한 챗봇")

# 모델 초기화
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", google_api_key=gemini_api_key)

# 도구 함수 정의


@tool
def get_current_time(timezone: str, location: str) -> str:
    """ 현재 시각을 반환하는 함수

    Args:
        timezone (str): 타임존 (예: 'Asia/Seoul') 실제 존재하는 타임존이어야 함
        location (str): 지역명. 타임존이 모든 지명에 대응되지 않기 때문에 이후 llm 답변 생성에 사용됨
    """
    try:
        target_timezone = ZoneInfo(timezone)
        now = datetime.now(target_timezone).strftime("%Y-%m-%d %H:%M:%S")
        location_and_local_time = f'{timezone} ({location}) 현재시각 {now} ' # 타임존, 지역명, 현재시각을 문자열로 반환
        print(location_and_local_time)
        return location_and_local_time
    except ZoneInfoNotFoundError:
        return f"알 수 없는 타임존: {timezone}"


# 도구 바인딩
tools = [get_current_time]

# 에이전트 프롬프트 정의
prompt = ChatPromptTemplate.from_messages([
    ("system", "너는 사용자의 질문에 답변을 하기 위해 tools를 사용할 수 있다."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# 에이전트 생성 및 실행기 초기화
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 사용자의 메시지 처리하기 위한 함수
def get_ai_response(messages):
    # ChatPromptTemplate의 input과 chat_history에 맞게 메시지 분리
    current_question = messages[-1].content
    chat_history = messages[:-1]

    full_response = ""
    for chunk in agent_executor.stream({"input": current_question, "chat_history": chat_history}):
        if "output" in chunk:
            full_response += chunk["output"]
            yield chunk["output"]
        elif "actions" in chunk:
            # 에이전트가 도구를 실행할 때의 중간 단계 처리
            for action in chunk["actions"]:
                tool_call_message = f"**도구 호출:** `{action.tool}` (입력: `{action.tool_input}`)\n"
                yield tool_call_message
        elif "steps" in chunk:
            # 에이전트 실행 단계 (도구 출력 포함)
            for step in chunk["steps"]:
                if hasattr(step, 'observation'):
                    tool_output_message = f"**도구 출력:** `{step.observation}`\n"
                    yield tool_output_message
    
    # 스트리밍 완료 후 최종 응답 저장
    st.session_state.messages.append(AIMessage(full_response))


# Streamlit 앱
st.title("💬 Langchain Chat")

# 스트림릿 session_state에 메시지 저장
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        SystemMessage("너는 사용자를 돕기 위해 최선을 다하는 인공지능 봇이다. "),
        AIMessage("무엇을 도와 드릴까요?")
    ]

# 스트림릿 화면에 메시지 출력
for msg in st.session_state.messages:
    if msg.content:
        if isinstance(msg, SystemMessage):
            st.chat_message("system").write(msg.content)
        elif isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        elif isinstance(msg, ToolMessage):
            st.chat_message("tool").write(msg.content)


# 사용자 입력 처리
if prompt := st.chat_input():
    st.chat_message("user").write(prompt)  # 사용자 메시지 출력
    st.session_state.messages.append(HumanMessage(prompt))  # 사용자 메시지 저장

    response = get_ai_response(st.session_state["messages"])

    result = st.chat_message("assistant").write_stream(response)  # AI 메시지 출력

# 질문 예시:
# 부산은 지금 몇시야?
# 테슬라는 한달 전에 비해 주가가 올랐나 내렸나?