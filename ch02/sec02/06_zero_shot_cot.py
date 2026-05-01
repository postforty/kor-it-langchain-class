from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# Gemini 클라이언트를 초기화합니다.
client = genai.Client(api_key=gemini_api_key)

# Zero-shot CoT (Chain-of-Thought) Prompting
# 별도의 예시(Shot) 없이도 "단계별로 생각해보세요(Let's think step by step)"라는 문구만으로 
# 모델의 논리적 추론 능력을 비약적으로 향상시킬 수 있습니다.

# 1. Zero-shot CoT를 적용하지 않은 프롬프트
# gemini-2.5-flash-lite 모델이 추론을 자동으로 진행하기 때문에 실험을 위해 프롬프트에 추론하지 않도록 명시하였음. 
prompt_basic = """
시장에 가서 사과 10개를 샀습니다. 이웃에게 2개, 수리 기사님께 2개를 나누어 주었습니다.
그 후 사과 5개를 더 사고 1개를 먹었습니다. 남은 사과는 총 몇 개인가요? 추론 과정 없이 최종 숫자만 답변하세요.
"""

# 2. Zero-shot CoT를 적용한 프롬프트
prompt_zero_shot_cot = """
시장에 가서 사과 10개를 샀습니다. 이웃에게 2개, 수리 기사님께 2개를 나누어 주었습니다.
그 후 사과 5개를 더 사고 1개를 먹었습니다. 남은 사과는 총 몇 개인가요?

차근차근 단계별로 생각해보세요.
"""

print("--- [Basic Prompt (No CoT)] ---")
response_basic = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt_basic
)
print(response_basic.text)

print("\n--- [Zero-shot CoT Prompting (Let's think step by step)] ---")
response_cot = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt_zero_shot_cot
)
print(response_cot.text)
