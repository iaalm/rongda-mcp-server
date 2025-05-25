# server.py
import json
from datetime import datetime
from os import environ
from typing import Any, Dict, List, Literal, Optional

import aiohttp
from loguru import logger
from mcp.server.fastmcp import FastMCP

from rongda_mcp_server.__about__ import __version__ as version
from rongda_mcp_server.api import (
    SearchResult, 
    comprehensive_search, 
    download_report_html,
    extract_keyword_context, 
    search_keywords, 
    search_stock_hint
)

from rongda_mcp_server.login import login
from rongda_mcp_server.models import FinancialReport

# Create an MCP server
mcp = FastMCP("Rongda MCP Server", version)


@mcp.tool(
    "search_disclosure_documents",
    description='Search for listed company disclosure documents in the Rongda database.\n'
                'Note: The company_name should in format of "000001 平安银行". \n'
                'Note: The body_key_words should be information you looking for in report body, like "主营业务收入".\n'
                'Note: The title_keywords should be information you looking for in report title, like "年度报告".'
    # "The report_type is either 'AnnualReports' or 'QuarterlyReports'."
)
async def search_disclosure_documents(
    company_name: str,
    body_key_words: List[str],
    title_keywords: List[str],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    # report_type: Optional[Literal["AnnualReports", "QuarterlyReports"]] = None,
) -> List[FinancialReport]:
    async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:
        # expanded_code = await search_stock_hint(session, company_name)
        expanded_code = [company_name]
        return await comprehensive_search(session, expanded_code, body_key_words, title_keywords)


def start_server():
    """Start the MCP server."""
    logger.verbose(f"Starting MCP Server ({version})...")
    mcp.run()
