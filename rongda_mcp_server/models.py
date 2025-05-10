from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FinancialReport:
    """Represents a financial report document from the Rongda database."""

    title: str
    content: str
    downpath: str
    htmlpath: Optional[str]
    dateStr: str
    security_code: str
    noticeTypeName: Optional[List[str]] = None



@dataclass
class ReportContent:
    """Contains the content of a financial report along with metadata."""
    title: str
    html_path: str
    content: str
    report_date: str
    security_code: str



@dataclass
class SearchResult:
    """Represents a search result with keyword context."""
    keyword: str
    context: str
    start_position: int
