# ! 요약시  Gemini Free Tier 분당 10회 제한 초과로 인한 429 발생

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import LocalFileStore, create_kv_docstore
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=gemini_api_key,
)

# 문서 로드
loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
documents = loader.load()

# 문서 분할
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = text_splitter.split_documents(documents)

# 문서 요약
prompt_text = '다음 문서의 요약을 생성하세요:\n\n{doc}'

prompt = ChatPromptTemplate.from_template(prompt_text)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, google_api_key=gemini_api_key)
summarize_chain = {
    'doc': lambda x: x.page_content} | prompt | llm | StrOutputParser()

summaries = summarize_chain.batch(chunks, {'max_concurrency': 5})

id_key = 'doc_id'

# 문서와 동일한 길이가 필요하므로 summaries에서 chunks로 변경
doc_ids = [str(uuid.uuid4()) for _ in chunks]

# 각 요약은 doc_id를 통해 원본 문서와 연결
summary_docs = [
    Document(page_content=s, metadata={id_key: doc_ids[i]})
    for i, s in enumerate(summaries)
]

# 벡터 저장소(FAISS)에는 요약을 인덱싱하고, 원문은 별도 docstore(InMemory)로 관리
vectorstore = FAISS.from_documents(summary_docs, embeddings_model)

# 파일 기반 문서 저장소 구성
byte_store = LocalFileStore("./docstore")
store = create_kv_docstore(byte_store)

# 원본 문서를 문서 저장소에 저장 (doc_id로 연결)
store.mset(list(zip(doc_ids, chunks)))

# MultiVectorRetriever 구성
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=store,
    id_key=id_key,
)

# 예시 질의
query = "본 연구에서 Private LLM 구축을 위해 수집한 문서의 총 페이지 수와 문서 유형별 비율은 어떻게 되나요?"
# query = "Advance RAG 기법이 임상시험 데이터 분석에서 수행하는 주요 역할은 무엇인가요?"
# query = "본 연구에서 Private LLM 성능을 평가하기 위해 사용한 지표 3가지는 무엇인가요?"
# query = "국내에서 LLM을 임상시험에 적용한 대표적인 기관과 그 적용 사례를 2가지 이상 말해보세요."
# query = "ROUGE 평가에서 Private LLM과 ChatGPT의 Recall 값은 각각 얼마였나요?"

# 벡터 저장소가 요약을 검색
sub_docs = retriever.vectorstore.similarity_search(
    query, k=2)

print('sub docs: ', sub_docs[0].page_content)

print('length of sub docs:\n', len(sub_docs[0].page_content))

# retriever는 더 큰 원본 문서 청크를 반환
retrieved_docs = retriever.invoke(query)

print('length of retrieved docs: ', len(retrieved_docs[0].page_content))