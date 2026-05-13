from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mcp_servers.local_only.tools.japanese_calendar import register_tools

mcp = FastMCP("office_py_tools_local_only")
register_tools(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
