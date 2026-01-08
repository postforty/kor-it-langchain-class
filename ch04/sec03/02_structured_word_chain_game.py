import gradio as gr
from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv

load_dotenv(override=True)

# 1. 구조화된 응답 모델(스키마) 정의
class WordChainResponse(BaseModel):
    """끝말잇기 게임의 응답 구조"""
    word: str = Field(description="에이전트가 제시하는 다음 단어. 게임 종료 시에는 비워둡니다.")
    status: Literal["ongoing", "win", "lose"] = Field(description="게임의 현재 상태 (진행중, 유저 승리, 유저 패배)")
    reason: Optional[str] = Field(description="게임이 종료된 상세 이유 (예: '이미 나온 단어입니다', '명사가 아닙니다')")
    message: str = Field(description="사용자에게 보여줄 최종 메시지 (단어 또는 'YOU WIN!' 등)")

# 시스템 프롬프트 수정 (데이터 구조를 채우는 것에 집중하도록 변경)
system_prompt = """당신은 끝말잇기 게임을 진행하는 AI 챗봇입니다.
지정된 WordChainResponse 형식에 맞춰 응답을 생성해야 합니다.

[게임 규칙]
1. 이미 나왔던 단어 재사용 금지.
2. 두음법칙 허용 (리 -> 이).
3. 명사만 가능.
4. 한 글자 단어 금지.
5. 유저가 규칙을 어기면 status를 'lose'로 하고 이유를 적으세요.
6. 당신이 단어를 잇지 못하면 status를 'win'으로 하세요. 
7. 유저가 승리하면 message에 'YOU WIN!', 패배하면 'YOU LOSE!'를 포함하세요.
"""

agent = create_agent(
    model="google_genai:gemini-2.5-flash", 
    tools=[],
    checkpointer=InMemorySaver(),
    system_prompt=system_prompt,
    response_format=WordChainResponse # 구조화된 출력 적용
)

def play_word_chain_game(message, history):
    # 에이전트 호출
    response = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": "word_chain_1"}},
    )
    
    # 구조화된 데이터 추출
    game_data: WordChainResponse = response["structured_response"]

    print(game_data)
    
    # 화면에 보여줄 텍스트 구성
    if game_data.status == "ongoing":
        return game_data.word
    else:
        # 종료된 경우 사유와 함께 결과 메시지 반환
        return f"{game_data.reason}\n\n{game_data.message}"

demo = gr.ChatInterface(
    fn = play_word_chain_game,
    title="🗣️ 구조화된 끝말잇기 게임",
    description="데이터 모델을 통해 더 정확하게 상태를 관리하는 끝말잇기 AI입니다."
)

if __name__ == "__main__":
    demo.launch()