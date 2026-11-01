import argparse
import asyncio
import base64
import json
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tool")
    parser.add_argument("--code-file")
    parser.add_argument("--params", default="{}")
    parser.add_argument("--image-out")
    args = parser.parse_args()

    if args.code_file:
        params = {"code": Path(args.code_file).read_text(encoding="utf-8")}
    else:
        params = json.loads(args.params)

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
            result = await session.call_tool(
                args.tool, params, read_timeout_seconds=timedelta(seconds=90)
            )
            for item in result.content:
                if item.type == "text":
                    print(item.text)
                elif item.type == "image" and args.image_out:
                    output = Path(args.image_out)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_bytes(base64.b64decode(item.data))
                    print(f"Screenshot saved: {output}")
            if result.isError:
                raise RuntimeError(f"{args.tool} returned an MCP error")


asyncio.run(main())
