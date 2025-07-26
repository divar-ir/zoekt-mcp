from dataclasses import dataclass
from typing import List


@dataclass
class Match:
    line_number: int
    text: str


@dataclass
class FormattedResult:
    filename: str
    repository: str
    matches: List[Match]
    url: str
