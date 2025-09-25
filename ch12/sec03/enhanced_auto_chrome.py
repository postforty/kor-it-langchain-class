from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from langchain_core.messages import HumanMessage
# browser_agent.py에서 app과 AgentState 임포트
from browser_agent import app, AgentState

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)  # 브라우저를 닫지 않고 유지

# 불필요한 에러 메시지 제거
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# WebDriver 생성
driver = webdriver.Chrome(options=chrome_options)

# 브라우저에 접속할 URL
driver.get("https://www.naver.com")

# 초기 에이전트 상태 정의 - 스마트 도구들을 활용한 예시
initial_state = AgentState(
    driver=driver,
    chat_history=[HumanMessage(content="""
네이버에서 다음 작업을 단계별로 수행해주세요:
1. 검색창을 찾아서 '오늘의 날씨'를 입력하세요
2. 검색 버튼을 클릭해서 검색을 실행하세요
3. 검색 결과 페이지에서 날씨 정보를 찾아서 읽어주세요

각 단계를 순서대로 완료한 후 다음 단계로 진행해주세요.
스마트 도구들(smart_click, smart_type, analyze_page_elements)을 활용하세요.
    """)],
    current_url=driver.current_url,
    scratchpad=[],
    user_input="continue"  # 초기에는 사용자 개입 없이 진행
)

print("--- 향상된 브라우저 에이전트 실행 시작 ---")
print("페이지 분석 에이전트가 통합되어 더 스마트한 요소 찾기가 가능합니다!")
print("---")

for s in app.stream(initial_state):
    print(s)
    print("---")
