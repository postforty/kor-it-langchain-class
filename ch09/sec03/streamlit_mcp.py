
import streamlit as st
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent 
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_mcp_adapters.client import MultiServerMCPClient

from dotenv import load_dotenv
load_dotenv()

st.title("🛠️MCP + 도구 호출 챗봇")
st.caption("MCP 서버 도구(시계, 주식) + 로컬 도구(웹 검색) + 메모리")

# * 세션 상태 초기화 (thread_id 추가)
if "thread_id" not in st.session_state:
    from datetime import datetime
    st.session_state["thread_id"] = str(datetime.now().timestamp())

# * MCP 도구 로드 함수 (캐싱 사용)
@st.cache_resource
def get_mcp_tools():
    async def _load():
        client = MultiServerMCPClient(
            {
                "mcp_tools": {
                    "url": "http://localhost:8000/mcp",
                    "transport": "streamable_http",
                }
            }
        )
        # MCP 서버에서 도구 목록을 가져옵니다.
        tools = await client.get_tools()
        return tools
    
    # 비동기 함수를 동기적으로 실행
    try:
        return asyncio.run(_load())
    except Exception as e:
        st.error(f"MCP 서버 연결 실패: {e}")
        st.error("sec02/mcp_server.py 파일이 실행 중인지 확인해주세요.")
        return []

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "agent" not in st.session_state:
    st.session_state["agent"] = None

def clear_task():
    st.session_state["messages"] = []
    st.session_state["agent"] = None
    from datetime import datetime
    st.session_state["thread_id"] = str(datetime.now().timestamp())
    
with st.sidebar:  
    st.button("대화 초기화", on_click=clear_task)

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
    
def create_graph_agent():
    tools = get_mcp_tools()

    # * 에이전트 생성 및 반환
    return create_agent(
        model="google_genai:gemini-3-flash-preview", 
        tools=tools, 
        checkpointer=InMemorySaver() # * 추가
    )

print_messages()

# 에이전트 초기화 (없거나 리로드 시)
if st.session_state["agent"] is None:
    st.session_state["agent"] = create_graph_agent()

if user_input := st.chat_input("시간, 주식, 뉴스 등에 대해 물어보세요!"):
    if st.session_state["agent"] is not None:
        st.chat_message("user").write(user_input)
        add_message("user", user_input)

        with st.chat_message("assistant"):
            ai_container = st.empty()
            
            with st.status("답변을 생성하고 있습니다...", expanded=True) as status:
                final_state = None
                
                # 에이전트 실행 (비동기)
                # mcp_server.py가 켜져 있어야 정상 동작함
                async def run_agent():
                    last_state = None
                    async for state in st.session_state["agent"].astream(
                        {"messages": [{"role": "user", "content": user_input}]},
                        {"configurable": {"thread_id": st.session_state["thread_id"]}},
                        stream_mode="values"
                    ):
                        last_state = state
                        last_msg = state["messages"][-1]
                        
                        # 도구 호출 로그 표시
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            for tool_call in last_msg.tool_calls:
                                status.write(f"🛠️ `{tool_call['name']}` 도구를 실행 중입니다...")
                    return last_state

                final_state = asyncio.run(run_agent())
                
                status.update(label="답변 완료!", state="complete", expanded=False)

            # 최종 답변 출력
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
