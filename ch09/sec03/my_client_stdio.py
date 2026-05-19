import asyncio
from pathlib import Path
from fastmcp import Client

server_path = Path(__file__).parent / "mcp_server.py"
client = Client(str(server_path))

async def call_tool(name: str):
    async with client:
        result = await client.call_tool("greet", {"name": name})
        print(result)

asyncio.run(call_tool("김일남"))