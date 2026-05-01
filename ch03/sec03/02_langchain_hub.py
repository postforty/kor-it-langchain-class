from dotenv import load_dotenv
from langsmith import Client
from langchain.chat_models import init_chat_model

# 환경 변수 로드 (LANGSMITH_API_KEY가 있으면 Hub와 연동됩니다)
load_dotenv()

def run_hub_example():
    # 1. LangSmith Client를 사용하여 프롬프트 가져오기
    # 공식 문서 권장 사항: langchainhub 패키지는 deprecated 되었으므로 langsmith 패키지를 사용합니다.
    client = Client()
    print("LangChain Hub에서 프롬프트를 불러오는 중...")
    prompt = client.pull_prompt("rlm/rag-prompt", dangerously_pull_public_prompt=True)
    
    print("\n--- [Pulled Prompt Template] ---")
    print(prompt)

    # 2. 모델 초기화
    llm = init_chat_model("google_genai:gemini-2.5-flash")

    # 3. 체인 생성 및 실행
    chain = prompt | llm

    # 예시 입력
    context = "랭체인(LangChain)은 LLM 기반 애플리케이션을 구축하기 위한 프레임워크입니다."
    question = "랭체인이 뭐야?"

    response = chain.invoke({"context": context, "question": question})
    
    print("\n--- [Hub Prompt Result] ---")
    print(response.content)

if __name__ == "__main__":
    run_hub_example()
