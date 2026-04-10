import os
import json
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
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", temperature=0.7)

        # [UPDATE] 컬렉션 이름을 변경하여 새로운 실습 환경 분리
        self.vector_store = PGVector(
            collection_name="upsert_history", 
            connection=connection_str,
            embeddings=self.embedding_model
        )
        self.output_parser = StrOutputParser()

        # [UPDATE] '범용 대화 내용'을 바탕으로 하도록 프롬프트 변경
        self.prompt = ChatPromptTemplate.from_template(
            """
            당신은 사용자와의 모든 대화 내용을 잘 기억하는 스마트 어시스턴트입니다.
            주어진 문맥(과거에 저장된 기억)을 바탕으로 자연스럽게 대답하거나 질문에 답하세요.
            정보가 상충한다면 가장 최신 정보를 우선하세요.

            ---
            관련된 기억(문맥): {context}
            ---

            사용자 입력: {question}
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
        # 1. 질문과 관련된 기존 기억을 벡터 DB에서 검색하여 확인합니다.
        related_docs = self.vector_store.similarity_search(question, k=3)
        existing_context = ""
        for d in related_docs:
            existing_context += f"- Topic ID [{d.metadata.get('topic', 'unknown')}]: {d.page_content}\n"

        # 2. LLM을 사용하여 입력이 새로운 정보인지, 아니면 기존 정보의 업데이트인지 분석합니다.
        intent_prompt = ChatPromptTemplate.from_template(
            """
            사용자의 입력문을 분석하여, 꼭 기억해 두어야 할 '새로운 사실'이거나 혹은 '기존 기억의 정정/수정'인지 판단하세요.
            단순한 질문, 인사, 감탄사 등 보관할 필요가 없는 내용이라면 무시합니다.

            [기존에 저장된 관련 기억들]
            {existing_context}

            [분석 규칙]
            1. 사용자의 입력이 '기존에 저장된 관련 기억들'과 연관되어 있고 이전 내용을 정정하거나 업데이트하는 것이라면:
               - 해당하는 기존 기억의 'Topic ID'를 그대로 topic 필드에 유지하세요. (매우 중요: 일치해야 덮어쓰기 업데이트 됨)
               - content 필드에는 새롭게 업데이트된 내용을 완전한 문장으로 적으세요.
            2. 사용자의 입력이 처음 등장하는 '완전히 새로운 사실(정보)'이라면:
               - 의미를 잘 나타내는 영문 소문자와 언더스코어(_) 조합의 새로운 식별자를 만들어 topic 필드에 넣으세요 (예: user_hobby, fav_movie).
               - content 필드에는 기억해둘 사실을 완전한 문장으로 적으세요.
            3. 사용자의 입력이 단순 질문이나 기억할 필요 없는 대화라면:
               - topic과 content 필드를 모두 빈 문자열("")로 반환하세요.

            [출력 형식]
            반드시 아래 JSON 형식으로만 응답하세요:
            ```json
            {{"topic": "...", "content": "..."}}
            ```

            사용자 입력: {question}
            """
        )

        intent_chain = intent_prompt | self.llm | StrOutputParser()
        intent_result = intent_chain.invoke({
            "existing_context": existing_context if existing_context.strip() else "저장된 관련 기억 없음",
            "question": question
        })

        try:
            # JSON만 파싱
            clean_json = intent_result.replace("```json", "").replace("```", "").strip()
            extracted_info = json.loads(clean_json)
            
            topic = extracted_info.get("topic")
            content = extracted_info.get("content")
            
            # topic이 추출되었다면 기억해야 할 내용이 있다는 뜻
            if topic:
                self.save_user_info(topic, content)
                return f"💡 [시스템 알림] 내용을 메모했습니다! \n- ID(주제): {topic}\n- 내용: {content}"
        except Exception as e:
            # 정상적인 JSON이 아니거나, 파싱 에러 발생 시 단순 응답으로 넘어감
            pass

        # 3. 추출할 정보가 없는 일반적인 질문/대화에 대한 응답 (최신 상태의 컨텍스트를 다시 조회)
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

    # 초기화: 기존 정보가 비어있지 않도록 임의의 정보를 넣어줍니다.
    bot.save_user_info("pet_name", "사용자의 고양이 이름은 '나비'입니다.")

    # [UPDATE] 대화 인터랙션 루프
    print("\n스마트 어시스턴트와의 대화를 시작합니다. ('종료' 입력 시 대화 종료)")
    print("TIP 1: '나 오늘부터 수영 다녀' 처럼 완전 새로운 사실을 말해보세요.")
    print("TIP 2: '나 고양이 이름 초코로 바꿨어' 혹은 '수영 안다니고 헬스 다녀' 처럼 기존과 연관된 정보를 수정해보세요.")
    
    while True:
        user_question = input("\n사용자: ")
        if user_question == "종료":
            print("대화를 종료합니다.")
            break

        bot_answer = bot.run_petbot(user_question)
        print(f"펫봇: {bot_answer}")
