import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# .env 파일 로드
load_dotenv()

class SmartPetBot:
    def __init__(self, connection_str):
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", temperature=0.7, google_api_key=os.getenv("GEMINI_API_KEY"))

        # [UPDATE] 컬렉션 이름을 변경하여 새로운 실습 환경 분리
        self.vector_store = PGVector(
            collection_name="upsert_history", 
            connection=connection_str,
            embeddings=self.embedding_model
        )
        self.output_parser = StrOutputParser()

        # [UPDATE] '가장 최신 정보'를 강조하는 프롬프트로 수정
        self.prompt = ChatPromptTemplate.from_template(
            """
            당신은 사용자의 반려동물 정보를 잘 기억하는 스마트 펫봇입니다.
            주어진 정보를 바탕으로 질문에 답하세요. 정보가 바뀌었다면 가장 최신 정보를 우선하세요.

            ---
            사용자 정보(가장 최신): {context}
            ---

            질문: {question}
            답변:
            """
        )

    def save_user_info(self, topic, content):
        """특정 주제(topic)에 대한 정보를 벡터 DB에 저장 또는 업데이트(Upsert)합니다."""
        doc = Document(
            page_content=content,
            metadata={"topic": topic}
        )
        # [핵심 변경 사항] topic을 ids로 직접 지정하여 동일한 주제의 데이터가 들어오면 덮어쓰도록 설정합니다.
        self.vector_store.add_documents([doc], ids=[topic])
        print(f"✅ '{topic}' 정보가 최신화되었습니다: {content}")

    def get_user_context(self, question):
        """질문과 관련된 정보를 검색합니다."""
        docs = self.vector_store.similarity_search(question, k=2)
        context = "\n".join([doc.page_content for doc in docs])
        return context

    def run_petbot(self, question):
        # [NEW] 정보 정정 요청을 감지하는 로직 (학습용 예시)
        if "이름은" in question and ("바꿨어" in question or "아니야" in question):
            try:
                new_name = question.split("이름은 ")[1].split("로")[0].replace("'", "").strip()
                self.save_user_info("pet_name", f"사용자의 반려동물 이름은 {new_name}입니다.")
                return f"네! 반려동물 이름을 {new_name}(으)로 성공적으로 변경했습니다. 이제 똑똑히 기억할게요!"
            except:
                pass

        context = self.get_user_context(question)
        chain = (
            {"context": RunnableLambda(lambda x: context), "question": RunnablePassthrough()}
            | self.prompt | self.llm | self.output_parser
        )
        return chain.invoke(question)

# 실행부
if __name__ == "__main__":
    PGVECTOR_ID = os.getenv("PGVECTOR_ID")
    PGVECTOR_PW = os.getenv("PGVECTOR_PW")
    PGVECTOR_HOST = os.getenv("PGVECTOR_HOST", "localhost")
    PGVECTOR_PORT = os.getenv("PGVECTOR_PORT", "5432")
    PGVECTOR_DB = os.getenv("PGVECTOR_DB")

    connection_str = f'postgresql+psycopg://{PGVECTOR_ID}:{PGVECTOR_PW}@{PGVECTOR_HOST}:{PGVECTOR_PORT}/{PGVECTOR_DB}'

    bot = SmartPetBot(connection_str)

    # [UPDATE] 학습 시나리오를 가이드용 주석으로 변환
    """
    --- Upsert 기능 테스트 시나리오 (직접 입력해 보세요) ---
    1단계: "내 고양이 이름이 뭐야?" (초기값 확인)
    2단계: "아니야, 고양이 이름은 초코로 바꿨어." (정보 수정 요청)
    3단계: "이제 내 고양이 이름 다시 말해봐." (업데이트 결과 확인)
    ------------------------------------------------------
    """

    # 테스트 편의를 위한 초기 정보 주입
    bot.save_user_info("pet_name", "사용자의 고양이 이름은 '나비'입니다.")

    # [UPDATE] 대화 인터랙션 루프
    print("\n스마트 펫봇과의 대화를 시작합니다. '종료'를 입력하면 대화가 끝납니다.")
    print("TIP: '이름은 XXX로 바꿨어'라고 입력하면 실시간으로 정보가 업데이트됩니다.")
    
    while True:
        user_question = input("\n사용자: ")
        if user_question == "종료":
            print("대화를 종료합니다.")
            break

        bot_answer = bot.run_petbot(user_question)
        print(f"펫봇: {bot_answer}")
