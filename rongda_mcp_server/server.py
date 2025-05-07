# server.py
from datetime import datetime
import json
from os import environ
from typing import Any, Dict, List, Literal, Optional

import aiohttp
from mcp.server.fastmcp import FastMCP

from rongda_mcp_server.__about__ import __version__ as version
from rongda_mcp_server.api import comprehensive_search, search_stock_hint
from rongda_mcp_server.login import login
from rongda_mcp_server.models import FinancialReport

# Create an MCP server
mcp = FastMCP("Rongda MCP Server", version)


# Add an addition tool
@mcp.tool(
    "search_disclosure_documents",
    description="Search for listed company disclosure documents in the Rongda database",
)
async def search_disclosure_documents(
    company_name: str, key_words: List[str], start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, report_type: Optional[Literal["AnnualReports", "QuarterlyReports"]] = None
) -> List[FinancialReport]:
    async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:
        expanded_code = await search_stock_hint(session, company_name)
        return await comprehensive_search(session, expanded_code, key_words)


def start_server():
    """Start the MCP server."""
    print(f"Starting MCP Server ({version})...")
    mcp.run()
