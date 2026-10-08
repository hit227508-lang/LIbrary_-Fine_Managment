"""Creates a realistic sample data/loans.csv (seeded, so reproducible)."""
import random
from datetime import date, timedelta

from storage import LoanStore

random.seed(42)
NAMES = ["Aarav Patel", "Diya Shah", "Rohan Mehta", "Isha Desai", "Kunal Joshi",
         "Meera Trivedi", "Nikhil Bhatt", "Priya Modi", "Sahil Parmar", "Tanvi Rao"]
BOOKS = ["Python Crash Course", "Wings of Fire", "Atomic Habits", "Data Structures in C",
         "The Alchemist", "Discrete Mathematics", "Clean Code", "Sapiens",
         "Digital Electronics", "Introduction to Algorithms", "Gitanjali", "Operating Systems"]
store = LoanStore("data/loans.csv")
store.loans.clear()
today = date.today()
for _ in range(60):
    i = random.randrange(len(NAMES))
    issue = today - timedelta(days=random.randint(5, 180))
    due = issue + timedelta(days=14)
    loan = store.add_loan(f"M{i+1:03d}", NAMES[i], random.choice(BOOKS), issue, due)
    if random.random() < (0.93 if due < today else 0.4):
        late = random.choice([0, 0, 0, 2, 4, 6, 9, 12, 18, 25]) if i % 3 == 0 else random.choice([0, 0, 0, 0, 1, 3])
        ret = min(due + timedelta(days=late), today)
        if ret >= issue:
            store.mark_returned(loan.loan_id, ret)
print("Created", len(store.loans), "loans")
