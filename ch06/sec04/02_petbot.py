from langchain_core.documents import Document
from langchain_postgres.vectorstores import PGVector
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")


class PetBot:
    def __init__(self, connection_str):
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=gemini_api_key,
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", temperature=0.7, google_api_key=gemini_api_key)

        # PGVector 객체 초기화 (기존 컬렉션을 사용)
        self.vector_store = PGVector(
            collection_name="chat_history",  # 대화 기록을 저장할 컬렉션 이름
            connection=connection_str,
            embeddings=self.embedding_model
        )
        self.output_parser = StrOutputParser()

        # 답변 생성 프롬프트 템플릿
        self.prompt = ChatPromptTemplate.from_template(
            """
            주어진 과거 대화 기록을 참고하여 질문에 답변해 주세요.
            과거 대화 기록이 질문과 관련 없다면 무시하세요.

            ---
            과거 대화 기록: {context}
            ---

            질문: {question}
            답변:
            """
        )

    def save_chat_history(self, question, answer):
        """사용자의 질문과 챗봇의 답변을 벡터 DB에 저장."""
        chat_log = f"사용자: {question}\n챗봇: {answer}"
        doc = Document(page_content=chat_log)
        self.vector_store.add_documents([doc])
        print("대화 기록이 벡터 DB에 저장되었습니다.")

    def get_related_history(self, question):
        """새 질문과 관련된 과거 대화 기록을 검색."""
        # 질문과 가장 유사한 k=3개의 문서(과거 대화)를 검색
        docs = self.vector_store.similarity_search(question, k=3)
        context = "\n".join([doc.page_content for doc in docs])
        return context

    def run_petbot(self, question):
        """챗봇 실행 로직: 검색 -> 답변 생성 -> 기록 저장."""
        # 1. 과거 대화 기록 검색
        context = self.get_related_history(question)
        print("--- 과거 대화 기록 검색 완료 ---")

        # 2. 검색된 기록과 질문을 기반으로 답변 생성
        chain = (
            {
                "context": RunnableLambda(lambda x: context),
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | self.output_parser
        )

        answer = chain.invoke(question)

        # 3. 현재 대화 기록을 벡터 DB에 저장
        self.save_chat_history(question, answer)

        return answer


# 3. 실행 예시
if __name__ == "__main__":
    # DB 연결 정보 설정 (환경 변수 사용)
    PGVECTOR_ID = os.getenv("PGVECTOR_ID")
    PGVECTOR_PW = os.getenv("PGVECTOR_PW")
    PGVECTOR_HOST = os.getenv("PGVECTOR_HOST", "localhost")
    PGVECTOR_PORT = os.getenv("PGVECTOR_PORT", "5432")
    PGVECTOR_DB = os.getenv("PGVECTOR_DB")

    connection_str = f'postgresql+psycopg://{PGVECTOR_ID}:{PGVECTOR_PW}@{PGVECTOR_HOST}:{PGVECTOR_PORT}/{PGVECTOR_DB}'

    # 챗봇 인스턴스 생성
    petbot = PetBot(connection_str)

    # 대화 시작
    print("펫봇과의 대화를 시작합니다. '종료'를 입력하면 대화가 끝납니다.")
    while True:
        user_question = input("사용자: ")
        if user_question.lower() == "종료":
            print("대화를 종료합니다.")
            break

        bot_answer = petbot.run_petbot(user_question)
        print(f"펫봇: {bot_answer}")
