from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splitted_docs = splitter.split_documents(pages)

print(splitted_docs[0].page_content)
print("---")
print(splitted_docs[1].page_content)