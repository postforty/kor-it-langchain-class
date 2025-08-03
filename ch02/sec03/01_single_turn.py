from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

system_instruction = "너는 사용자를 도와주는 상담사야."

while True:
    user_input = input("사용자: ")

    if user_input == "exit":
        break

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            temperature=0.9,
            system_instruction=system_instruction),
        contents=user_input
    )
    print("AI: " + response.text)

"""
사용자: 안녕, 내 이름은 김일남이야.
AI: 안녕하세요, 김일남님. 만나 뵙게 되어 반갑습니다. 어떤 일로 저를 찾아오셨나요? 편하게 말씀해주세요. 제가 도울 수 있는 부분이 있다면 최선을 다해 돕겠습니다.

사용자: 내 이름이 뭘까?
AI: 음, 제가 당신의 이름을 알 수 있는 방법은 없네요. 당신이 알려주시면 그때부터는 당신을 그렇게 부를 수 있어요. 당신의 이름이 무엇인가요?

사용자: exit
"""
