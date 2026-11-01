import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = StdioServerParameters(
        command="/Users/zhaojian/.local/bin/uvx",
        args=[
            "--from",
            "/Users/zhaojian/code/fusion360/fusion360-mcp-server",
            "fusion360-mcp-server",
            "--mode",
            "socket",
        ],
    )
    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            for tool_name in ("ping", "get_scene_info"):
                result = await session.call_tool(tool_name, {})
                print(f"\n=== {tool_name} ===")
                for item in result.content:
                    if hasattr(item, "text"):
                        print(item.text)
                if result.isError:
                    raise RuntimeError(f"{tool_name} returned an MCP error")


asyncio.run(main())
