import asyncio
from fastmcp import Client

async def main():
    """MCP 클라이언트를 사용하여 서버와 통신합니다."""

    client = Client("http://localhost:8000/mcp")
    print("MCP 클라이언트를 생성하고 서버에 연결합니다.\n")

    try:
        # async with 블록을 사용하여 클라이언트 세션 관리
        async with client:
            print("--- 사용 가능한 도구 목록 ---")
            tools = await client.list_tools()
            print([tool.name for tool in tools])
            print("")

            # 'hello' 도구 테스트
            print("--- 'hello' 도구 테스트 ---")
            hello_response = await client.call_tool("hello", {"name": "김일남"}) # call_tool은 콘텐츠 객체의 리스트 반환
            print(f"결과: {hello_response}")

            # 'get_prompt' 도구 테스트
            print("--- 'get_current_time' 도구 테스트 ---")
            get_current_time_response = await client.call_tool(
                "get_current_time")
            print(f"결과:\n{get_current_time_response}\n")

            # 'simple://info' 리소스 테스트
            print("--- 'get_yf_stock_history' 도구 테스트 ---")
            get_yf_stock_history_response = await client.call_tool(
                "get_yf_stock_history",
                {"stock_history_input": 
                    {
                        "ticker": "TLSA", 
                        "period": "1mo"
                    }
                }
            )
            print(f"결과:\n{get_yf_stock_history_response}")

            # 'simple://info' 리소스 테스트
            print("--- 'simple://info' 리소스 테스트 ---")
            resource_content = await client.read_resource("simple://info")
            # read_resource도 콘텐츠 객체의 리스트 반환
            print(f"결과:\n{resource_content[0].text}")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    asyncio.run(main())