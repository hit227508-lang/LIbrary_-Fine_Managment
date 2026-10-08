"""storage.py - CSV persistence and loan management (pandas based)."""
import os
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from fines import calculate_fines_array
from models import Loan, ValidationError, parse_date

COLUMNS = ["loan_id", "member_id", "member_name", "book_title",
           "issue_date", "due_date", "return_date"]


class StorageError(Exception):
    """Raised when the data file cannot be read or written."""


class LoanStore:
    def __init__(self, path="data/loans.csv"):
        self.path = Path(path)
        self.loans: list[Loan] = []
        self.skipped_rows = 0
        self.load()

    # ---------- persistence ----------
    def load(self):
        self.loans, self.skipped_rows = [], 0
        if not self.path.exists():
            return
        try:
            df = pd.read_csv(self.path, dtype=str).fillna("")
        except pd.errors.EmptyDataError:
            return
        except (pd.errors.ParserError, OSError, UnicodeDecodeError) as exc:
            raise StorageError(f"Could not read {self.path}: {exc}") from exc
        missing = set(COLUMNS) - set(df.columns)
        if missing:
            raise StorageError(f"Data file is missing columns: {sorted(missing)}")
        for row in df.to_dict("records"):
            try:
                self.loans.append(Loan.from_dict(row))
            except (ValidationError, KeyError):
                self.skipped_rows += 1   # ignore corrupt rows, keep the rest

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            pd.DataFrame([l.to_dict() for l in self.loans], columns=COLUMNS).to_csv(tmp, index=False)
            os.replace(tmp, self.path)
        except OSError as exc:
            raise StorageError(f"Could not save {self.path}: {exc}") from exc

    # ---------- operations ----------
    def _next_id(self) -> str:
        nums = [int(l.loan_id[1:]) for l in self.loans if l.loan_id[1:].isdigit()]
        return f"L{(max(nums) + 1 if nums else 1):04d}"

    def add_loan(self, member_id, member_name, book_title, issue_date, due_date) -> Loan:
        loan = Loan(self._next_id(), member_id, member_name, book_title, issue_date, due_date)
        self.loans.append(loan)
        self.save()
        return loan

    def get(self, loan_id: str) -> Loan:
        for l in self.loans:
            if l.loan_id == loan_id:
                return l
        raise KeyError(f"Loan {loan_id} not found.")

    def mark_returned(self, loan_id: str, return_date=None) -> Loan:
        loan = self.get(loan_id)
        if loan.return_date is not None:
            raise ValidationError(f"Loan {loan_id} is already returned.")
        rdate = parse_date(return_date, "Return date") if return_date else date.today()
        if rdate < loan.issue_date:
            raise ValidationError("Return date cannot be before the issue date.")
        loan.return_date = rdate
        self.save()
        return loan

    # ---------- analysis table ----------
    def to_dataframe(self, today: Optional[date] = None) -> pd.DataFrame:
        today = today or date.today()
        df = pd.DataFrame([l.to_dict() for l in self.loans], columns=COLUMNS)
        if df.empty:
            return df.assign(days_late=pd.Series(dtype=int), fine=pd.Series(dtype=float),
                             status=pd.Series(dtype=str))
        for c in ("issue_date", "due_date", "return_date"):
            df[c] = pd.to_datetime(df[c].replace("", pd.NA))
        end = df["return_date"].fillna(pd.Timestamp(today))
        df["days_late"] = (end - df["due_date"]).dt.days.clip(lower=0).astype(int)
        df["fine"] = calculate_fines_array(df["days_late"].to_numpy())
        df["status"] = "Borrowed"
        df.loc[df["return_date"].notna(), "status"] = "Returned"
        df.loc[df["return_date"].isna() & (df["days_late"] > 0), "status"] = "Overdue"
        return df

    def search(self, query: str = "", status: str = "All", today=None) -> pd.DataFrame:
        df = self.to_dataframe(today)
        if df.empty:
            return df
        if status and status != "All":
            df = df[df["status"] == status]
        q = (query or "").strip()
        if q:
            mask = pd.Series(False, index=df.index)
            for col in ("loan_id", "member_id", "member_name", "book_title"):
                mask |= df[col].str.contains(q, case=False, regex=False)
            df = df[mask]
        return df
