from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState

from dotenv import load_dotenv
load_dotenv()

# 1. 모델 초기화
model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    temperature=0
)

# 2. Node 정의
def chat_node(state: MessagesState):
    response = model.invoke(
        state["messages"]
    )
    return {"messages": [response]}

# 3. Graph 생성
graph_builder = StateGraph(MessagesState)

# 4. Graph에 Node 추가
graph_builder.add_node("chat", chat_node)

# 5. Edge 추가하여 Node 연결
graph_builder.add_edge(START, "chat")
graph_builder.add_edge("chat", END)

# 6. Graph를 실행 가능한 형태로 컴파일
graph = graph_builder.compile()


# 7. 대화형 챗봇 실행 함수
def run_chatbot():
    print("Chatbot 시작! (종료: exit)")

    state: MessagesState = {"messages": []}

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot 종료!")
            break

        if not user_input:
                continue

        # 사용자 메시지를 state에 추가
        user_msg = HumanMessage(content=user_input)
        state["messages"].append(user_msg)

        # LangGraph 실행
        result_state = graph.invoke(state)

        # 새로 추가된 AI 메시지 가져오기
        new_messages = result_state["messages"]
        ai_msg = new_messages[-1]  # 마지막 메시지가 방금 생성된 응답

        print(f"AI: {ai_msg.content}")

        # 상태 업데이트 (AI 메시지도 기록)
        state["messages"].append(ai_msg)


if __name__ == "__main__":
    run_chatbot()
