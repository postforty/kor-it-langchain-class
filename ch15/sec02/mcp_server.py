# FastMCP 설치: https://github.com/jlowin/fastmcp?tab=readme-ov-file#installation
# MCP Inspector: https://modelcontextprotocol.io/docs/tools/inspector

from mcp.server.fastmcp import FastMCP
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
import yfinance as yf

# FastMCP 인스턴스 생성
mcp = FastMCP("Simple MCP Server")

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
    mcp.run(transport="streamable-http") # uv run mcp_server.py 실행