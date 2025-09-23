from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
from langchain_core.messages import HumanMessage
from browser_agent import app, AgentState # browser_agent.py에서 app과 AgentState 임포트

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True) # 브라우저를 닫지 않고 유지

# 불필요한 에러 메시지 제거
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

# WebDriver 서비스 설정
# service = Service(ChromeDriverManager().install())

# WebDriver 생성
driver = webdriver.Chrome(options=chrome_options)

# 브라우저에 접속할 URL
driver.get("https://www.naver.com")

# 초기 에이전트 상태 정의
initial_state = AgentState(
    driver=driver,
    chat_history=[HumanMessage(content="네이버에서 '오늘의 날씨'를 검색하고, 검색 결과를 읽어주세요.")], # 초기 지시
    current_url=driver.current_url,
    scratchpad=[],
    user_input="continue" # 초기에는 사용자 개입 없이 진행
)

print("--- 에이전트 실행 시작 ---")
for s in app.stream(initial_state):
    print(s)
    print("---")

