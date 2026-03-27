from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()

loader = PDFPlumberLoader(r"..\data\Employee_Benefits_Guide_2026_v1.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
texts = text_splitter.split_documents(documents)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

vectorstore = FAISS.from_documents(texts, embeddings)

vectorstore.save_local("./faiss_index")