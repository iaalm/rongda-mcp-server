from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FinancialReport:
    """Represents a financial report document from the Rongda database."""

    title: str
    content: str
    downpath: str
    htmlpath: Optional[str]
    dateStr: str
    secCode: str
    secName: str
    industry: Optional[str] = None
    noticeTypeName: Optional[List[str]] = None
