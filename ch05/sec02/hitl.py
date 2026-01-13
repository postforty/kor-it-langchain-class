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
def send_email(recipient: str, content: str) -> str:
    """이메일을 전송합니다."""
    print(f"\n[📧 전송 완료] 수신인: {recipient} | 내용: {content}")
    return "이메일 전송에 성공했습니다."

tools = [send_email]

# 2. 모델 설정
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 3. 메모리(Checkpointer) 설정
memory = InMemorySaver()

# 4. 에이전트 생성 (최신 create_agent 문법)
agent = create_agent(
    model=llm,
    tools=tools,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "send_email": True,  # send_email 도구 호출 시 승인/수정/거절 허용
            },
            description_prefix="도구 실행 승인이 대기 중입니다",
        ),
    ],
    checkpointer=memory,
)

def run_hitl_agent():
    config = {"configurable": {"thread_id": "hitl_1"}}
    
    print("--- 1. 사용자 요청 ---")
    # 이메일 주소를 추가하여 AI가 바로 도구를 호출하게 유도합니다.
    user_input = "팀장님(manager@example.com)께 이번 주 금요일에 연차 쓴다고 공손하게 메일 보내줘."
    print(f"사용자: {user_input}\n")
    
    # 실행
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config
    )
    
    # 최신 메시지 출력 (AI의 생각을 보기 위함)
    if "messages" in result and result["messages"]:
        last_msg = result["messages"][-1]
        content = last_msg.content
        # 리스트 형태의 응답인 경우 텍스트만 추출
        if isinstance(content, list):
            content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
        
        if content:
            print(f"AI 응답: {content}")

    # 인터럽트 발생 여부 확인
    if "__interrupt__" in result and result["__interrupt__"]:
        # 미들웨어에 의해 생성된 인터럽트 정보 가져오기
        interrupt_item = result["__interrupt__"][0]
        interrupt_data = interrupt_item.value if hasattr(interrupt_item, 'value') else interrupt_item

        print(f"\n[데이터 확인]: {interrupt_data}")
        
        # 1. 터미널 출력 데이터에서 첫 번째 액션 요청 추출
        action_request = interrupt_data["action_requests"][0]
        # 2. args 키 참조 (중요: arguments가 아니라 args임)
        current_args = action_request.get("args", {})
        
        print(f"\n⚠️  [검토 필요 - HITL Middleware]")
        print(f"수신인: {current_args.get('recipient')}")
        print(f"현재 내용: {current_args.get('content')}")

        # 사용자 선택
        action = input("\n어떻게 하시겠습니까? (1: 승인 / 2: 수정 / 3: 거절): ").strip()
        
        final_result = None
        if action == "1":
            print(">> 승인되었습니다. 실행을 재개합니다.")
            final_result = agent.invoke(
                Command(resume={"decisions": [{"type": "approve"}]}),
                config=config
            )
                
        elif action == "2":
            new_content = input(">> 수정할 내용을 입력하세요: ")
            print(">> 내용을 수정하여 실행을 재개합니다.")
            # 데이터 구조에 맞게 edited_action 구성
            edited_action = {
                "name": action_request["name"],
                "args": {**current_args, "content": new_content}
            }
            final_result = agent.invoke(
                Command(resume={"decisions": [{"type": "edit", "edited_action": edited_action}]}),
                config=config
            )
                
        elif action == "3":
            reason = input(">> 거절 사유를 입력하세요: ")
            print(">> 요청을 거절하고 에이전트에게 피드백을 전달합니다.")
            final_result = agent.invoke(
                Command(resume={"decisions": [{"type": "reject", "message": reason}]}),
                config=config
            )
            
        # 재개 후 최종 결과 출력
        if final_result and "messages" in final_result:
            last_msg = final_result['messages'][-1]
            content = last_msg.content
            if isinstance(content, list):
                content = " ".join([c.get("text", "") for c in content if isinstance(c, dict)])
            print(f"\n최종 AI 응답: {content}")
    else:
        # 도구 호출(tool_calls)이 있었는지 확인
        has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls
        if not has_tool_calls:
            print("\n(알림: 도구 호출이 발생하지 않아 승인 절차 없이 종료되었습니다.)")
    
    print("\n--- 모든 시퀀스 종료 ---")



if __name__ == "__main__":
    run_hitl_agent()

