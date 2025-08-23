from google import genai
from google.genai import types  # 추가
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

# 페르소나를 설정
# system_instruction = "너는 백설공주 이야기 속의 거울이야. 그 이야기 속의 마법 거울의 캐릭터에 부합하게 답변해줘."
system_instruction = "너는 배트맨에 나오는 조커야. 조커의 악당 캐릭터에 맞게 답변해줘"
prompt = "세상에서 누가 제일 아름답니?"

# https://github.com/google-gemini/cookbook
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
