"""analytics.py - Fine summaries, pattern detection and Matplotlib charts."""
import pandas as pd
from matplotlib.figure import Figure


def fines_by_member(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["member_id", "member_name", "loans", "late_loans", "total_fine"])
    g = df.groupby(["member_id", "member_name"]).agg(
        loans=("loan_id", "count"),
        late_loans=("days_late", lambda s: int((s > 0).sum())),
        total_fine=("fine", "sum")).reset_index()
    return g.sort_values("total_fine", ascending=False)


def fines_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "total_fine", "late_loans"])
    d = df.copy()
    d["month"] = d["due_date"].dt.to_period("M").astype(str)
    g = d.groupby("month").agg(total_fine=("fine", "sum"),
                               late_loans=("days_late", lambda s: int((s > 0).sum()))).reset_index()
    return g.sort_values("month")


def detect_patterns(df: pd.DataFrame) -> list[str]:
    """Plain-language insights about fine behaviour."""
    if df.empty:
        return ["No loan data available."]
    out = []
    late = df[df["days_late"] > 0]
    out.append(f"{len(late)} of {len(df)} loans ({len(late)/len(df):.0%}) were/are late.")
    if late.empty:
        return out
    out.append(f"Average lateness: {late['days_late'].mean():.1f} days; longest: {late['days_late'].max()} days.")
    out.append(f"Total fines: Rs {df['fine'].sum():,.0f} "
               f"(Rs {df.loc[df['status']=='Overdue','fine'].sum():,.0f} still accruing on unreturned books).")
    m = fines_by_member(df)
    top = m.iloc[0]
    out.append(f"Highest fine: {top['member_name']} ({top['member_id']}) - Rs {top['total_fine']:,.0f}.")
    share = m.head(3)["total_fine"].sum() / max(m["total_fine"].sum(), 1)
    out.append(f"Top 3 members account for {share:.0%} of all fines.")
    repeat = m[m["late_loans"] >= 3]
    if not repeat.empty:
        names = ", ".join(repeat["member_name"].head(5))
        out.append(f"Repeat late borrowers (3+ late loans): {names}.")
    mo = fines_by_month(df)
    if len(mo):
        worst = mo.loc[mo["total_fine"].idxmax()]
        out.append(f"Worst month for fines: {worst['month']} (Rs {worst['total_fine']:,.0f}).")
    book = late.groupby("book_title")["days_late"].count().sort_values(ascending=False)
    if len(book):
        out.append(f"Book most often returned late: '{book.index[0]}' ({book.iloc[0]} times).")
    return out


# ---------- charts (return Figure objects so Tkinter and files can both use them) ----------
def chart_fines_by_member(df: pd.DataFrame, top_n: int = 10) -> Figure:
    fig = Figure(figsize=(7, 4.2), dpi=100)
    ax = fig.add_subplot(111)
    m = fines_by_member(df).head(top_n)
    m = m[m["total_fine"] > 0]
    if m.empty:
        ax.text(0.5, 0.5, "No fines to show", ha="center", va="center")
    else:
        labels = m["member_name"] + " (" + m["member_id"] + ")"
        ax.barh(labels[::-1], m["total_fine"][::-1], color="#c0392b")
        ax.set_xlabel("Total fine (Rs)")
    ax.set_title(f"Top {top_n} Members by Fines")
    fig.tight_layout()
    return fig


def chart_fines_by_month(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(7, 4.2), dpi=100)
    ax = fig.add_subplot(111)
    mo = fines_by_month(df)
    if mo.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        ax.bar(mo["month"], mo["total_fine"], color="#2980b9", label="Fine (Rs)")
        ax.set_ylabel("Fine (Rs)")
        ax2 = ax.twinx()
        ax2.plot(mo["month"], mo["late_loans"], color="#27ae60", marker="o", label="Late loans")
        ax2.set_ylabel("Late loans")
        ax.tick_params(axis="x", rotation=45)
    ax.set_title("Fines per Month (by due date)")
    fig.tight_layout()
    return fig


def chart_status_distribution(df: pd.DataFrame) -> Figure:
    fig = Figure(figsize=(5.5, 4.2), dpi=100)
    ax = fig.add_subplot(111)
    if df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        counts = df["status"].value_counts()
        colors = {"Returned": "#27ae60", "Borrowed": "#f39c12", "Overdue": "#c0392b"}
        ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%",
               colors=[colors.get(s, "#999") for s in counts.index])
    ax.set_title("Loan Status Distribution")
    fig.tight_layout()
    return fig


CHARTS = {"Fines by Member": chart_fines_by_member,
          "Fines per Month": chart_fines_by_month,
          "Status Distribution": chart_status_distribution}
