# Library Loan & Fine Manager

Python desktop application (Tkinter) that manages library loans, calculates overdue
fines using fixed rules, and analyses how fines are spread across members and months.

## Features
- Maintain loan records (add loan, mark as returned) - stored in `data/loans.csv`
- Overdue duration + fine calculation (rules below)
- Search (loan id / member / book) and status filter (Borrowed / Overdue / Returned)
- Fine summaries per member and per month, plus automatic pattern insights
- 3 Matplotlib reports: Fines by Member, Fines per Month, Status Distribution (savable as PNG)
- Input validation + exception handling (invalid dates, member IDs, double return, corrupt CSV rows)

## Fine rules
| Item | Rule |
|---|---|
| Grace period | 1 day after due date is free |
| Days 1-7 after grace | Rs 5 / day |
| Days 8-14 after grace | Rs 10 / day |
| Day 15+ after grace | Rs 20 / day |
| Cap | Rs 500 per loan |

Unreturned books keep accruing fine up to today's date.

## Project structure
| File | Purpose |
|---|---|
| `main.py` | entry point |
| `models.py` | `Loan` dataclass, validation, `ValidationError` |
| `fines.py` | fine rules (NumPy vectorised) |
| `storage.py` | CSV persistence, loan operations, Pandas DataFrame, search |
| `analytics.py` | summaries, pattern detection, Matplotlib charts |
| `gui.py` | Tkinter interface |
| `generate_sample_data.py` | creates sample `data/loans.csv` |
| `tests/test_all.py` | 16 unit tests |

## Run
```bash
pip install -r requirements.txt
python main.py
```
Tkinter ships with Python (on Linux: `sudo apt install python3-tk`).

## Test
```bash
python -m unittest discover -s tests -t .
```

## Sample reports
See the `reports/` folder.
