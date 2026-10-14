import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def make_charts(sales_rows, detail_rows):
    report_dir = Path(__file__).parent / "reports"
    report_dir.mkdir(exist_ok=True)
    if sales_rows:
        df = pd.DataFrame(sales_rows, columns=["Invoice No","Date","Customer","Subtotal","Discount","GST","Grand Total"])
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Grand Total"] = pd.to_numeric(df["Grand Total"], errors="coerce").fillna(0)
        monthly = df.groupby(df["Date"].dt.to_period("M"))["Grand Total"].sum()
        if len(monthly):
            plt.figure(figsize=(8,4))
            monthly.plot(kind="bar")
            plt.title("Monthly Sales")
            plt.xlabel("Month"); plt.ylabel("Sales")
            plt.tight_layout()
            p1 = report_dir/"monthly_sales.png"; plt.savefig(p1); plt.close()
        else: p1 = None
    else: p1 = None

    if detail_rows:
        dd = pd.DataFrame(detail_rows, columns=["Invoice No","Date","Product ID","Product","Category","Qty","Price","Amount"])
        dd["Amount"] = pd.to_numeric(dd["Amount"], errors="coerce").fillna(0)
        cat = dd.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        if len(cat):
            plt.figure(figsize=(8,4))
            cat.plot(kind="bar")
            plt.title("Category-wise Sales")
            plt.xlabel("Category"); plt.ylabel("Sales")
            plt.tight_layout()
            p2 = report_dir/"category_sales.png"; plt.savefig(p2); plt.close()
        else: p2 = None
    else: p2 = None
    return p1, p2
