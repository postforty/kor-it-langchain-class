# LLM API
from google import genai

# 환경 변수
import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash"


def summarize_txt(file_path: str):
    client = genai.Client(api_key=gemini_api_key)

    file_ref = client.files.upload(file=file_path)

    system_prompt = f'''
    이 글을 읽고, 저자의 문제 인식과 주장을 파악하고, 주요 내용을 요약하라.

    작성해야 하는 포맷은 다음과 같다.

    # 제목

    ## 저자의 문제 인식 및 주장 (15문장 이내)

    ## 저자 소개
    '''

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[file_ref, system_prompt]
    )

    return response.text


if __name__ == '__main__':
    file_path = r"output\KCI_FI003153549_pymupdf.txt"

    summary = summarize_txt(file_path)
    print(summary)

    # 파일명만 추출
    file_name = os.path.basename(file_path)
    file_name = os.path.splitext(file_name)[0]  # 확장자 제거

    txt_file_path = f'output/{file_name}_summary.md'

    # 요약된 내용을 파일로 저장
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        f.write(summary)
