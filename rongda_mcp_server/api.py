from typing import List
from rongda_mcp_server.helpers import login, DEFAULT_HEADERS
from rongda_mcp_server.models import FinancialReport


async def comprehensive_search(
    security_code: str, key_words: List[str]
) -> List[FinancialReport]:
    """Search Rongda's financial report database."""
    # API endpoint
    url = "https://doc.rongdasoft.com/api/web-server/xp/comprehensive/search"

    # Prepare headers using DEFAULT_HEADERS
    headers = DEFAULT_HEADERS.copy()
    headers["Content-Type"] = "application/json"

    # Format security code for request
    sec_codes = [f"{security_code} "] if " " not in security_code else [security_code]

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
            "secCodes": sec_codes,
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

    try:
        # Use aiohttp client session for async requests
        async with await login(environ["RD_USER"], environ["RD_PASS"]) as session:
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
                            secCode=item.get("secCode", ""),
                            secName=item.get("secName", ""),
                            industry=item.get("industry", ""),
                            noticeTypeName=item.get("noticeTypeName", []),
                        )

                        reports.append(report)

                    return reports
                else:
                    # Return empty list on error
                    print(
                        f"Error: API request failed with status code {response.status}"
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
            reports = await comprehensive_search("000001 平安银行", ["财报"])
            for report in reports:
                print(report)
        except Exception as e:
            print(f"Error: {str(e)}")

    asyncio.run(main())
