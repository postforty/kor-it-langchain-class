# uv add pymupdf
import pymupdf
import os

# PDF 논문, 간행물 다운로드
# http://www.riss.kr
# https://www.tta.or.kr/
FILE_PATH = r"data\KCI_FI003153549.pdf"
doc = pymupdf.open(FILE_PATH)

print("doc.metadata:", doc.metadata)

# 전처리 설정
# - 불필요한 머리글과 바닥글을 제외
HEADER_HEIGHT = 90
FOOTER_HEIGHT = 0

# 페이지 수 확인
print(len(doc))

# 첫 번째 페이지 확인
print(doc[0])

print("---")

# 전체 텍스트 추출
full_text = ''

# 각 페이지 전처리
for page in doc:
    # 텍스트를 추출할 영역(clip) 정의
    clip_rect = pymupdf.Rect(
        0,  # 왼쪽 x 좌표
        HEADER_HEIGHT,  # 상단 y 좌표 (머리글 높이만큼 제외)
        page.rect.width,  # 오른쪽 x 좌표 (페이지 전체 너비)
        page.rect.height - FOOTER_HEIGHT  # 하단 y 좌표 (바닥글 높이만큼 제외)
    )
    text = page.get_text(clip=clip_rect)
    full_text += text

print(full_text)

pdf_file_name = os.path.basename(FILE_PATH)
pdf_file_name = os.path.splitext(pdf_file_name)[0]  # 확장자 제거

txt_file_path = f"output/{pdf_file_name}_pymupdf.txt"

with open(txt_file_path, 'w', encoding='utf-8') as f:
    f.write(full_text)
