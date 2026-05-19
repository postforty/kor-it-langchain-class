from fastmcp import FastMCP

mcp = FastMCP("My MCP Server")

@mcp.tool
def greet(name: str) -> str:
    return f"안녕하세요, {name}님!"

# stdio 방식 -> 서버 구동 불필요
if __name__ == "__main__":
    mcp.run() # http 방식 서버 구동 명령: uv run fastmcp run mcp_server.py:mcp --transport http --port 8000

# if __name__ == "__main__":
#     mcp.run(transport="http", port=8000) # 포트 지정 http 방식 서버 구동 명령: uv run mcp_server.py