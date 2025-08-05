# uv add pymupdf
import pymupdf
import os

# PDF 논문, 간행물 다운로드
# http://www.riss.kr
# https://www.tta.or.kr/
FILE_PATH = r"data\KCI_FI003153549.pdf"
doc = pymupdf.open(FILE_PATH)

# 전처리 설정
HEADER_HEIGHT = 90
FOOTER_HEIGHT = 0

# 페이지 수 확인
print(len(doc))

# 첫 번째 페이지 확인
print(doc[0])

# 전체 텍스트 추출
full_text = ''

# 각 페이지 전처리
for page in doc:  # 문서 페이지 반복
    clip_rect = pymupdf.Rect(0, HEADER_HEIGHT, page.rect.width, page.rect.height - FOOTER_HEIGHT)
    text = page.get_text(clip=clip_rect)
    full_text += text

print(full_text)

pdf_file_name = os.path.basename(FILE_PATH)
pdf_file_name = os.path.splitext(pdf_file_name)[0]  # 확장자 제거

txt_file_path = f"output/{pdf_file_name}_pymupdf.txt"

with open(txt_file_path, 'w', encoding='utf-8') as f:
    f.write(full_text)
