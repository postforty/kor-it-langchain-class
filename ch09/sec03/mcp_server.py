# FastMCP 설치: https://github.com/jlowin/fastmcp?tab=readme-ov-file#installation
# 빠른 시작: https://gofastmcp.com/getting-started/quickstart
# MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector

from mcp.server.fastmcp import FastMCP # uv add fastmcp
from datetime import datetime
from zoneinfo import ZoneInfo # uv add tzdata
from pydantic import BaseModel, Field
import yfinance as yf
from langchain_community.tools import DuckDuckGoSearchResults 
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper 

# FastMCP 인스턴스 생성
mcp = FastMCP("My MCP Server")

@mcp.tool()  # 도구 정의
def hello(name: str = "아무개") -> str:
    """간단한 인사말을 반환하는 도구"""
    return f"안녕하세요, {name}님!"

@mcp.tool()
def get_current_time(timezone: str = "Asia/Seoul", location: str = "부산") -> str:
    """ 현재 시각을 반환하는 함수

    Args:
        timezone (str): 타임존 (예: 'Asia/Seoul') 실제 존재하는 타임존이어야 함
        location (str): 지역명. 타임존이 모든 지명에 대응되지 않기 때문에 이후 llm 답변 생성에 사용됨
    """
    target_timezone = ZoneInfo(timezone)
    now = datetime.now(target_timezone).strftime("%Y-%m-%d %H:%M:%S")
    location_and_local_time = f'{timezone} ({location}) 현재시각 {now} ' # 타임존, 지역명, 현재시각을 문자열로 반환
    print(location_and_local_time)
    return location_and_local_time

class StockHistoryInput(BaseModel):
    ticker: str = Field(..., title="주식 코드", description="주식 코드 (예: TSLA)")
    period: str = Field(..., title="기간", description="주식 데이터 조회 기간 (예: 1d, 1mo, 1y)")

@mcp.tool()
def get_yf_stock_history(stock_history_input: StockHistoryInput) -> str:
    """ 주식 종목의 가격 데이터를 조회하는 함수"""
    stock = yf.Ticker(stock_history_input.ticker)
    history = stock.history(period=stock_history_input.period)
    history_md = history.to_markdown() 

    return history_md

@mcp.tool()
def get_web_search(query: str, search_period: str='w', region: str='kr-kr') -> str:
    """
    특정 지역과 기간을 설정하여 웹 검색(뉴스)을 수행합니다.

    Args:
        query (str): 검색어
        search_period (str): 검색 기간. 'd'(일간), 'w'(주간), 'm'(월간), 'y'(연간) 중 선택
        region (str): 검색 지역 코드. 한국('kr-kr'), 미국('us-en'), 일본('jp-jp'), 영국('uk-en') 등
    
    Returns:
        str: 검색된 뉴스 결과 리스트
    """
    wrapper = DuckDuckGoSearchAPIWrapper(
        region=region,
        time=search_period
    )
    
    search = DuckDuckGoSearchResults(
        api_wrapper=wrapper,
        backend="news",
        results_separator=';\n'
    )

    searched = search.invoke(query)
    return searched

@mcp.resource("simple://info")  # 리소스 정의(필수 아님)
def get_server_info() -> str:
    """서버 정보를 제공하는 리소스"""
    return """
    Simple MCP Server 정보
    =====================
    
    이 서버는 MCP(Model Context Protocol)의 기본 기능을 시연하는 간단한 예제입니다.
    
    제공하는 도구:
    - hello: 인사말 생성
    - get_current_time: 현재 시각 제공
    - get_yf_stock_history: 주식 종목의 가격 데이터 조회
    
    제공하는 리소스:
    - simple://info: 서버 정보
    """

if __name__ == "__main__":
    """서버를 실행합니다."""
    mcp.run()

# 발생했던 오류 및 해결 방법:
# 1. ERROR Failed to run: Already running asyncio in this thread (cli.py:533)
#    - 발생: uv run fastmcp run mcp_server.py:mcp 실행 시
#    - 원인: Windows 환경에서 FastMCP 2.x 버전의 비동기 이벤트 루프 충돌 문제
#    - 해결: uv add fastmcp --upgrade 명령을 통해 FastMCP 3.2.3 이상으로 업데이트하여 해결
#
# 2. [WinError 10048] 각 소켓 주소(프로토콜/네트워크 주소/포트)는 하나만 사용할 수 있습니다
#    - 발생: --port 8000 등으로 실행 시
#    - 원인: 지정한 포트가 이미 다른 프로세스(이전 서버 등)에 의해 사용 중임
#    - 해결: 해당 포트를 사용하는 프로세스를 종료하거나, 다른 포트를 지정하여 실행

# 구동 방법:
# 1. 기본 실행 (stdio 방식 - Claude Desktop 등 연동 시)
#    uv run fastmcp run mcp_server.py:mcp
#
# 2. HTTP 방식 실행 (SSE - 외부 클라이언트 접속 시)
#    uv run fastmcp run mcp_server.py:mcp --transport http --port 8000
#
# 3. 개발 및 테스트 (Inspector UI 실행)
#    uv run fastmcp dev inspector mcp_server.py:mcp