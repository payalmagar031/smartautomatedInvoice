from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from datetime import datetime
from pathlib import Path
import pandas as pd

from database import *
from invoice import create_invoice_pdf

app = Flask(__name__)
app.secret_key = "smart-invoice-dashboard-secret"


def cart_items():
    return session.get("cart", [])


def set_cart(items):
    session["cart"] = items
    session.modified = True


def dashboard_data():
    sales = rows("sales")
    details = rows("details")
    products = get_products()
    revenue = sum(float(r[6] or 0) for r in sales)
    gst = sum(float(r[5] or 0) for r in sales)
    avg = revenue / len(sales) if sales else 0
    low = sum(1 for r in products if float(r[4] or 0) <= 5)
    top_product = "—"
    top_category = "—"
    monthly_labels, monthly_values = [], []
    category_labels, category_values = [], []
    if details:
        d = pd.DataFrame(details, columns=HEADERS["details"])
        d["Amount"] = pd.to_numeric(d["Amount"], errors="coerce").fillna(0)
        prod = d.groupby("Product")["Amount"].sum().sort_values(ascending=False)
        cat = d.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        if len(prod): top_product = prod.index[0]
        if len(cat):
            top_category = cat.index[0]
            category_labels = cat.index.tolist()
            category_values = [round(float(v), 2) for v in cat.values]
    if sales:
        s = pd.DataFrame(sales, columns=HEADERS["sales"])
        s["Date"] = pd.to_datetime(s["Date"], errors="coerce")
        s["Grand Total"] = pd.to_numeric(s["Grand Total"], errors="coerce").fillna(0)
        monthly = s.dropna(subset=["Date"]).groupby(s["Date"].dt.to_period("M"))["Grand Total"].sum()
        monthly_labels = [str(x) for x in monthly.index]
        monthly_values = [round(float(v), 2) for v in monthly.values]
    return {
        "revenue": revenue, "gst": gst, "avg": avg, "invoices": len(sales),
        "low": low, "top_product": top_product, "top_category": top_category,
        "monthly_labels": monthly_labels, "monthly_values": monthly_values,
        "category_labels": category_labels, "category_values": category_values,
        "products": products, "customers": get_customers()
    }


@app.context_processor
def inject_globals():
    return {"app_name": "Smart Invoice", "cart_count": len(cart_items())}


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", data=dashboard_data(), active="dashboard")


@app.route("/products", methods=["GET", "POST"])
def products():
    if request.method == "POST":
        try:
            pid = request.form.get("product_id", "").strip() or next_id("products", "P")
            if find_product(pid):
                raise ValueError("Product ID already exists.")
            name = request.form.get("product", "").strip()
            category = request.form.get("category", "").strip()
            price = float(request.form.get("price", 0))
            stock = int(float(request.form.get("stock", 0)))
            if not name or not category: raise ValueError("Product and category are required.")
            if price < 0 or stock < 0: raise ValueError("Price and stock cannot be negative.")
            append_row("products", [pid, name, category, price, stock])
            flash("Product added successfully.", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("products"))
    return render_template("products.html", products=get_products(), active="products")


@app.route("/customers", methods=["GET", "POST"])
def customers():
    if request.method == "POST":
        try:
            name = request.form.get("customer_name", "").strip()
            if not name: raise ValueError("Customer name is required.")
            cid = request.form.get("customer_id", "").strip() or next_id("customers", "C")
            if any(str(r[0]) == cid for r in get_customers()):
                raise ValueError("Customer ID already exists.")
            append_row("customers", [cid, name, request.form.get("mobile", "").strip(),
                                      request.form.get("email", "").strip(), request.form.get("address", "").strip()])
            flash("Customer added successfully.", "success")
        except Exception as e:
            flash(str(e), "error")
        return redirect(url_for("customers"))
    return render_template("customers.html", customers=get_customers(), active="customers")


@app.route("/invoice", methods=["GET", "POST"])
def invoice():
    if request.method == "POST":
        action = request.form.get("action")
        cart = cart_items()
        if action == "add":
            try:
                pid = request.form.get("product_id", "").strip()
                p = find_product(pid)
                if not p: raise ValueError("Select a product.")
                qty = float(request.form.get("qty", 1))
                stock = float(p[4] or 0)
                already = sum(float(x["qty"]) for x in cart if x["product_id"] == pid)
                if qty <= 0 or already + qty > stock:
                    raise ValueError(f"Available stock: {stock:g}")
                cart.append({"product_id": pid, "product": p[1], "category": p[2],
                             "qty": qty, "price": float(p[3]), "amount": qty * float(p[3])})
                set_cart(cart)
                flash("Item added to invoice.", "success")
            except Exception as e:
                flash(str(e), "error")
            return redirect(url_for("invoice"))
        if action == "remove":
            try:
                idx = int(request.form.get("index"))
                if 0 <= idx < len(cart): cart.pop(idx)
                set_cart(cart)
            except Exception: pass
            return redirect(url_for("invoice"))
        if action == "save":
            try:
                if not cart: raise ValueError("Add at least one product.")
                customer = request.form.get("customer", "")
                if not customer: raise ValueError("Select a customer.")
                subtotal = sum(x["amount"] for x in cart)
                discount = max(0, float(request.form.get("discount", 0)))
                gst_rate = max(0, float(request.form.get("gst", 18)))
                taxable = max(0, subtotal - discount)
                gst = taxable * gst_rate / 100
                total = taxable + gst
                inv = next_invoice()
                date = datetime.now().strftime("%Y-%m-%d %H:%M")
                cname = customer.split(" - ", 1)[1] if " - " in customer else customer
                append_row("sales", [inv, date, cname, subtotal, discount, gst, total])
                for x in cart:
                    append_row("details", [inv, date, x["product_id"], x["product"], x["category"], x["qty"], x["price"], x["amount"]])
                    update_stock(x["product_id"], x["qty"])
                path = create_invoice_pdf(inv, date, cname, cart, subtotal, discount, gst, total)
                set_cart([])
                flash(f"Invoice {inv} created successfully.", "success")
                return redirect(url_for("invoice_pdf", filename=path.name))
            except Exception as e:
                flash(str(e), "error")
            return redirect(url_for("invoice"))
    subtotal = sum(x["amount"] for x in cart_items())
    discount = 0
    gst = 0
    taxable = subtotal
    total = subtotal
    return render_template("invoice.html", products=get_products(), customers=get_customers(),
                           cart=cart_items(), subtotal=subtotal, discount=discount, gst=gst, total=total,
                           invoice_no=next_invoice(), active="invoice")


@app.route("/invoice/pdf/<filename>")
def invoice_pdf(filename):
    path = Path(__file__).parent / "invoices" / filename
    if not path.exists():
        flash("Invoice PDF not found.", "error")
        return redirect(url_for("sales"))
    return send_file(path, as_attachment=False, download_name=filename)


@app.route("/sales")
def sales():
    return render_template("sales.html", sales=rows("sales"), active="sales")


@app.route("/refresh")
def refresh():
    return redirect(request.referrer or url_for("dashboard"))


if __name__ == "__main__":
    ensure_files()
    app.run(host="127.0.0.1", port=5000, debug=True)
