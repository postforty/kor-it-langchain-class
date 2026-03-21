import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

# API 키 설정
load_dotenv(override=True)

# 1. 도구(Tool) 정의
@tool
def write_file_tool(filename: str, content: str) -> str:
    """파일을 지정된 경로에 작성합니다. (이름: write_file)"""
    # 실제 파일 작성을 수행할 수도 있지만, 여기서는 메시지만 반환합니다.
    print(f"\n[💾 파일 저장] 파일명: {filename} | 내용 요약: {content[:20]}...")
    return f"파일 '{filename}'에 내용이 성공적으로 기록되었습니다."

@tool
def execute_sql_tool(query: str) -> str:
    """데이터베이스에서 SQL 쿼리를 실행합니다. (이름: execute_sql)"""
    print(f"\n[🗄️ SQL 실행] 쿼리: {query}")
    return f"쿼리 '{query}'가 실행되었습니다. (영향을 받은 행: 1개)"

@tool
def read_data_tool(source: str) -> str:
    """지정된 소스에서 데이터를 읽어옵니다. (이름: read_data)"""
    print(f"\n[📖 데이터 읽기] 소스: {source}")
    return f"'{source}'로부터 데이터를 성공적으로 불러왔습니다: [샘플 데이터]"

tools = [write_file_tool, execute_sql_tool, read_data_tool]

# 2. 모델 설정
# 노트북과 동일하게 gemini-2.5-flash 사용 (또는 사용 가능한 최신 모델)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 3. 메모리(Checkpointer) 설정
memory = InMemorySaver()

# 4. 에이전트 생성
agent = create_agent(
    model=llm,
    tools=tools,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "write_file_tool": True,  # 승인, 수정, 거절(approve, edit, reject) 가능
                "execute_sql_tool": {"allowed_decisions": ["approve", "reject"]},  # 승인, 거절(approve, reject) 가능
                "read_data_tool": False,  # 사용자 승인 없이 즉시 실행
            },
            description_prefix="도구 실행 승인이 대기 중입니다",
        ),
    ],
    checkpointer=memory,
    system_prompt="모든 답변은 한국어로 작성해주세요. 파일을 쓰거나 SQL을 실행할 때는 도구를 사용하세요."
)

def handle_interrupt(result, config):
    """인터럽트 상황을 처리하는 함수"""
    interrupt_item = result["__interrupt__"][0]
    # Interrupt 객체인 경우 value 속성 사용, 딕셔너리인 경우 그대로 사용
    interrupt_data = interrupt_item.value if hasattr(interrupt_item, 'value') else interrupt_item
    
    # 첫 번째 액션 요청 가져오기
    action_request = interrupt_data["action_requests"][0]
    tool_name = action_request["name"]
    current_args = action_request.get("args", {})
    
    # 허용된 결정 사항 확인
    review_config = next((rc for rc in interrupt_data["review_configs"] if rc["action_name"] == tool_name), {})
    allowed_decisions = review_config.get("allowed_decisions", ["approve", "edit", "reject"])
    
    print(f"\n⚠️  [검토 필요 - Human-In-The-Loop]")
    print(f"도구: {tool_name}")
    print(f"인자: {current_args}")
    
    options = []
    if "approve" in allowed_decisions: options.append("1: 승인")
    if "edit" in allowed_decisions: options.append("2: 수정")
    if "reject" in allowed_decisions: options.append("3: 거절")
    
    prompt_text = f"\n어떻게 하시겠습니까? ({' / '.join(options)}) : "
    choice = input(prompt_text).strip()
    
    if choice == "1" and "approve" in allowed_decisions:
        print(">> 승인되었습니다. 실행을 재개합니다.")
        return agent.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config
        )
    elif choice == "2" and "edit" in allowed_decisions:
        print("\n[수정 모드]")
        new_args = current_args.copy()
        for key, val in current_args.items():
            new_val = input(f" - {key} 수정 (엔터 시 유지: '{val}'): ").strip()
            if new_val:
                new_args[key] = new_val
        
        edited_action = {
            "name": tool_name,
            "args": new_args
        }
        print(">> 내용을 수정하여 실행을 재개합니다.")
        return agent.invoke(
            Command(resume={"decisions": [{"type": "edit", "edited_action": edited_action}]}),
            config=config
        )
    elif choice == "3" and "reject" in allowed_decisions:
        reason = input(">> 거절 사유를 입력하세요: ")
        print(">> 요청을 거절하고 에이전트에게 피드백을 전달합니다.")
        return agent.invoke(
            Command(resume={"decisions": [{"type": "reject", "message": reason}]}),
            config=config
        )
    else:
        print("잘못된 선택입니다. 처리를 중단합니다.")
        return result

def run_interactive_agent():
    print("=== LangGraph HITL 실습 (03_hitl.py) ===")
    print("사용 가능한 도구: write_file_tool, execute_sql_tool, read_data_tool")
    print("종료하려면 'exit' 또는 'quit'를 입력하세요.")
    
    thread_id = "interactive_thread_1"
    config = {"configurable": {"thread_id": thread_id}}
    
    while True:
        user_input = input("\n[사용자 입력] : ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        
        if not user_input:
            continue
            
        # 초기 실행
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )
        
        # 루프를 돌며 모든 인터럽트가 해소될 때까지 처리
        while "__interrupt__" in result and result["__interrupt__"]:
            result = handle_interrupt(result, config)
            
        # 최종 결과 출력
        if "messages" in result and result["messages"]:
            last_msg = result["messages"][-1]
            if last_msg.type == "ai":
                content = last_msg.content
                if isinstance(content, list):
                    content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
                print(f"\n[AI] : {content}")

if __name__ == "__main__":
    run_interactive_agent()
