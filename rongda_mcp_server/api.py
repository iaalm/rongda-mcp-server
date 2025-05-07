from typing import List, Optional
from os import environ

import aiohttp

from rongda_mcp_server.login import DEFAULT_HEADERS, login
from rongda_mcp_server.models import FinancialReport



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
                print(f"Response data: {data}")
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
                        item.get("stock_code_short", "")
                        + " "
                        + item.get("stock_name")
                    )

                return stock_hints
            else:
                print(f"Error in response: {data.get('retMsg', 'Unknown error')}")
                return []
        else:
            # Return empty list on error
            print(f"Error: API request failed with status code {response.status}")
            return []

async def comprehensive_search(
    session:  aiohttp.ClientSession, security_code: List[str], key_words: List[str]) -> List[FinancialReport]:
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
            "title": [],
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
            print(f"Response data: {data}")

            # Create a list to store the FinancialReport objects
            reports = []
            # Process each report in the response
            for item in data.get("datas", []):
                # Clean up HTML tags from title
                title = item.get("title", "")
                if "<font" in title:
                    title = title.replace(
                        "<font style='color:red;'>", ""
                    ).replace("</font>", "")

                # Create digest/content from the highlight fields
                content = ""
                if "digest" in item:
                    content = item.get("digest", "")
                    content = content.replace(
                        "<div class='doc-digest-row'>", "\n"
                    ).replace("</div>", "")
                    content = content.replace(
                        "<font style='color:red;'>", ""
                    ).replace("</font>", "")

                # Create a FinancialReport object
                report = FinancialReport(
                    title=title,
                    content=content,
                    downpath=item.get("downpath", ""),
                    htmlpath=item.get("htmlpath", ""),
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
            print(
                f"Error: API request failed with status code {response.status}, response: {await response.text()}"
            )
            return []


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def main():
        # Example for comprehensive_search
        print("Testing comprehensive_search:")
        async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:
            expanded_code = await search_stock_hint(session, "平安银行")
            for code in expanded_code:
                print(code)
                
            reports = await comprehensive_search(session, ["平安银行"], ["财报"])
            for report in reports:
                print(report)

    asyncio.run(main())
