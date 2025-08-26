from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# 문서 로드
loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
pages = loader.load()

# 문서 분할
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(pages)

# 임베딩 생성
# embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key) # 이전 모델인 embedding-001사용시 오류 발생: Error embedding content: 429 You exceeded your current quota, please check your plan and billing details.
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=gemini_api_key)
embeddings = embeddings_model.embed_documents(
    [chunk.page_content for chunk in chunks]
)

# # 임베딩 생성 (순차적 처리)
# import time
# embeddings = []
# for chunk in chunks:
#     try:
#         # 단일 문서 임베딩 요청
#         embedding = embeddings_model.embed_documents([chunk.page_content])
#         embeddings.extend(embedding)
        
#         # 요청 간 1초 지연
#         time.sleep(1) 
#     except Exception as e:
#         print(f"Error processing chunk: {e}")
#         # 오류 발생 시 대기 시간 증가 또는 재시도 로직 추가 가능
#         time.sleep(5)

print(embeddings)