from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from langchain_core.messages import HumanMessage
from browser_agent import app, AgentState

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# WebDriver 생성
driver = webdriver.Chrome(options=chrome_options)

# 브라우저에 접속할 URL
driver.get("https://www.naver.com")

# 단계별 명확한 지시사항
initial_state = AgentState(
    driver=driver,
    chat_history=[HumanMessage(content="""
네이버에서 날씨 검색을 단계별로 수행해주세요:

**1단계**: smart_type을 사용해서 검색창에 '오늘의 날씨'를 입력하세요
**2단계**: smart_click을 사용해서 '검색 버튼'을 클릭하거나 press_enter를 사용해서 Enter 키를 누르세요
**3단계**: 검색 결과 페이지가 로드된 후 analyze_page_elements를 사용해서 날씨 정보를 찾으세요
**4단계**: 찾은 날씨 정보를 사용자에게 알려주세요

각 단계를 완료한 후 다음 단계로 진행해주세요. 
검색을 실행하지 않고 바로 날씨 정보를 찾으려고 하지 마세요.
    """)],
    current_url=driver.current_url,
    scratchpad=[],
    user_input="continue"
)

print("--- 단계별 브라우저 에이전트 실행 시작 ---")
print("명확한 단계별 지시사항으로 더 정확한 실행이 가능합니다!")
print("---")

for s in app.stream(initial_state):
    print(s)
    print("---")
