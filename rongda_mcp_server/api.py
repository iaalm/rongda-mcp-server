from os import environ
from typing import List, Optional
from dataclasses import dataclass

import aiohttp
from loguru import logger

from rongda_mcp_server.login import DEFAULT_HEADERS, login
from rongda_mcp_server.models import FinancialReport, ReportContent, SearchResult

async def search_stock_hint(session: aiohttp.ClientSession, hint_key: str) -> List[str]:
    """Search Rongda's database for stocks based on a keyword hint.

    Args:
        hint_key: The keyword to search for (e.g. company name)

    Returns:
        List of StockHint objects matching the search term
    """
    # API endpoint
    url = f"https://doc.rongdasoft.com/api/web-server/xp/3947/searchStockHint"

    # Prepare query parameters
    params = {
        "stockType": "comprehensive",
        "searchAfter": "",
        "hintKey": hint_key,
    }

    # Prepare headers using DEFAULT_HEADERS
    headers = DEFAULT_HEADERS.copy()
    headers["Accept"] = "application/json, text/plain, */*"

    # Make the API request
    async with session.get(url, headers=headers, params=params) as response:
        # Check if the request was successful
        if response.status == 200:
            # Parse the JSON response
            data = await response.json()

            # Check if the response is successful and contains data
            if data.get("code") == 200 and data.get("success") and "data" in data:
                logger.debug(f"Response data: {data}")
                # Create a list to store the StockHint objects
                stock_hints = []

                # Process each stock in the response
                for item in data.get("data", []):
                    #     # Create a StockHint object
                    #     stock_hint = StockHint(
                    #         id=item.get("id", ""),
                    #         stock_code=item.get("stock_code", ""),
                    #         stock_name=item.get("stock_name", ""),
                    #         stock_code_short=item.get("stock_code_short", ""),
                    #         stock_type=item.get("stock_type", ""),
                    #         oldNameType=item.get("oldNameType", False),
                    #         stock_old_name=item.get("stock_old_name"),
                    #         stock_name_short=item.get("stock_name_short"),
                    #         delist_flag=item.get("delist_flag"),
                    #         create_time=item.get("create_time"),
                    #         update_time=item.get("update_time")
                    #     )

                    stock_hints.append(
                        item.get("stock_code_short", "") + " " + item.get("stock_name")
                    )

                return stock_hints
            else:
                logger.error(
                    f"Error in response: {data.get('retMsg', 'Unknown error')}"
                )
                return []
        else:
            # Return empty list on error
            logger.error(
                f"Error: API request failed with status code {response.status}"
            )
            return []


async def comprehensive_search(
    session: aiohttp.ClientSession, security_code: List[str], key_words: List[str], title: List[str] = []
) -> List[FinancialReport]:
    """Search Rongda's financial report database."""
    # API endpoint
    url = "https://doc.rongdasoft.com/api/web-server/xp/comprehensive/search"

    # Prepare headers using DEFAULT_HEADERS
    headers = DEFAULT_HEADERS.copy()
    headers["Content-Type"] = "application/json"

    # Prepare request payload
    payload = {
        "code_uid": 1683257028933,
        "obj": {
            "title": title,
            "titleOr": [],
            "titleNot": [],
            "content": key_words,
            "contentOr": [],
            "contentNot": [],
            "sectionTitle": [],
            "sectionTitleOr": [],
            "sectionTitleNot": [],
            "intelligentContent": "",
            "type": "2",
            "sortField": "pubdate",
            "order": "desc",
            "pageNum": 1,
            "pageSize": 20,
            "startDate": "",
            "endDate": "",
            "secCodes": security_code,
            "secCodeCombo": [],
            "secCodeComboName": [],
            "notice_code": [],
            "area": [],
            "seniorIndustry": [],
            "industry_code": [],
            "seniorPlate": [],
            "plateList": [],
        },
        "model": "comprehensive",
        "model_new": "comprehensive",
        "searchSource": "manual",
    }

    # Make the API request
    async with session.post(url, headers=headers, json=payload) as response:
        # Check if the request was successful
        if response.status == 200:
            # Parse the JSON response
            data = await response.json()
            logger.debug(f"Response data: {data}")

            # Create a list to store the FinancialReport objects
            reports = []
            # Process each report in the response
            for item in data.get("datas") or []:
                # Clean up HTML tags from title
                title = item.get("title") or ""
                if "<font" in title:
                    title = title.replace("<font style='color:red;'>", "").replace(
                        "</font>", ""
                    )

                # Create digest/content from the highlight fields
                content = ""
                if "digest" in item:
                    content = item.get("digest") or ""
                    content = content.replace(
                        "<div class='doc-digest-row'>", "\n"
                    ).replace("</div>", "")
                    content = content.replace("<font style='color:red;'>", "").replace(
                        "</font>", ""
                    )
                print(item)
                # Create a FinancialReport object
                report = FinancialReport(
                    title=title,
                    content=content,
                    downpath=item.get("downpath") or "",
                    htmlpath=item.get("htmlPath") or "",
                    dateStr=item.get("dateStr", ""),
                    security_code=str(item.get("secCode", ""))
                    + " "
                    + str(item.get("secName", "")),
                    noticeTypeName=item.get("noticeTypeName", []),
                )

                reports.append(report)

            return reports
        else:
            # Return empty list on error
            logger.error(
                f"Error: API request failed with status code {response.status}, response: {await response.text()}"
            )
            return []
        

doc_base = "https://rd-xp-pdfhtml.rongdasoft.com/"


async def download_report_html(
    session: aiohttp.ClientSession, 
    report: FinancialReport
) -> Optional[ReportContent]:
    """Download the HTML content of a financial report.
    
    Args:
        session: The authenticated aiohttp session
        report: The FinancialReport object containing the htmlpath
    
    Returns:
        ReportContent object with the report's content and metadata, or None if download fails
    """
    if not report.htmlpath:
        logger.error(f"No HTML path available for report: {report.title}")
        return None

    # Construct the full URL
    url = f"{doc_base}{report.htmlpath}"
    
    # Prepare headers using DEFAULT_HEADERS
    headers = DEFAULT_HEADERS.copy()
    
    try:
        # Download the HTML content
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Failed to download HTML content: {response.status}, {await response.text()}")
                return None
            
            html_content = await response.text()
            
            # Create and return a ReportContent object
            return ReportContent(
                title=report.title,
                html_path=report.htmlpath,
                content=html_content,
                report_date=report.dateStr,
                security_code=report.security_code
            )
            
    except Exception as e:
        logger.exception(f"Error downloading report HTML: {e}")
        return None


def search_keywords(
    report_content: ReportContent, 
    keywords: List[str], 
    context_chars: int = 100
) -> List[SearchResult]:
    """Search for keywords in a report's content and extract surrounding context.
    
    Args:
        report_content: ReportContent object containing the report's HTML content and metadata
        keywords: List of keywords to search for
        context_chars: Number of characters to include before and after each keyword
    
    Returns:
        List of SearchResult objects containing the keyword, context, and position
    """
    try:
        # Simple HTML cleaning - remove tags to get plain text
        import re
        text_content = report_content.content
        text_content = re.sub(r'<style.*?>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<script.*?>.*?</script>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]*>', ' ', text_content)
        # Replace multiple spaces and newlines with single space
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Search for keywords and collect context
        results = []
        for keyword in keywords:
            # Case insensitive search
            positions = [m.start() for m in re.finditer(re.escape(keyword), text_content, re.IGNORECASE)]
            
            for pos in positions:
                # Get text around the keyword
                start = max(0, pos - context_chars)
                end = min(len(text_content), pos + len(keyword) + context_chars)
                
                # Extract the context
                context = text_content[start:end]
                
                # Add ellipsis if we trimmed the text
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(text_content) else ""
                
                # Create context with the keyword highlighted
                highlighted_context = prefix + context + suffix
                
                results.append(SearchResult(
                    keyword=keyword,
                    context=highlighted_context,
                    start_position=pos
                ))
        
        # Sort results by position
        return sorted(results, key=lambda x: x.start_position)
            
    except Exception as e:
        logger.exception(f"Error searching keywords in report content: {e}")
        return []


def extract_keyword_context(
    report_content: ReportContent,
    search_result: SearchResult,
    context_chars: int = 300  # Extended context
) -> dict:
    """Extract a broader context around a keyword search result.
    
    Args:
        report_content: ReportContent object containing the report's content and metadata
        search_result: A SearchResult object with keyword and position information
        context_chars: Number of characters to include before and after the keyword
    
    Returns:
        Dictionary with enhanced context information including:
        - keyword: The keyword that was matched
        - context: Broader text context surrounding the keyword
        - position: The position of the keyword in the text
        - paragraph: Attempt to extract the full paragraph containing the keyword
        - section_title: Attempt to find a nearby section title (if available)
        - report_metadata: Basic metadata about the source report
    """
    try:
        import re
        
        # Get clean text content from HTML
        text_content = report_content.content
        text_content = re.sub(r'<style.*?>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<script.*?>.*?</script>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]*>', ' ', text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Get position info from search result
        keyword = search_result.keyword
        position = search_result.start_position
        
        # Extract broader context
        start = max(0, position - context_chars)
        end = min(len(text_content), position + len(keyword) + context_chars)
        
        broader_context = text_content[start:end]
        
        # Add ellipsis if we trimmed the text
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text_content) else ""
        
        broader_context = prefix + broader_context + suffix
        
        # Try to extract the paragraph
        # Look for paragraph breaks (multiple spaces/newlines) before and after keyword
        paragraph_text = ""
        para_start = text_content.rfind("\n\n", 0, position)
        if para_start == -1:
            # Try with a different paragraph delimiter
            para_start = text_content.rfind(". ", 0, position)
            if para_start != -1:
                para_start += 2  # Move past the period and space
            else:
                para_start = max(0, position - 200)
        else:
            para_start += 2  # Move past the newlines
            
        para_end = text_content.find("\n\n", position)
        if para_end == -1:
            # Try with a different paragraph delimiter
            next_sentence = text_content.find(". ", position)
            if next_sentence != -1:
                para_end = next_sentence + 1
            else:
                para_end = min(len(text_content), position + 200)
                
        paragraph_text = text_content[para_start:para_end].strip()
        
        # Try to find nearby section title (often in bold/h tags)
        section_title = ""
        # Simple attempt to find section title pattern in original HTML
        title_pattern = r'<h\d[^>]*>(.*?)</h\d>'
        titles = re.findall(title_pattern, report_content.content)
        # Find the nearest title before the keyword position
        if titles:
            plain_html = re.sub(r'<[^>]*>', '', report_content.content)
            for title in titles:
                title_plain = re.sub(r'<[^>]*>', '', title)
                title_pos = plain_html.find(title_plain)
                if 0 <= title_pos < position:
                    section_title = title_plain.strip()
        
        # Construct rich result
        return {
            "keyword": keyword,
            "context": broader_context,
            "position": position,
            "paragraph": paragraph_text,
            "section_title": section_title,
            "report_metadata": {
                "title": report_content.title,
                "date": report_content.report_date,
                "security_code": report_content.security_code
            }
        }
        
    except Exception as e:
        logger.exception(f"Error extracting broader keyword context: {e}")
        # Fallback to original context from search_result
        return {
            "keyword": search_result.keyword,
            "context": search_result.context,
            "position": search_result.start_position
        }



if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        # Example for comprehensive_search
        print("Testing comprehensive_search:")
        async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:
            expanded_code = await search_stock_hint(session, "药明康德")
            for code in expanded_code:
                print(code)
            
            reports = await comprehensive_search(session, ["603259 药明康德"], ["管理费用"])
            for report in reports:
                print(report)
            
            report = await download_report_html(session=session, report=reports[0])
            print(report)

    asyncio.run(main())
