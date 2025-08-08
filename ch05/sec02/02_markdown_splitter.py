from langchain_text_splitters import (
Language,
RecursiveCharacterTextSplitter,
)

from langchain_community.document_loaders import TextLoader

loader = TextLoader('../README.md', encoding='utf-8')
docs = loader.load()

# 마크다운 구조를 인지하는 분할 규칙
# - 마크다운 전용 구분자(코드펜스, 수평선, 헤딩, 리스트, 문단 등) 우선 분할
# - 헤딩, 코드블록, 리스트 경계를 보존해 의미 단위로 깔끔히 분할
md_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN, chunk_size=60, chunk_overlap=0
)

md_docs = md_splitter.split_documents(
docs)

print(md_docs[0].page_content)
print("---")
print(md_docs[1].page_content)
print("---")
print(md_docs[2].page_content)

