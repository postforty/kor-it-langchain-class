from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

system_instruction = "너는 유치원 학생이야. 유치원생처럼 답변해줘."

# 2~5개 예시 사용
prompt = """
    선생님: 참새
    유치원생: 짹짹
    선생님: 말
    유치원생: 히이잉
    선생님: 개구리
    유치원생: 개굴개굴
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

# Anthropic 프롬프트 엔지니어링 참고
# https://docs.anthropic.com/ko/docs/build-with-claude/prompt-engineering/overview
