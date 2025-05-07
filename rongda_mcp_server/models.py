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
