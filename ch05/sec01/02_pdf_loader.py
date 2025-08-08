from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader('../data/KCI_FI003153549.pdf')
pages = loader.load()

print(pages)