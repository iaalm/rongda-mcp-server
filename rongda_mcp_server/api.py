from typing import List, Optional

from rongda_mcp_server.helpers import DEFAULT_HEADERS, login, search_stock_hint
from rongda_mcp_server.models import FinancialReport


async def comprehensive_search(
    security_code: str, key_words: List[str], search_security_code: bool = True
) -> List[FinancialReport]:
    """Search Rongda's financial report database."""
    # API endpoint
    url = "https://doc.rongdasoft.com/api/web-server/xp/comprehensive/search"

    # Prepare headers using DEFAULT_HEADERS
    headers = DEFAULT_HEADERS.copy()
    headers["Content-Type"] = "application/json"

    try:
        # Use aiohttp client session for async requests
        async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:

            if search_security_code:
                expanded_code = await search_stock_hint(session, security_code)
            else:
                expanded_code = [security_code]

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
                    "secCodes": expanded_code,
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
                    if data.get("datas", None) is None:
                        if search_security_code and len(security_code) == 1:
                            print("No data found, trying to search by security code.")
                            new_security_code = await search_stock_hint(
                                security_code[0]
                            )
                            comprehensive_search(
                                session=session,
                                security_code=new_security_code,
                                key_words=key_words,
                                search_security_code=False,
                            )
                        else:
                            print("No data found in the response.")
                            return []

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
                            security_code=item.get("secCode", "")
                            + " "
                            + item.get("secName", ""),
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

    except Exception as e:
        raise


if __name__ == "__main__":
    # Example usage
    import asyncio
    from os import environ

    async def main():
        try:
            # Example for comprehensive_search
            print("Testing comprehensive_search:")
            reports = await comprehensive_search("平安银行", ["财报"])
            for report in reports:
                print(report)
        except Exception as e:
            print(f"Error: {str(e)}")

    asyncio.run(main())
