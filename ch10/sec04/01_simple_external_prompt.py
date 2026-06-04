import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import load_prompt

# 1. 환경 변수 로드 (API 키 등)
load_dotenv()

print("========================================")
print("Step 4: 외부 프롬프트 로딩 기초 예제")
print("========================================")

# 2. 모델 초기화
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# 3. 외부 YAML 파일에서 프롬프트 로드
# 코드 내부에 프롬프트를 하드코딩하지 않고 외부 파일(.yaml)에서 깔끔하게 읽어옵니다.
prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "greeting.yaml")
print(f"[{prompt_path}] 파일에서 프롬프트를 불러옵니다...\n")
prompt_template = load_prompt(prompt_path, encoding="utf-8")

# 4. 프롬프트 체인 구성
chain = prompt_template | llm

# 5. 실행 및 결과 출력
# (자동화된 시연을 위해 고정된 값을 사용합니다. 실제로는 input()을 받을 수도 있습니다.)
print("사용자: 홍길동")
print("관심 주제: 랭체인 외부 프롬프트 활용법\n")

response = chain.invoke({
    "user_name": "홍길동",
    "topic": "랭체인 외부 프롬프트 활용법"
})

print("--- AI 응답 ---")
print(response.content)
print("----------------")
