from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

system_instruction = "너는 유치원 학생이야. 유치원생처럼 답변해줘."

prompt = """
    USER: 참새
    MODEL: 짹짹
    USER: 말
    MODEL: 히이잉
    USER: 개구리
    MODEL: 개굴개굴
    USER: 오리
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction),
    contents=prompt
)

print(response)
print('----')

# Gemini API의 응답에서 텍스트 내용을 추출한다.
print(response.text)