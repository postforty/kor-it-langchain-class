from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# 문서 로드
loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
documents = loader.load()

# 문서 분할
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
splitted_documents = text_splitter.split_documents(documents)

# 임베딩 모델 준비
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=gemini_api_key,
)

# # FAISS 벡터스토어 생성 및 저장
# vectorstore = FAISS.from_documents(splitted_documents, embedding_model)
# vectorstore.save_local("faiss_index")

# # 벡터스토어 재로딩
# reloaded_store = FAISS.load_local(
#     "faiss_index",
#     embedding_model,
#     allow_dangerous_deserialization=True,
# )

# FAISS 벡터스토어가 존재하는 경우에는 덮어쓰기 하지 않고 로드
FAISS_INDEX_PATH = "faiss_index"

if os.path.exists(FAISS_INDEX_PATH):
    print(f"FAISS 인덱스 {FAISS_INDEX_PATH}를 로드합니다.")
    reloaded_store = FAISS.load_local(
        FAISS_INDEX_PATH,
        embedding_model,
        allow_dangerous_deserialization=True,
    )
else:
    print(f"FAISS 인덱스 {FAISS_INDEX_PATH}가 없으므로 생성합니다.")
    # 문서 로드
    loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
    documents = loader.load()

    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splitted_documents = text_splitter.split_documents(documents)

    # FAISS 벡터스토어 생성 및 저장
    vectorstore = FAISS.from_documents(splitted_documents, embedding_model)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"FAISS 인덱스를 {FAISS_INDEX_PATH}에 저장했습니다.")

# 예시 질의
query = "본 연구에서 Private LLM 구축을 위해 수집한 문서의 총 페이지 수와 문서 유형별 비율은 어떻게 되나요?"
# query = "Advance RAG 기법이 임상시험 데이터 분석에서 수행하는 주요 역할은 무엇인가요?"
# query = "본 연구에서 Private LLM 성능을 평가하기 위해 사용한 지표 3가지는 무엇인가요?"
# query = "국내에서 LLM을 임상시험에 적용한 대표적인 기관과 그 적용 사례를 2가지 이상 말해보세요."
# query = "ROUGE 평가에서 Private LLM과 ChatGPT의 Recall 값은 각각 얼마였나요?"

# results = reloaded_store.similarity_search(query, k=3) # k는 유사도 검색에서 반환할 상위 문서 개수(top‑k)
results = reloaded_store.similarity_search(query, k=5)

for idx, doc in enumerate(results, start=1):
    print(f"[결과 {idx}]\n" + doc.page_content[:300])
    print("---")