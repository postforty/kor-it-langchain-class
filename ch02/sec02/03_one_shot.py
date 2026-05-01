from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

system_instruction = "너는 유치원 학생이야. 유치원생처럼 답변해줘."

# 1개 예시 사용
prompt = """
    선생님: 참새
    유치원생: 짹짹
    선생님: 오리
    유치원생: 
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
