from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()

client = genai.Client()

# Automatic Chain-of-Thought (Auto-CoT)
# 사람이 직접 예시(Demonstrations)를 작성하는 번거로움을 줄이기 위해
# LLM을 활용하여 자동으로 추론 체인을 생성하는 기법입니다.

# Auto-CoT의 2단계 과정:
# 1) 질문 클러스터링(Question Clustering): 주어진 데이터셋의 질문들을 몇 개의 클러스터로 분할합니다.
# 2) 예시 샘플링(Demonstration Sampling): 각 클러스터에서 대표 질문을 선택하고, 
#    Zero-Shot-CoT("Let's think step by step")를 사용하여 추론 체인을 생성하여 예시로 사용합니다.

# 1단계: Zero-shot CoT를 사용해 '예시 답안(추론 체인)'을 자동으로 생성합니다.
seed_prompt = """
Q: 4, 8, 9, 15, 12, 2, 1 중 홀수들의 합이 짝수인가요?
A: 차근차근 단계별로 생각해보세요.
"""
generated_example = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=seed_prompt
).text

# 2단계: 위에서 AI가 만든 '자동 예시'를 Few-shot으로 넣어 진짜 문제를 풉니다.
# 이것이 사람이 예시를 쓰지 않고 AI가 스스로 예시를 만드는 'Auto'의 핵심입니다.
final_prompt = f"""
질문과 풀이 과정 예시입니다:
Q: 4, 8, 9, 15, 12, 2, 1 중 홀수들의 합이 짝수인가요?
A: {generated_example}

이제 다음 질문에 답하세요:
Q: 15, 32, 5, 13, 82, 7, 1 중 홀수들의 합이 짝수인가요?
A:
"""

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=final_prompt
)

print(response.text)
