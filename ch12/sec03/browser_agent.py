from typing import List, Annotated, TypedDict
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool # Tool 데코레이터만 유지
import json
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
load_dotenv()


class AgentState(TypedDict):
    driver: WebDriver
    chat_history: List[BaseMessage]
    current_url: str
    scratchpad: List[BaseMessage]

@tool
def navigate_to_url(url: str, **kwargs) -> str: # 시그니처 수정
    """브라우저를 지정된 URL로 이동시킵니다."""
    driver = kwargs['driver']
    driver.get(url)
    return f"브라우저가 {url}로 이동했습니다."

@tool
def click_element(selector: str, **kwargs) -> str: # 시그니처 수정
    """CSS 선택자를 사용하여 요소를 클릭합니다."""
    driver = kwargs['driver']
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        ).click()
        return f"선택자 '{selector}'를 가진 요소를 클릭했습니다."
    except Exception as e:
        return f"요소 클릭 실패 (선택자: '{selector}'): {e}"

@tool
def type_text(selector: str, text: str, **kwargs) -> str: # 시그니처 수정
    """CSS 선택자를 사용하여 입력 필드에 텍스트를 입력합니다."""
    driver = kwargs['driver']
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        element.send_keys(text)
        return f"선택자 '{selector}'를 가진 입력 필드에 '{text}'를 입력했습니다."
    except Exception as e:
        return f"텍스트 입력 실패 (선택자: '{selector}', 텍스트: '{text}'): {e}"

@tool
def get_page_content(**kwargs) -> str: # 시그니처 수정
    """현재 페이지의 전체 HTML 콘텐츠를 반환합니다."""
    driver = kwargs['driver']
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # 스크립트와 스타일 태그 제거
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    # 여러 개의 빈 줄을 하나의 빈 줄로 대체하고 양 끝 공백 제거
    return "\\n".join(filter(lambda line: line.strip(), text.splitlines()))

# LLM 초기화
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Selenium 도구들을 LangChain Tool 객체로 래핑합니다.
tools = [navigate_to_url, click_element, type_text, get_page_content] # 데코레이터 적용 함수 직접 참조

llm_with_tools = llm.bind_tools(tools) # 여기에 도구 바인딩 추가

# # ToolExecutor 설정 (제거)
# tool_executor = ToolExecutor(tools)

# 에이전트 노드: LLM이 다음 동작을 결정합니다.
def run_agent(state: AgentState):
    current_url = state["driver"].current_url
    print(f"현재 URL: {current_url}")
    print("사용 가능한 도구:")
    for tool_item in tools:
        print(f"- {tool_item.name}: {tool_item.description}")

    agent_outcome = llm_with_tools.invoke(state["chat_history"] + state["scratchpad"])
    state["current_url"] = state["driver"].current_url
    return {"scratchpad": state["scratchpad"] + [agent_outcome]}

# 도구 노드: 에이전트가 선택한 도구를 실행합니다.
def run_tools(state: AgentState):
    last_message = state["scratchpad"][-1]
    tool_input = json.loads(last_message.additional_kwargs["function_call"]["arguments"])
    tool_name_str = last_message.additional_kwargs["function_call"]["name"]

    print(f"도구 실행: {tool_name_str} (입력: {tool_input})")

    # tools 리스트에서 실제 Tool 객체를 찾습니다.
    tool_obj = next((t for t in tools if t.name == tool_name_str), None)

    if tool_obj is None:
        return {"scratchpad": state["scratchpad"] + [FunctionMessage(content=f"Error: Tool '{tool_name_str}' not found.", name=tool_name_str)]}

    # driver 인스턴스를 tool_input 딕셔너리에 추가합니다.
    tool_input['driver'] = state['driver']
    
    response = tool_obj.func(**tool_input) # 실제 함수 호출, driver를 포함한 모든 인자를 kwargs로 전달
    return {"scratchpad": state["scratchpad"] + [FunctionMessage(content=str(response), name=tool_name_str)]}

# Human-in-the-loop 노드: 사용자 개입을 요청합니다.
def human_intervention(state: AgentState):
    print("\n--- Human Intervention Required ---")
    print("에이전트가 다음 단계를 결정하기 전에 당신의 도움이 필요합니다.")
    print("현재 상태:")
    print(f"  URL: {state['current_url']}") # driver.current_url 대신 state['current_url'] 사용
    print(f"  채팅 기록: {state['chat_history']}")
    print(f"  스크래치패드: {state['scratchpad']}")
    print("다음 중 하나를 선택하세요:")
    print("1. 계속 진행 (continue)")
    print("2. 새로운 지침 제공 (new instruction)")
    print("3. 종료 (exit)")
    
    while True:
        choice = input("선택: ").strip().lower()
        if choice == "continue":
            return {"user_input": "continue"}
        elif choice == "new instruction":
            instruction = input("새로운 지침을 입력하세요: ")
            return {"user_input": "new instruction", "chat_history": state["chat_history"] + [HumanMessage(content=instruction)]} # 새 지침 추가
        elif choice == "exit":
            return {"user_input": "exit"}
        else:
            print("잘못된 입력입니다. 'continue', 'new instruction', 'exit' 중 하나를 입력하세요.")

# 그래프 정의
graph = StateGraph(AgentState)

# 노드 추가
graph.add_node("agent", run_agent)
graph.add_node("tools", run_tools) # run_tools 함수 다시 사용
# graph.add_node("tools", ToolNode(tools)) # ToolNode 제거
graph.add_node("human_intervention", human_intervention)

# 에이전트의 초기 진입점을 설정합니다.
graph.set_entry_point("agent")

# 조건부 에지 함수: 에이전트의 마지막 메시지가 도구 호출인지 확인합니다.
def should_continue(state: AgentState): # should_continue 함수 복원
    last_message = state["scratchpad"][-1]
    if "function_call" in last_message.additional_kwargs:
        return "tools"
    else:
        return "human_intervention" # 또는 'agent'로 돌아갈 수도 있습니다.

# 에지 추가
graph.add_conditional_edges(
    "agent",
    should_continue, # tools_condition 대신 should_continue 사용
    {"tools": "tools", "human_intervention": "human_intervention"} # 조건부 에지 수정
)
graph.add_edge("tools", "agent") # 도구 실행 후 다시 에이전트로 돌아갑니다.

# human_intervention 이후의 조건부 에지
def should_react_to_human_input(state: AgentState):
    if state["user_input"] == "continue":
        return "agent"
    elif state["user_input"] == "new instruction":
        instruction = input("새로운 지침을 입력하세요: ")
        return {"user_input": "new instruction", "chat_history": state["chat_history"] + [HumanMessage(content=instruction)]}
    elif state["user_input"] == "exit":
        return END
    else:
        return "agent" # 기본적으로 에이전트로 돌아갑니다. (이 부분은 상황에 따라 조정 가능)

graph.add_conditional_edges(
    "human_intervention",
    should_react_to_human_input,
    {"agent": "agent", "exit": END}
)


# 그래프 컴파일
app = graph.compile()