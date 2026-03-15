import gradio as gr

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from dotenv import load_dotenv
load_dotenv(override=True)

system_prompt="""당신은 끝말잇기 게임을 진행하는 AI 챗봇입니다.
아래 순서가 있는 목록은 게임 규칙입니다.
당신과 user 의 입력에서 아래 규칙을 반드시 지켜야 합니다.
규칙을 지키지 않은 사람에게 패배를 알린 뒤, 끝말잇기 게임을 종료합니다.
user가 말한 단어의 끝말로 시작하지 못하면 당신의 패배입니다.
user가 승리한 경우에는 "YOU WIN!", user가 패배한 경우에는 "YOU LOSE!"를 출력합니다.

[게임 규칙]
1. 주어진 대화 기록에서 이미 나왔던 단어를 다시 말했을 경우 패배합니다.
2. 두음법칙을 허용합니다. (ex. 리 -> 이, 력 -> 역, 락 -> 낙)
3. 국어사전에 존재하는 단어이자, 명사여야 합니다.
4. 한 글자 단어는 사용하지 않습니다.
5. 아무런 설명 없이, 끝말잇기 단어만 한글로 한 단어만 출력하세요."""

agent = create_agent(
    model="google_genai:gemini-2.5-flash", 
    checkpointer=InMemorySaver(),
    system_prompt=system_prompt,
)

def play_word_chain_game(message, history):
    """끝말잇기 게임 응답 함수"""
    response = agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                {"configurable": {"thread_id": "1"}},
            )
    return response["messages"][-1].content

demo = gr.ChatInterface(
    fn = play_word_chain_game,
    title="🗣️ 끝말잇기 게임",
    description="AI와 함께 끝말잇기 게임을 해보세요! 단어만 입력하면 됩니다."
)

if __name__ == "__main__":
    demo.launch()