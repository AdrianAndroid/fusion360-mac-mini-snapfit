import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server = StdioServerParameters(
        command="/Users/zhaojian/.local/bin/uvx",
        args=["--from", "/Users/zhaojian/code/fusion360/fusion360-mcp-server",
              "fusion360-mcp-server", "--mode", "socket"],
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"- {t.name}: {t.description or ''}")

asyncio.run(main())
