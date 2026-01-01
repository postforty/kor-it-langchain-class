# multi-turn: 대화 내용을 기억

# LLM API
from google import genai

# 환경 변수
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

# 출처:
# 공식 문서: https://github.com/google-gemini/cookbook
# 경로: quickstarts/Get_started.ipynb
# 전체 경로: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started.ipynb
chat = client.chats.create(model="gemini-2.5-flash")

while True:
    user_input = input("사용자: ")  # 사용자 입력 받기

    if user_input == "종료":  # 사용자가 대화를 종료하려는지 확인
        break

    response = chat.send_message(
        message=user_input
    )

    messages = chat.get_history()
    for message in messages:
        print(f"{message.role}: {message.parts[0].text}")

    print("AI: " + response.text)  # AI 응답 출력

"""
사용자: 안녕? 내 이름은 김일남이야.
AI: 안녕하세요, 김일남님! 만나뵙게 되어 반갑습니다. 무엇을 도와드릴까요?

사용자: 내가 누구게?
AI: 음... 방금 김일남이라고 말씀하셨으니, 김일남님이시겠죠? 😉
"""
