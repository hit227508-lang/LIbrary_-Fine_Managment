"""models.py - Loan data structure and input validation."""
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional

DATE_FORMAT = "%Y-%m-%d"
MEMBER_ID_PATTERN = re.compile(r"^M\d{3}$")


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def parse_date(text, field: str = "Date") -> date:
    if isinstance(text, date):
        return text
    try:
        return datetime.strptime(str(text).strip(), DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(f"{field} must be in YYYY-MM-DD format (got '{text}').")


def validate_member_id(value: str) -> str:
    value = str(value).strip().upper()
    if not MEMBER_ID_PATTERN.match(value):
        raise ValidationError("Member ID must look like M001 (M + 3 digits).")
    return value


def validate_text(value: str, field: str, max_len: int = 80) -> str:
    value = " ".join(str(value).split())
    if not value:
        raise ValidationError(f"{field} cannot be empty.")
    if len(value) > max_len:
        raise ValidationError(f"{field} is too long (max {max_len} characters).")
    return value


@dataclass
class Loan:
    loan_id: str
    member_id: str
    member_name: str
    book_title: str
    issue_date: date
    due_date: date
    return_date: Optional[date] = None

    def __post_init__(self):
        self.member_id = validate_member_id(self.member_id)
        self.member_name = validate_text(self.member_name, "Member name", 50)
        self.book_title = validate_text(self.book_title, "Book title")
        self.issue_date = parse_date(self.issue_date, "Issue date")
        self.due_date = parse_date(self.due_date, "Due date")
        if self.due_date < self.issue_date:
            raise ValidationError("Due date cannot be before the issue date.")
        if self.return_date not in (None, ""):
            self.return_date = parse_date(self.return_date, "Return date")
            if self.return_date < self.issue_date:
                raise ValidationError("Return date cannot be before the issue date.")
        else:
            self.return_date = None

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("issue_date", "due_date", "return_date"):
            d[k] = d[k].strftime(DATE_FORMAT) if d[k] else ""
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Loan":
        return cls(d["loan_id"], d["member_id"], d["member_name"], d["book_title"],
                   d["issue_date"], d["due_date"], d.get("return_date") or None)
