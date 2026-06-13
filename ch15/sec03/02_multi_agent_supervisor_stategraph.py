import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults 
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from langgraph_supervisor import create_supervisor

# 환경 변수 로드
load_dotenv()

# ==============================================================================
# 1. 도구(Tools) 정의
# ==============================================================================
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
    wrapper = DuckDuckGoSearchAPIWrapper(time=search_period)
    print('\n----- WEB SEARCH -----')
    print(query)
    print(search_period)

    search = DuckDuckGoSearchResults(
        api_wrapper=wrapper,
        results_separator=';\n'
    )

    searched = search.invoke(query)
    for i, result in enumerate(searched.split(';\n')):
        print(f'{i+1}. {result}')
    
    return searched

@tool
def add(a: float, b: float):
    """Add two numbers."""
    return a + b

@tool
def multiply(a: float, b: float):
    """Multiply two numbers."""
    return a * b

@tool
def divide(a: float, b: float):
    """Divide two numbers."""
    return a / b

# ==============================================================================
# 2. StateGraph를 이용한 커스텀 에이전트 생성 함수
# ==============================================================================
def create_custom_agent(model_name: str, tools: list, system_prompt: str, agent_name: str):
    """
    create_react_agent를 대체하기 위해 직접 StateGraph를 구성하여 에이전트를 생성하는 함수.
    """
    model = init_chat_model(model_name)
    model_with_tools = model.bind_tools(tools)
    
    def call_model(state: MessagesState):
        messages = state["messages"]
        if system_prompt:
            # 시스템 프롬프트가 존재하면 메시지 리스트의 맨 앞에 추가합니다.
            sys_msg = SystemMessage(content=system_prompt)
            invoke_messages = [sys_msg] + messages
        else:
            invoke_messages = messages
            
        response = model_with_tools.invoke(invoke_messages)
        return {"messages": [response]}
        
    def should_continue(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        # 모델의 응답에 tool_calls가 있으면 tools 노드로 이동, 없으면 종료
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")
    
    # 컴파일 시 에이전트의 이름을 지정합니다 (supervisor가 에이전트 이름으로 식별함)
    return workflow.compile(name=agent_name)

# ==============================================================================
# 3. 워커(Worker) 에이전트 생성
# ==============================================================================
research_agent = create_custom_agent(
    model_name="google_genai:gemini-3.1-flash-lite",
    tools=[get_web_search],
    system_prompt=(
        "당신은 리서치 에이전트입니다.\n\n"
        "지시사항:\n"
        "- 리서치 관련 작업만 수행하고, 수학 계산은 절대 하지 마세요.\n"
        "- 작업을 완료한 후에는 감독관(supervisor)에게 직접 응답하세요.\n"
        "- 작업 결과만 응답하고, 다른 텍스트는 포함하지 마세요."
    ),
    agent_name="research_agent"
)

math_agent = create_custom_agent(
    model_name="google_genai:gemini-3.1-flash-lite",
    tools=[add, multiply, divide],
    system_prompt=(
        "당신은 수학 에이전트입니다.\n\n"
        "지시사항:\n"
        "- 수학 관련 작업만 수행하세요.\n"
        "- 작업을 완료한 후에는 감독관(supervisor)에게 직접 응답하세요.\n"
        "- 작업 결과만 응답하고, 다른 텍스트는 포함하지 마세요."
    ),
    agent_name="math_agent"
)

# ==============================================================================
# 4. Supervisor 생성 (langgraph-supervisor 활용)
# ==============================================================================
supervisor = create_supervisor(
    model=init_chat_model("google_genai:gemini-3.1-flash-lite"),
    agents=[research_agent, math_agent],
    prompt=(
        "당신은 두 에이전트를 관리하는 감독관입니다:\n"
        "- 리서치 에이전트. 리서치 관련 작업은 이 에이전트에게 할당하세요.\n"
        "- 수학 에이전트. 수학 관련 작업은 이 에이전트에게 할당하세요.\n"
        "한 번에 하나의 에이전트에게만 작업을 할당하고, 여러 에이전트를 병렬로 호출하지 마세요.\n"
        "어떤 작업도 직접 수행하지 마세요."
    ),
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()

# ==============================================================================
# 5. 테스트 실행
# ==============================================================================
if __name__ == "__main__":
    # LangGraph 상태(State)에서 반환된 다양한 형태의 메시지 데이터를 LangChain의 표준 BaseMessage 객체로 변환하고 통일시키기 위함
    # convert_to_messages를 거치면 모든 데이터가 LangChain의 BaseMessage 객체로 통일되므로, 안전하게 pretty_repr()(예쁘게 출력해주는 기능) 등의 내장 메서드를 사용할 수 있게 됨.
    from langchain_core.messages import convert_to_messages

    def pretty_print_message(message, indent=False):
        pretty_message = message.pretty_repr(html=True)
        if not indent:
            print(pretty_message)
            return

        indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
        print(indented)

    def pretty_print_messages(update, last_message=False):
        is_subgraph = False
        if isinstance(update, tuple):
            ns, update = update
            if len(ns) == 0:
                return
            graph_id = ns[-1].split(":")[0]
            print(f"Update from subgraph {graph_id}:")
            print("\n")
            is_subgraph = True

        for node_name, node_update in update.items():
            update_label = f"Update from node {node_name}:"
            if is_subgraph:
                update_label = "\t" + update_label
            
            print(update_label)
            print("\n")

            messages = convert_to_messages(node_update["messages"])
            if last_message:
                messages = messages[-1:]

            for m in messages:
                pretty_print_message(m, indent=is_subgraph)
            print("\n")
            
    print("================== [TEST RUN] ==================")
    # 리서치와 수학 에이전트가 모두 필요한 복합 작업 요청 테스트
    test_query = "부산광역시 시장은 누구인지 검색하고, 그 이름의 글자 수에 10을 더하고 2를 곱한 값을 계산해줘."
    
    for chunk in supervisor.stream(
        {"messages": [{"role": "user", "content": test_query}]},
        subgraphs=True
    ):
        pretty_print_messages(chunk)
