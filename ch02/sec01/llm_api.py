
# 환경변수
# .env 파일은 gitignore에 추가해야 함
# uv add python-dotenv
# https://pypi.org/project/python-dotenv/

# gemini API
# uv add google-genai
# https://ai.google.dev/gemini-api/docs/quickstart?hl=ko

from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="대한민국의 수도는 어디야?"
)

print(response)
print('----')

# Gemini API의 응답에서 텍스트 내용을 추출한다.
print(response.text)

