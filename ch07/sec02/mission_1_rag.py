# Mission 1: PDF Loader, Text Splitter, and FAISS Vectorstore
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

def load_and_parse_pdf_implement(pdf_path, embeddings, db_path):
    # 1. PDF 로드 (하나의 객체로 로드됨)
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    # 2. 텍스트 분할 (청크 크기 1000, 겹침 100)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    # 3. 벡터스토어 생성 및 로컬 저장
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(db_path)
    
    # 전체 컨텍스트 반환 (퀴즈 생성용)
    full_context = "\n".join([doc.page_content for doc in docs])
    return vectorstore, full_context

# (테스트 코드 생략)
