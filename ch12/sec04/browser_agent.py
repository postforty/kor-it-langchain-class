from typing import List, Annotated, TypedDict
from langchain_core.messages import BaseMessage, FunctionMessage, HumanMessage
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool  # Tool 데코레이터만 유지
import json
import asyncio
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from page_analyzer import PageAnalyzer
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
load_dotenv()


class AgentState(TypedDict):
    driver: WebDriver
    chat_history: List[BaseMessage]
    current_url: str
    scratchpad: List[BaseMessage]
    user_input: str  # human_intervention에서 사용


@tool
def navigate_to_url(url: str, **kwargs) -> str:  # 시그니처 수정
    """브라우저를 지정된 URL로 이동시킵니다."""
    driver = kwargs['driver']
    driver.get(url)
    return f"브라우저가 {url}로 이동했습니다."


@tool
def click_element(selector: str, **kwargs) -> str:  # 시그니처 수정
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
def type_text(selector: str, text: str, **kwargs) -> str:  # 시그니처 수정
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
def get_page_content(**kwargs) -> str:  # 시그니처 수정
    """현재 페이지의 전체 HTML 콘텐츠를 반환합니다."""
    driver = kwargs['driver']
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # 스크립트와 스타일 태그 제거
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    # 여러 개의 빈 줄을 하나의 빈 줄로 대체하고 양 끝 공백 제거
    return "\\n".join(filter(lambda line: line.strip(), text.splitlines()))


@tool
def analyze_page_elements(query: str, **kwargs) -> str:
    """페이지 분석 에이전트를 사용하여 특정 요소를 찾고 CSS 셀렉터를 생성합니다."""
    driver = kwargs['driver']

    # 현재 페이지의 HTML 콘텐츠 가져오기
    html_content = driver.page_source

    # 전역 페이지 분석 에이전트 사용
    result = page_analyzer.run(query=query, html_content=html_content)

    if result.get("selector"):
        selector = result["selector"]
        elements_count = len(result.get("extracted_elements", []))
        return f"CSS 셀렉터 '{selector}'를 생성했습니다. {elements_count}개의 요소를 찾았습니다."
    else:
        return f"'{query}'에 해당하는 요소를 찾을 수 없습니다."


@tool
def extract_html_elements(query: str, **kwargs) -> str:
    """페이지 분석 에이전트를 사용하여 특정 요소를 찾고 HTML 요소를 추출하여 반환합니다."""
    driver = kwargs['driver']

    # 현재 페이지의 HTML 콘텐츠 가져오기
    html_content = driver.page_source

    # 전역 페이지 분석 에이전트 사용
    result = page_analyzer.run(query=query, html_content=html_content)

    if result.get("selector") and result.get("extracted_elements"):
        selector = result["selector"]
        extracted_elements = result["extracted_elements"]

        response = f"'{query}'에 해당하는 요소를 찾았습니다.\n"
        response += f"CSS 셀렉터: {selector}\n"
        response += f"추출된 요소 개수: {len(extracted_elements)}개\n\n"

        # 각 요소의 HTML을 출력
        for i, element_html in enumerate(extracted_elements, 1):
            response += f"=== 요소 {i} ===\n"
            response += element_html
            response += "\n\n"

        return response
    else:
        return f"'{query}'에 해당하는 요소를 찾을 수 없습니다."


@tool
def smart_click(query: str, **kwargs) -> str:
    """페이지 분석 에이전트를 사용하여 요소를 찾고 클릭합니다."""
    driver = kwargs['driver']

    # 전역 페이지 분석 에이전트로 셀렉터 생성
    result = page_analyzer.run(query=query, html_content=driver.page_source)

    if not result.get("selector"):
        return f"'{query}'에 해당하는 요소를 찾을 수 없습니다."

    selector = result["selector"]

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        ).click()
        return f"'{query}'에 해당하는 요소 (셀렉터: '{selector}')를 클릭했습니다."
    except Exception as e:
        return f"요소 클릭 실패 (셀렉터: '{selector}'): {e}"


@tool
def smart_type(query: str, text: str, **kwargs) -> str:
    """페이지 분석 에이전트를 사용하여 입력 필드를 찾고 텍스트를 입력합니다."""
    driver = kwargs['driver']

    # 전역 페이지 분석 에이전트로 셀렉터 생성
    result = page_analyzer.run(query=query, html_content=driver.page_source)

    if not result.get("selector"):
        return f"'{query}'에 해당하는 입력 필드를 찾을 수 없습니다."

    selector = result["selector"]

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        element.clear()  # 기존 텍스트 지우기
        element.send_keys(text)
        return f"'{query}'에 해당하는 입력 필드 (셀렉터: '{selector}')에 '{text}'를 입력했습니다. 다음 단계로 검색 버튼을 클릭하거나 Enter 키를 눌러야 합니다."
    except Exception as e:
        return f"텍스트 입력 실패 (셀렉터: '{selector}', 텍스트: '{text}'): {e}"


@tool
def press_enter(query: str, **kwargs) -> str:
    """페이지 분석 에이전트를 사용하여 입력 필드를 찾고 Enter 키를 누릅니다."""
    from selenium.webdriver.common.keys import Keys
    driver = kwargs['driver']

    # 전역 페이지 분석 에이전트로 셀렉터 생성
    result = page_analyzer.run(query=query, html_content=driver.page_source)

    if not result.get("selector"):
        return f"'{query}'에 해당하는 입력 필드를 찾을 수 없습니다."

    selector = result["selector"]

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        element.send_keys(Keys.RETURN)
        return f"'{query}'에 해당하는 입력 필드 (셀렉터: '{selector}')에서 Enter 키를 눌렀습니다."
    except Exception as e:
        return f"Enter 키 입력 실패 (셀렉터: '{selector}'): {e}"


# LLM 초기화
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
# llm = ChatOpenAI(model="gpt-4o", temperature=0)

# PageAnalyzer 인스턴스를 한 번만 생성 (그래프 시각화도 이때 실행됨)
page_analyzer = PageAnalyzer()

# Selenium 도구들을 LangChain Tool 객체로 래핑합니다.


@tool
def analyze_and_execute_instruction(instruction: str, **kwargs) -> str:
    """
    지시사항 분석 에이전트를 사용하여 고수준 지시사항을 분석하고 실행 계획을 생성합니다.

    Args:
        instruction: 사용자의 자연어 지시사항
        **kwargs: driver 등 추가 매개변수

    Returns:
        str: 분석 결과 및 생성된 실행 계획 요약
    """
    driver = kwargs['driver']

    try:
        from instruction_analyzer import InstructionAnalyzer

        print(f"🧠 지시사항 분석 에이전트 실행: '{instruction}'")

        # 현재 페이지 정보 수집
        current_url = driver.current_url
        html_content = driver.page_source

        # 지시사항 분석 에이전트 실행
        analyzer = InstructionAnalyzer()
        result = analyzer.analyze_instruction(
            instruction, html_content, current_url)

        # 결과 요약 생성
        processing_stage = result.get('processing_stage', 'unknown')
        execution_steps = result.get('execution_steps', [])
        is_approved = result.get('is_approved', False)
        validation_errors = result.get('validation_errors', [])

        summary = f"분석 완료 - 단계: {processing_stage}"

        if execution_steps:
            summary += f", 실행 계획: {len(execution_steps)}단계"

            # 주요 단계들 요약
            step_summary = []
            for step in execution_steps[:3]:  # 처음 3단계만
                step_desc = f"{step.action_type.value}({step.target_description})"
                step_summary.append(step_desc)

            if step_summary:
                summary += f" [{' → '.join(step_summary)}"
                if len(execution_steps) > 3:
                    summary += f" + {len(execution_steps) - 3}개 추가"
                summary += "]"

        if validation_errors:
            summary += f", 오류: {len(validation_errors)}개"

        if is_approved:
            summary += ", 승인됨"
        else:
            summary += ", 검토 필요"

        # 글로벌 상태에 결과 저장 (다른 도구들이 사용할 수 있도록)
        if not hasattr(driver, '_instruction_analysis_result'):
            driver._instruction_analysis_result = {}
        driver._instruction_analysis_result = result

        return summary

    except Exception as e:
        error_msg = f"지시사항 분석 실패: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


@tool
def get_execution_plan(**kwargs) -> str:
    """
    이전에 분석된 지시사항의 실행 계획을 반환합니다.

    Returns:
        str: 실행 계획 상세 정보
    """
    driver = kwargs['driver']

    try:
        if not hasattr(driver, '_instruction_analysis_result'):
            return "먼저 analyze_and_execute_instruction을 실행해주세요."

        result = driver._instruction_analysis_result
        execution_steps = result.get('execution_steps', [])

        if not execution_steps:
            return "생성된 실행 계획이 없습니다."

        plan_details = f"실행 계획 ({len(execution_steps)}단계):\n"

        for step in execution_steps:
            plan_details += f"{step.step_id}. {step.action_type.value}: {step.target_description}\n"
            if step.parameters:
                plan_details += f"   매개변수: {step.parameters}\n"
            plan_details += f"   예상 결과: {step.expected_outcome}\n"
            if step.dependencies:
                plan_details += f"   의존성: {step.dependencies}\n"
            plan_details += "\n"

        return plan_details.strip()

    except Exception as e:
        return f"실행 계획 조회 실패: {str(e)}"


@tool
def execute_plan_step(step_number: int, **kwargs) -> str:
    """
    지정된 실행 계획 단계를 실행합니다.

    Args:
        step_number: 실행할 단계 번호
        **kwargs: driver 등 추가 매개변수

    Returns:
        str: 단계 실행 결과
    """
    driver = kwargs['driver']

    try:
        if not hasattr(driver, '_instruction_analysis_result'):
            return "먼저 analyze_and_execute_instruction을 실행해주세요."

        result = driver._instruction_analysis_result
        execution_steps = result.get('execution_steps', [])

        # 해당 단계 찾기
        target_step = None
        for step in execution_steps:
            if step.step_id == step_number:
                target_step = step
                break

        if not target_step:
            return f"단계 {step_number}를 찾을 수 없습니다."

        print(f"🎯 단계 {step_number} 실행: {target_step.target_description}")

        # 액션 타입별 실행
        if target_step.action_type.value == "click":
            if target_step.target_selector:
                return click_element(target_step.target_selector, driver=driver)
            else:
                return f"클릭할 요소의 셀렉터가 없습니다: {target_step.target_description}"

        elif target_step.action_type.value == "type":
            if target_step.target_selector and target_step.parameters.get("text"):
                return type_text(target_step.target_selector, target_step.parameters["text"], driver=driver)
            else:
                return f"입력 정보가 부족합니다: {target_step.target_description}"

        elif target_step.action_type.value == "navigate":
            if target_step.parameters.get("url"):
                return navigate_to_url(target_step.parameters["url"], driver=driver)
            else:
                return f"이동할 URL이 없습니다: {target_step.target_description}"

        elif target_step.action_type.value == "wait":
            import time
            duration = target_step.parameters.get(
                "duration", 3) if target_step.parameters else 3
            time.sleep(duration)
            return f"{duration}초 대기 완료"

        elif target_step.action_type.value == "verify":
            # 검증 로직 (현재는 기본 구현)
            if target_step.parameters.get("action") == "press_enter":
                return press_enter(target_step.target_description, driver=driver)
            else:
                return f"검증 완료: {target_step.target_description}"

        else:
            return f"지원하지 않는 액션 타입: {target_step.action_type.value}"

    except Exception as e:
        return f"단계 실행 실패: {str(e)}"


@tool
def execute_full_plan(**kwargs) -> str:
    """
    전체 실행 계획을 순차적으로 실행합니다.

    Returns:
        str: 전체 실행 결과
    """
    driver = kwargs['driver']

    try:
        if not hasattr(driver, '_instruction_analysis_result'):
            return "먼저 analyze_and_execute_instruction을 실행해주세요."

        result = driver._instruction_analysis_result
        execution_steps = result.get('execution_steps', [])
        is_approved = result.get('is_approved', False)

        if not execution_steps:
            return "실행할 계획이 없습니다."

        if not is_approved:
            return "계획이 승인되지 않았습니다. 먼저 검토가 필요합니다."

        print(f"🚀 전체 실행 계획 실행 시작 ({len(execution_steps)}단계)")

        results = []
        failed_steps = []

        for step in execution_steps:
            print(f"  단계 {step.step_id}: {step.target_description}")

            # 의존성 확인
            if step.dependencies:
                unmet_dependencies = [
                    dep for dep in step.dependencies if dep in failed_steps]
                if unmet_dependencies:
                    result_msg = f"의존성 미충족으로 건너뜀 (의존: {unmet_dependencies})"
                    results.append(f"단계 {step.step_id}: {result_msg}")
                    failed_steps.append(step.step_id)
                    continue

            # 단계 실행
            step_result = execute_plan_step(step.step_id, driver=driver)
            results.append(f"단계 {step.step_id}: {step_result}")

            # 실행 실패 확인
            if "실패" in step_result or "오류" in step_result:
                failed_steps.append(step.step_id)

                # 대안 액션 시도
                if step.fallback_actions:
                    print(f"    대안 액션 시도: {step.fallback_actions[0]}")
                    # 간단한 대안 구현 (실제로는 더 복잡할 수 있음)
                    if step.fallback_actions[0] == "retry_click":
                        retry_result = execute_plan_step(
                            step.step_id, driver=driver)
                        results.append(
                            f"단계 {step.step_id} 재시도: {retry_result}")

            # 단계 간 짧은 대기
            import time
            time.sleep(0.5)

        # 결과 요약
        total_steps = len(execution_steps)
        failed_count = len(failed_steps)
        success_count = total_steps - failed_count

        summary = f"실행 완료: {success_count}/{total_steps} 성공"
        if failed_steps:
            summary += f", 실패한 단계: {failed_steps}"

        return f"{summary}\n\n상세 결과:\n" + "\n".join(results)

    except Exception as e:
        return f"전체 계획 실행 실패: {str(e)}"


@tool
def get_analysis_status(**kwargs) -> str:
    """
    현재 지시사항 분석 상태를 반환합니다.

    Returns:
        str: 분석 상태 정보
    """
    driver = kwargs['driver']

    try:
        if not hasattr(driver, '_instruction_analysis_result'):
            return "분석된 지시사항이 없습니다."

        result = driver._instruction_analysis_result

        status_info = []
        status_info.append(
            f"처리 단계: {result.get('processing_stage', 'unknown')}")
        status_info.append(f"세션 ID: {result.get('session_id', 'N/A')}")

        if result.get('parsed_intent'):
            intent = result['parsed_intent']
            status_info.append(f"주요 목표: {intent.primary_goal}")
            status_info.append(f"신뢰도: {intent.confidence_score:.2f}")

        if result.get('execution_steps'):
            status_info.append(f"실행 단계: {len(result['execution_steps'])}개")

        status_info.append(
            f"승인 상태: {'승인됨' if result.get('is_approved') else '미승인'}")

        if result.get('validation_errors'):
            status_info.append(f"검증 오류: {len(result['validation_errors'])}개")

        if result.get('step_by_step_execution'):
            status_info.append("단계별 실행 모드 활성화")

        return "\n".join(status_info)

    except Exception as e:
        return f"상태 조회 실패: {str(e)}"


tools = [navigate_to_url, click_element, type_text, get_page_content,
         analyze_page_elements, extract_html_elements, smart_click, smart_type, press_enter,
         analyze_and_execute_instruction, get_execution_plan, execute_plan_step,
         execute_full_plan, get_analysis_status]  # 지시사항 분석 도구들 추가

llm_with_tools = llm.bind_tools(tools)  # 여기에 도구 바인딩 추가

# # ToolExecutor 설정 (제거)
# tool_executor = ToolExecutor(tools)

# 에이전트 노드: LLM이 다음 동작을 결정합니다.


def run_agent(state: AgentState):
    current_url = state["driver"].current_url
    print(f"현재 URL: {current_url}")

    # 지시사항 분석 결과가 있는지 확인
    has_analysis = hasattr(state["driver"], '_instruction_analysis_result')

    if has_analysis:
        analysis_result = state["driver"]._instruction_analysis_result
        print(f"📋 분석된 지시사항 있음 - 단계: {analysis_result.get('processing_stage')}")

        # 승인된 계획이 있으면 실행 도구들을 우선 제안
        if analysis_result.get('is_approved') and analysis_result.get('execution_steps'):
            print("✅ 승인된 실행 계획 있음 - 실행 도구 사용 권장")
            print("권장 도구: execute_full_plan, execute_plan_step, get_execution_plan")
        elif analysis_result.get('execution_steps'):
            print("⏳ 검토 대기 중인 실행 계획 있음")
            print("권장 도구: get_execution_plan (검토용)")
    else:
        print("💡 지시사항 분석이 필요한 경우 analyze_and_execute_instruction 도구를 사용하세요")

    print("\n사용 가능한 도구:")
    for tool_item in tools:
        print(f"- {tool_item.name}: {tool_item.description}")

    # 지시사항 분석 결과를 컨텍스트에 포함
    context_messages = state["chat_history"] + state["scratchpad"]

    # 분석 결과가 있으면 컨텍스트에 추가
    if has_analysis:
        analysis_result = state["driver"]._instruction_analysis_result
        context_summary = f"""
현재 지시사항 분석 상태:
- 처리 단계: {analysis_result.get('processing_stage')}
- 실행 계획: {len(analysis_result.get('execution_steps', []))}단계
- 승인 상태: {'승인됨' if analysis_result.get('is_approved') else '미승인'}
- 검증 오류: {len(analysis_result.get('validation_errors', []))}개

승인된 계획이 있다면 execute_full_plan 또는 execute_plan_step을 사용하여 실행하세요.
계획을 검토하려면 get_execution_plan을 사용하세요.
"""
        from langchain_core.messages import SystemMessage
        context_messages.append(SystemMessage(content=context_summary))

    agent_outcome = llm_with_tools.invoke(context_messages)
    state["current_url"] = state["driver"].current_url
    return {"scratchpad": state["scratchpad"] + [agent_outcome]}

# 도구 노드: 에이전트가 선택한 도구를 실행합니다.


def run_tools(state: AgentState):
    last_message = state["scratchpad"][-1]
    tool_input = json.loads(
        last_message.additional_kwargs["function_call"]["arguments"])
    tool_name_str = last_message.additional_kwargs["function_call"]["name"]

    print(f"도구 실행: {tool_name_str} (입력: {tool_input})")

    # tools 리스트에서 실제 Tool 객체를 찾습니다.
    tool_obj = next((t for t in tools if t.name == tool_name_str), None)

    if tool_obj is None:
        return {"scratchpad": state["scratchpad"] + [FunctionMessage(content=f"Error: Tool '{tool_name_str}' not found.", name=tool_name_str)]}

    # driver 인스턴스를 tool_input 딕셔너리에 추가합니다.
    tool_input['driver'] = state['driver']

    # 실제 함수 호출, driver를 포함한 모든 인자를 kwargs로 전달
    response = tool_obj.func(**tool_input)
    return {"scratchpad": state["scratchpad"] + [FunctionMessage(content=str(response), name=tool_name_str)]}

# Human-in-the-loop 노드: 사용자로부터 지시사항을 받습니다.


def human_intervention(state: AgentState):
    print(f"\n현재 URL: {state['current_url']}")

    user_instruction = input("지시사항을 입력하세요 (종료하려면 'exit' 입력): ").strip()

    if user_instruction.lower() == "exit":
        return {"user_input": "exit"}
    elif user_instruction:
        # 새로운 지시사항을 채팅 기록에 추가
        return {
            "user_input": "new_instruction",
            "chat_history": state["chat_history"] + [HumanMessage(content=user_instruction)]
        }
    else:
        # 빈 입력인 경우 다시 입력 요청
        return human_intervention(state)


# 그래프 정의
graph = StateGraph(AgentState)

# 노드 추가
graph.add_node("agent", run_agent)
graph.add_node("tools", run_tools)  # run_tools 함수 다시 사용
# graph.add_node("tools", ToolNode(tools)) # ToolNode 제거
graph.add_node("human_intervention", human_intervention)

# 에이전트의 초기 진입점을 설정합니다.
graph.set_entry_point("human_intervention")

# 조건부 에지 함수: 에이전트의 마지막 메시지가 도구 호출인지 확인합니다.


def should_continue(state: AgentState):  # should_continue 함수 복원
    last_message = state["scratchpad"][-1]

    # 스크래치패드가 너무 길어지면 human_intervention으로 이동
    if len(state["scratchpad"]) > 10:
        print("⚠️ 스크래치패드가 너무 길어졌습니다. 사용자 입력을 기다립니다.")
        return "human_intervention"

    # 도구 호출이 있으면 도구 실행
    if "function_call" in last_message.additional_kwargs:
        return "tools"
    else:
        return "human_intervention"


# 에지 추가
graph.add_conditional_edges(
    "agent",
    should_continue,  # tools_condition 대신 should_continue 사용
    {"tools": "tools", "human_intervention": "human_intervention"}  # 조건부 에지 수정
)
graph.add_edge("tools", "agent")  # 도구 실행 후 다시 에이전트로 돌아갑니다.

# human_intervention 이후의 조건부 에지


def should_react_to_human_input(state: AgentState):
    if state["user_input"] == "exit":
        return "__end__"
    elif state["user_input"] == "new_instruction":
        return "agent"  # 새 지시사항으로 에이전트 실행
    else:
        return "agent"  # 기본적으로 에이전트로 돌아갑니다.


graph.add_conditional_edges(
    "human_intervention",
    should_react_to_human_input,
    {"agent": "agent", "__end__": END}
)


# 그래프 컴파일
app = graph.compile()

# 비동기 그래프 시각화 함수


async def save_graph_visualization():
    """그래프 시각화를 비동기로 처리합니다."""
    print("📊 BrowserAgent 그래프 구조 시각화 중...")
    try:
        # 비동기로 그래프 생성
        mermaid_png = await asyncio.to_thread(
            lambda: app.get_graph(xray=True).draw_mermaid_png(
                draw_method=MermaidDrawMethod.PYPPETEER)
        )

        # 파일 저장도 비동기로 처리
        await asyncio.to_thread(
            lambda: _save_png_file(mermaid_png)
        )

        print("✅ BrowserAgent 그래프 시각화 저장: ./sec04/browser_agent_detailed_graph.png")
    except Exception as e:
        print(f"⚠️ BrowserAgent 그래프 시각화 실패: {e}")


def _save_png_file(mermaid_png):
    """PNG 파일 저장 헬퍼 함수"""
    with open("./browser_agent_detailed_graph.png", "wb") as f:
        f.write(mermaid_png)


# 그래프 시각화 실행
if __name__ == "__main__":
    asyncio.run(save_graph_visualization())
