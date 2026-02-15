from typing import TypedDict, Annotated

from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, add_messages

from dotenv import load_dotenv
load_dotenv()

# 1. 모델 초기화
model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    temperature=0
)

# 2. State 정의 (정석!)
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# 3. Node 정의
def greet(state: State):
    response = model.invoke(
        state["messages"]
    )
    return {"messages": [response]}

def goodbye(state: State):

    human_message = HumanMessage(content="안녕! 잘 가!")
    response = model.invoke(
        state["messages"] + [human_message]
    )
    return {"messages": [human_message, response]}

# 4. Graph 생성
graph = StateGraph(State)

# 5. Graph에 Node 추가
graph.add_node("greet_node", greet)
graph.add_node("goodbye_node", goodbye)

# 6. Edge 추가하여 Node 연결
graph.add_edge(START, "greet_node")
graph.add_edge("greet_node", "goodbye_node")
graph.add_edge("goodbye_node", END)

# 7. Graph를 실행 가능한 형태로 컴파일
app = graph.compile()

# 8. Graph 실행
initial_state: State = {
    "messages": [HumanMessage(content="안녕! 난 김일남이야!")],
}
result = app.invoke(initial_state)
for msg in result["messages"]:
    print(f"[{type(msg).__name__}] {msg.content}")
