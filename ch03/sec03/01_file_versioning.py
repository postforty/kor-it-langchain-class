import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import load_prompt

# 환경 변수 로드
load_dotenv()

def run_summary(version: str, text: str):
    # 1. 파일 시스템에서 프롬프트 로드 (버전 관리 예시)
    # prompts/summary_v1.yaml 또는 prompts/summary_v2.yaml을 불러옵니다.
    prompt_path = f"prompts/summary_{version}.yaml"
    
    if not os.path.exists(prompt_path):
        print(f"Error: {prompt_path} 파일을 찾을 수 없습니다.")
        return

    prompt_template = load_prompt(prompt_path, encoding="utf-8")
    
    # 2. 모델 초기화 (Gemini)
    llm = init_chat_model("google_genai:gemini-2.5-flash")
    
    # 3. 체인 생성 및 실행
    chain = prompt_template | llm
    
    print(f"\n--- [Summary Version: {version}] ---")
    response = chain.invoke({"text": text})
    print(response.content)

if __name__ == "__main__":
    sample_text = """
    인공지능(AI)은 인간의 학습 능력과 추론 능력, 지각 능력, 자연어 처리 능력 등을 
    컴퓨터 프로그램으로 구현한 기술입니다. 최근에는 딥러닝 기술의 발전으로 
    이미지 인식, 음성 인식, 번역 등 다양한 분야에서 인간 수준의 성능을 보여주고 있습니다.
    특히 거대 언어 모델(LLM)의 등장은 사용자와의 자연스러운 대화를 가능하게 하여 
    다양한 산업 분야에 혁신을 일으키고 있습니다.
    """

    # v1 실행: 한 문장 요약
    run_summary("v1", sample_text)
    
    # v2 실행: 세 가지 불렛 포인트 요약
    run_summary("v2", sample_text)
