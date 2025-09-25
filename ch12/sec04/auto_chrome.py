from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
from langchain_core.messages import HumanMessage
# browser_agent.py에서 app과 AgentState 임포트
from browser_agent import app, AgentState

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)  # 브라우저를 닫지 않고 유지

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
    chat_history=[],  # 빈 채팅 기록으로 시작
    current_url=driver.current_url,
    scratchpad=[],
    user_input="start"  # 초기 시작 신호
)

print("--- 에이전트 실행 시작 ---")
try:
    # 재귀 한계를 늘리고 최대 반복 횟수 설정
    config = {
        "recursion_limit": 50,  # 기본 25에서 50으로 증가
        "max_iterations": 20
    }

    iteration_count = 0
    for s in app.stream(initial_state, config=config):
        iteration_count += 1
        print(f"--- 반복 {iteration_count} ---")
        print(s)
        print("---")

        # 최대 반복 횟수 체크
        if iteration_count >= config["max_iterations"]:
            print(
                f"⚠️ 최대 반복 횟수({config['max_iterations']})에 도달했습니다. 프로그램을 종료합니다.")
            break

        # 사용자가 'exit'를 입력했는지 체크
        if any('exit' in str(state_value).lower() for state_value in s.values() if isinstance(state_value, dict)):
            print("👋 사용자가 종료를 요청했습니다.")
            break

except Exception as e:
    print(f"❌ 에이전트 실행 중 오류 발생: {e}")
    print("프로그램을 안전하게 종료합니다.")
finally:
    # 브라우저 정리
    if 'driver' in locals() and driver:
        try:
            print("🧹 브라우저 정리 중...")
            # driver.quit()  # 브라우저를 유지하려면 주석 처리
        except:
            pass
    print("✅ 프로그램 종료 완료")
