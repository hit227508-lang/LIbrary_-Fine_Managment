"""gui.py - Tkinter user interface."""
import tkinter as tk
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import analytics
from models import ValidationError
from storage import LoanStore, StorageError

COLS = ("loan_id", "member_id", "member_name", "book_title", "issue_date",
        "due_date", "return_date", "days_late", "fine", "status")


class App(tk.Tk):
    def __init__(self, store: LoanStore):
        super().__init__()
        self.store = store
        self.title("Library Loan & Fine Manager")
        self.geometry("1100x650")
        self.current_fig = None
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.tab_loans, self.tab_add, self.tab_reports = (ttk.Frame(nb) for _ in range(3))
        nb.add(self.tab_loans, text="Loans")
        nb.add(self.tab_add, text="Add Loan")
        nb.add(self.tab_reports, text="Reports")
        self._build_loans()
        self._build_add()
        self._build_reports()
        self.refresh()
        if store.skipped_rows:
            messagebox.showwarning("Data", f"{store.skipped_rows} invalid row(s) were skipped while loading.")

    # ---------- Loans tab ----------
    def _build_loans(self):
        bar = ttk.Frame(self.tab_loans)
        bar.pack(fill="x", pady=6)
        ttk.Label(bar, text="Search:").pack(side="left", padx=4)
        self.q = tk.StringVar()
        e = ttk.Entry(bar, textvariable=self.q, width=28)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _e: self.refresh())
        ttk.Label(bar, text="Status:").pack(side="left", padx=8)
        self.status = tk.StringVar(value="All")
        cb = ttk.Combobox(bar, textvariable=self.status, state="readonly", width=10,
                          values=["All", "Borrowed", "Overdue", "Returned"])
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Button(bar, text="Mark Returned", command=self.mark_returned).pack(side="right", padx=4)
        self.total_lbl = ttk.Label(bar, text="")
        self.total_lbl.pack(side="right", padx=12)

        self.tree = ttk.Treeview(self.tab_loans, columns=COLS, show="headings")
        for c in COLS:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=170 if c == "book_title" else 95, anchor="w")
        sb = ttk.Scrollbar(self.tab_loans, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.tag_configure("Overdue", background="#f8d7da")
        self.tree.tag_configure("Returned", background="#e2f0d9")

    def refresh(self):
        df = self.store.search(self.q.get(), self.status.get())
        self.tree.delete(*self.tree.get_children())
        for _, r in df.iterrows():
            vals = [r["loan_id"], r["member_id"], r["member_name"], r["book_title"],
                    r["issue_date"].date(), r["due_date"].date(),
                    r["return_date"].date() if r["return_date"] == r["return_date"] else "",
                    r["days_late"], f"{r['fine']:.0f}", r["status"]]
            self.tree.insert("", "end", values=vals, tags=(r["status"],))
        total = df["fine"].sum() if len(df) else 0
        self.total_lbl.config(text=f"{len(df)} loans | Fines shown: Rs {total:,.0f}")

    def mark_returned(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a loan first.")
            return
        loan_id = self.tree.item(sel[0])["values"][0]
        try:
            loan = self.store.mark_returned(loan_id)
        except (ValidationError, KeyError, StorageError) as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.refresh()
        messagebox.showinfo("Returned", f"{loan.loan_id} returned on {loan.return_date}.")

    # ---------- Add tab ----------
    def _build_add(self):
        f = ttk.Frame(self.tab_add, padding=20)
        f.pack(anchor="nw")
        today = date.today()
        self.vars = {k: tk.StringVar(value=v) for k, v in {
            "member_id": "", "member_name": "", "book_title": "",
            "issue_date": str(today), "due_date": str(today + timedelta(days=14))}.items()}
        labels = {"member_id": "Member ID (M001)", "member_name": "Member name",
                  "book_title": "Book title", "issue_date": "Issue date (YYYY-MM-DD)",
                  "due_date": "Due date (YYYY-MM-DD)"}
        for i, k in enumerate(labels):
            ttk.Label(f, text=labels[k]).grid(row=i, column=0, sticky="w", pady=5)
            ttk.Entry(f, textvariable=self.vars[k], width=36).grid(row=i, column=1, padx=10)
        ttk.Button(f, text="Add Loan", command=self.add_loan).grid(row=6, column=1, sticky="e", pady=12)

    def add_loan(self):
        try:
            loan = self.store.add_loan(*(self.vars[k].get() for k in
                                         ("member_id", "member_name", "book_title", "issue_date", "due_date")))
        except (ValidationError, StorageError) as exc:
            messagebox.showerror("Invalid input", str(exc))
            return
        messagebox.showinfo("Added", f"Loan {loan.loan_id} added.")
        for k in ("member_id", "member_name", "book_title"):
            self.vars[k].set("")
        self.refresh()

    # ---------- Reports tab ----------
    def _build_reports(self):
        left = ttk.Frame(self.tab_reports, padding=6)
        left.pack(side="left", fill="y")
        for name in analytics.CHARTS:
            ttk.Button(left, text=name, width=22, command=lambda n=name: self.show_chart(n)).pack(pady=3)
        ttk.Button(left, text="Save current chart...", width=22, command=self.save_chart).pack(pady=(14, 3))
        ttk.Button(left, text="Refresh insights", width=22, command=self.show_insights).pack(pady=3)
        self.insights = tk.Text(left, width=44, height=22, wrap="word")
        self.insights.pack(pady=8)
        self.chart_frame = ttk.Frame(self.tab_reports)
        self.chart_frame.pack(side="right", fill="both", expand=True)
        self.show_insights()

    def show_insights(self):
        self.insights.delete("1.0", "end")
        for line in analytics.detect_patterns(self.store.to_dataframe()):
            self.insights.insert("end", "• " + line + "\n\n")

    def show_chart(self, name):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        self.current_fig = analytics.CHARTS[name](self.store.to_dataframe())
        canvas = FigureCanvasTkAgg(self.current_fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.show_insights()

    def save_chart(self):
        if self.current_fig is None:
            messagebox.showinfo("Chart", "Open a chart first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                self.current_fig.savefig(path)
            except OSError as exc:
                messagebox.showerror("Error", str(exc))
