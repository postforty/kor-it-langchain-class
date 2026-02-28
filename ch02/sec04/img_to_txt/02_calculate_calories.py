import os
from google import genai
from dotenv import load_dotenv

def calculate_calories(image_path):
    """
    주어진 이미지 경로의 음식 사진을 분석하여 칼로리를 계산합니다.
    """
    # 환경 변수 로드
    load_dotenv()

    # 클라이언트 초기화
    client = genai.Client()
    MODEL_ID = "gemini-2.5-flash"
    
    if not os.path.exists(image_path):
         print(f"[오류] 지정한 이미지 파일({image_path})을 찾을 수 없습니다.")
         return

    print("이미지 데이터 전송 중...")
    food_image_file = client.files.upload(file=image_path)
    
    # 영양 및 칼로리 분석을 위한 시스템 프롬프트
    # 암시적 문자열 리터럴 결합(Implicit String Literal Concatenation)
    prompt = (
        "당신은 정밀한 데이터 분석을 수행하는 영양학 전문가입니다. "
        "첨부된 음식 사진을 기반으로 다음 정보를 냉철하고 객관적으로 분석하십시오.\n\n"
        "1. 구성 요소 식별: 사진에 포함된 모든 식재료 목록\n"
        "2. 중량 및 칼로리 추정: 각 구성 요소별 예상 중량(g) 및 추정 칼로리(kcal)\n"
        "3. 총합 계산: 전체 식단의 총 추정 칼로리\n\n"
        "분석 결과는 아래의 표 형식을 반드시 포함하여 가독성 높게 작성하십시오.\n\n"
        "| 구성 요소 | 예상 중량(g) | 추정 칼로리(kcal) |\n"
        "| :--- | :--- | :--- |\n"
        "| 항목 1 | 00g | 00kcal |\n"
        "| **총합** | - | **00kcal** |"
    )

    print("모델 분석 진행 중...")
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            prompt,
            food_image_file,
        ]
    )

    print("\n===============================")
    print("        분석 결과 보고서        ")
    print("===============================\n")
    print(response.text)

if __name__ == "__main__":
    # 분석할 대상 이미지 파일의 경로를 지정하십시오.
    TARGET_IMAGE = "data/food_image.jpg" 
    calculate_calories(TARGET_IMAGE)
