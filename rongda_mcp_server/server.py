# server.py
from os import environ
from typing import List, Dict, Any
import json
import aiohttp
from mcp.server.fastmcp import FastMCP
from rongda_mcp_server.__about__ import __version__ as version
from rongda_mcp_server.api import comprehensive_search
from rongda_mcp_server.models import FinancialReport

# Create an MCP server
mcp = FastMCP("Rongda MCP Server", version)


# Add an addition tool
@mcp.tool()
async def search(security_code: str, key_words: List[str]) -> List[FinancialReport]:
    return await comprehensive_search(security_code, key_words)


def start_server():
    """Start the MCP server."""
    mcp.run()