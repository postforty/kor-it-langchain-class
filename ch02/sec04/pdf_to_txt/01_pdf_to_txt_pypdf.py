# PyPDF
# - 페이지 내용 및 메타데이터(page 정보 등) 포함

# uv add pypdf
# uv add langchain-community
from langchain_community.document_loaders import PyPDFLoader
import os

# PDF 논문, 간행물 다운로드
# http://www.riss.kr
# https://www.tta.or.kr/
FILE_PATH = r"data\KCI_FI003153549.pdf"
loader = PyPDFLoader(FILE_PATH)
pages = loader.load()

# 페이지 수 확인
print(len(pages))

# 첫 번째 페이지 확인
print(pages[0])

# 전체 텍스트 추출
full_text = ''

for page in pages:  # 문서 페이지 반복
    full_text += page.page_content

print(full_text)

pdf_file_name = os.path.basename(FILE_PATH)
pdf_file_name = os.path.splitext(pdf_file_name)[0]  # 확장자 제거

txt_file_path = f"output/{pdf_file_name}_pypdf.txt"

with open(txt_file_path, 'w', encoding='utf-8') as f:
    f.write(full_text)
