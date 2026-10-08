"""main.py - Entry point.  Run:  python main.py"""
from pathlib import Path

from storage import LoanStore, StorageError

DATA = Path(__file__).parent / "data" / "loans.csv"


def main():
    try:
        store = LoanStore(DATA)
    except StorageError as exc:
        print("Fatal:", exc)
        return
    from gui import App          # imported here so tests don't need a display
    App(store).mainloop()


if __name__ == "__main__":
    main()
