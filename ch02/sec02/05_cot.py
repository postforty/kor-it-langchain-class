from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

# Chain-of-Thought (CoT) Prompting
# 중간 추론 단계를 포함하여 모델이 복잡한 추론 문제를 해결할 수 있도록 돕습니다.
# Few-shot Prompting과 결합하면 더 강력한 성능을 발휘합니다.
# 먼저 "모든 홀수가 무엇인지 찾아내고, 그 합계를 계산하는 과정"이 '생각의 사슬(Chain-of-Thought)'입니다.

prompt = """
이 그룹의 홀수들을 합하면 짝수가 됩니다: 4, 8, 9, 15, 12, 2, 1.
A: 모든 홀수(9, 15, 1)를 더하면 25입니다. 정답은 False입니다.
이 그룹의 홀수들을 합하면 짝수가 됩니다: 17, 10, 19, 4, 8, 12, 24.
A: 모든 홀수(17, 19)를 더하면 36입니다. 정답은 True입니다.
이 그룹의 홀수들을 합하면 짝수가 됩니다: 16, 11, 14, 4, 8, 13, 24.
A: 모든 홀수(11, 13)를 더하면 24입니다. 정답은 True입니다.
이 그룹의 홀수들을 합하면 짝수가 됩니다: 17, 9, 10, 12, 13, 4, 2.
A: 모든 홀수(17, 9, 13)를 더하면 39입니다. 정답은 False입니다.
이 그룹의 홀수들을 합하면 짝수가 됩니다: 15, 32, 5, 13, 82, 7, 1. 
A:
"""

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print("--- [Chain-of-Thought (CoT) Prompting Output] ---")
print(response.text)
