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
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=gemini_api_key)
embeddings = embeddings_model.embed_documents(
    [chunk.page_content for chunk in chunks]
)

print(embeddings)