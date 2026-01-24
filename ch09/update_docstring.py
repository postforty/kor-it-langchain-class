import json

# 노트북 파일 읽기
with open('sec02/01_conditional_tools.ipynb', 'r', encoding='utf-8') as f:
    notebook = json.load(f)

# get_web_search 함수가 있는 셀 찾기 및 수정
for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'def get_web_search' in source:
            # 새로운 docstring으로 교체
            new_source = source.replace(
                '    """\n    웹 검색을 수행하는 함수.\n    """',
                '''    """
    웹 검색을 수행하는 함수.
    
    Args:
        query (str): 검색할 키워드나 질문
        search_period (str): 검색 기간 설정 (기본값: 'm')
                            - 'd': 최근 하루 (day)
                            - 'w': 최근 일주일 (week)
                            - 'm': 최근 한 달 (month)
                            - 'y': 최근 일 년 (year)
    
    Returns:
        str: 검색 결과 문자열
    
    Examples:
        - 최근 뉴스 검색: query='KT 소액결제 사건', search_period='d'
        - 일반 검색: query='Python 튜토리얼', search_period='m'
        - 오래된 자료 검색: query='역사적 사건', search_period='y'
    """'''
            )
            # 소스를 다시 리스트로 변환
            cell['source'] = new_source.split('\n')
            # 각 라인 끝에 개행 문자 추가 (마지막 라인 제외)
            cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                             for i, line in enumerate(cell['source'])]
            break

# 수정된 노트북 저장
with open('sec02/01_conditional_tools.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print("Docstring이 성공적으로 업데이트되었습니다.")
