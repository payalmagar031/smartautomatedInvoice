import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import webbrowser
from database import *
from invoice import create_invoice_pdf
from dashboard import make_charts

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Automated Invoice & Business Insight System")
        self.geometry("1200x760")
        self.minsize(1050, 680)
        ensure_files()
        self.cart = []
        self.build()
        self.refresh_all()

    def build(self):
        header = tk.Frame(self, bg="#1f4e78", height=70)
        header.pack(fill="x")
        tk.Label(header, text="SMART AUTOMATED INVOICE & BUSINESS INSIGHT SYSTEM",
                 bg="#1f4e78", fg="white", font=("Arial", 19, "bold")).pack(pady=20)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.dashboard_tab = ttk.Frame(self.nb)
        self.product_tab = ttk.Frame(self.nb)
        self.customer_tab = ttk.Frame(self.nb)
        self.invoice_tab = ttk.Frame(self.nb)
        self.sales_tab = ttk.Frame(self.nb)
        self.nb.add(self.dashboard_tab, text="Dashboard")
        self.nb.add(self.product_tab, text="Products")
        self.nb.add(self.customer_tab, text="Customers")
        self.nb.add(self.invoice_tab, text="New Invoice")
        self.nb.add(self.sales_tab, text="Sales History")
        self.build_dashboard(); self.build_products(); self.build_customers()
        self.build_invoice(); self.build_sales()

    def clear(self, parent):
        for w in parent.winfo_children(): w.destroy()

    def build_dashboard(self):
        self.clear(self.dashboard_tab)
        rows = rows_sales = globals()["rows"]("sales")
        details = globals()["rows"]("details")
        products = get_products()
        revenue = sum(float(r[6] or 0) for r in rows_sales)
        gst = sum(float(r[5] or 0) for r in rows_sales)
        inv = len(rows_sales)
        avg = revenue/inv if inv else 0
        low = sum(1 for r in products if float(r[4] or 0) <= 5)
        cards = tk.Frame(self.dashboard_tab); cards.pack(fill="x", pady=15)
        for title, val in [("Total Sales", f"₹{revenue:,.2f}"), ("Invoices", str(inv)),
                           ("Average Invoice", f"₹{avg:,.2f}"), ("GST Collected", f"₹{gst:,.2f}"),
                           ("Low Stock Items", str(low))]:
            c=tk.LabelFrame(cards,text=title,padx=25,pady=15)
            c.pack(side="left",fill="x",expand=True,padx=5)
            tk.Label(c,text=val,font=("Arial",16,"bold")).pack()
        ttk.Button(self.dashboard_tab,text="Refresh Dashboard",command=self.refresh_dashboard).pack(pady=8)
        if rows_sales:
            top = tk.LabelFrame(self.dashboard_tab, text="Quick Insights", padx=15,pady=15)
            top.pack(fill="both",expand=True,pady=10)
            self.insight = tk.Text(top,height=14,font=("Arial",11))
            self.insight.pack(fill="both",expand=True)
            self.write_insights(rows_sales, details)

    def write_insights(self, sales, details):
        import pandas as pd
        self.insight.delete("1.0","end")
        total=sum(float(r[6] or 0) for r in sales)
        self.insight.insert("end", f"Revenue: ₹{total:,.2f}\n")
        if details:
            d=pd.DataFrame(details,columns=HEADERS["details"])
            d["Amount"]=pd.to_numeric(d["Amount"],errors="coerce").fillna(0)
            d["Qty"]=pd.to_numeric(d["Qty"],errors="coerce").fillna(0)
            prod=d.groupby("Product")["Amount"].sum().sort_values(ascending=False)
            cat=d.groupby("Category")["Amount"].sum().sort_values(ascending=False)
            if len(prod): self.insight.insert("end", f"Top Product by Sales Value: {prod.index[0]} (₹{prod.iloc[0]:,.2f})\n")
            if len(cat): self.insight.insert("end", f"Top Category by Sales Value: {cat.index[0]} (₹{cat.iloc[0]:,.2f})\n")
        self.insight.insert("end", "\nUse the New Invoice tab to create bills and automatically update Excel.\n")

    def refresh_dashboard(self):
        self.build_dashboard()

    def build_products(self):
        f=self.product_tab
        form=tk.Frame(f); form.pack(fill="x",pady=10)
        self.pvars=[tk.StringVar() for _ in range(5)]
        labels=["Product ID","Product","Category","Price","Stock"]
        for i,l in enumerate(labels):
            tk.Label(form,text=l).grid(row=0,column=i,padx=5)
            tk.Entry(form,textvariable=self.pvars[i],width=18).grid(row=1,column=i,padx=5)
        ttk.Button(form,text="Add Product",command=self.add_product).grid(row=1,column=5,padx=8)
        ttk.Button(form,text="Refresh",command=self.refresh_products).grid(row=1,column=6)
        self.ptree=ttk.Treeview(f,columns=labels,show="headings")
        for l in labels: self.ptree.heading(l,text=l); self.ptree.column(l,width=150)
        self.ptree.pack(fill="both",expand=True,padx=10,pady=10)

    def add_product(self):
        try:
            pid=self.pvars[0].get().strip() or next_id("products","P")
            if find_product(pid): raise ValueError("Product ID already exists")
            row=[pid,self.pvars[1].get().strip(),self.pvars[2].get().strip(),float(self.pvars[3].get()),int(float(self.pvars[4].get()))]
            if not row[1] or not row[2]: raise ValueError("Enter product and category")
            append_row("products",row)
            self.refresh_products()
            for v in self.pvars: v.set("")
            messagebox.showinfo("Saved","Product added successfully.")
        except Exception as e: messagebox.showerror("Error",str(e))

    def refresh_products(self):
        for x in self.ptree.get_children(): self.ptree.delete(x)
        for r in get_products(): self.ptree.insert("", "end", values=r)

    def build_customers(self):
        f=self.customer_tab
        form=tk.Frame(f); form.pack(fill="x",pady=10)
        self.cvars=[tk.StringVar() for _ in range(5)]
        labels=["Customer ID","Customer Name","Mobile","Email","Address"]
        for i,l in enumerate(labels):
            tk.Label(form,text=l).grid(row=0,column=i,padx=5)
            tk.Entry(form,textvariable=self.cvars[i],width=20).grid(row=1,column=i,padx=5)
        ttk.Button(form,text="Add Customer",command=self.add_customer).grid(row=1,column=5,padx=8)
        ttk.Button(form,text="Refresh",command=self.refresh_customers).grid(row=1,column=6)
        self.ctree=ttk.Treeview(f,columns=labels,show="headings")
        for l in labels: self.ctree.heading(l,text=l); self.ctree.column(l,width=150)
        self.ctree.pack(fill="both",expand=True,padx=10,pady=10)

    def add_customer(self):
        if not self.cvars[1].get().strip():
            messagebox.showerror("Error","Customer name is required."); return
        cid=self.cvars[0].get().strip() or next_id("customers","C")
        if any(str(r[0])==cid for r in get_customers()):
            messagebox.showerror("Error","Customer ID already exists."); return
        append_row("customers",[cid]+[v.get().strip() for v in self.cvars[1:]])
        self.refresh_customers()
        for v in self.cvars: v.set("")
        messagebox.showinfo("Saved","Customer added successfully.")

    def refresh_customers(self):
        for x in self.ctree.get_children(): self.ctree.delete(x)
        for r in get_customers(): self.ctree.insert("", "end", values=r)

    def build_invoice(self):
        f=self.invoice_tab
        top=tk.Frame(f); top.pack(fill="x",pady=10)
        self.customer_var=tk.StringVar()
        self.product_var=tk.StringVar()
        self.qty_var=tk.StringVar(value="1")
        self.discount_var=tk.StringVar(value="0")
        self.gst_var=tk.StringVar(value="18")
        self.inv_label=tk.StringVar(value=next_invoice())
        tk.Label(top,text="Invoice:").grid(row=0,column=0,padx=5)
        tk.Label(top,textvariable=self.inv_label,font=("Arial",11,"bold")).grid(row=0,column=1,padx=5)
        tk.Label(top,text="Customer").grid(row=0,column=2,padx=5)
        self.cc=ttk.Combobox(top,textvariable=self.customer_var,width=30,state="readonly")
        self.cc.grid(row=0,column=3,padx=5)
        tk.Label(top,text="Product").grid(row=1,column=0,pady=8)
        self.pc=ttk.Combobox(top,textvariable=self.product_var,width=35,state="readonly")
        self.pc.grid(row=1,column=1,columnspan=2,padx=5)
        tk.Label(top,text="Qty").grid(row=1,column=3)
        tk.Entry(top,textvariable=self.qty_var,width=8).grid(row=1,column=4)
        ttk.Button(top,text="Add to Invoice",command=self.add_to_cart).grid(row=1,column=5,padx=10)
        treeframe=tk.Frame(f); treeframe.pack(fill="both",expand=True,padx=10)
        cols=("Product","Qty","Price","Amount")
        self.itree=ttk.Treeview(treeframe,columns=cols,show="headings",height=12)
        for c in cols: self.itree.heading(c,text=c); self.itree.column(c,width=180)
        self.itree.pack(fill="both",expand=True)
        bottom=tk.Frame(f); bottom.pack(fill="x",pady=10)
        tk.Label(bottom,text="Discount ₹").pack(side="left")
        tk.Entry(bottom,textvariable=self.discount_var,width=10).pack(side="left",padx=5)
        tk.Label(bottom,text="GST %").pack(side="left")
        tk.Entry(bottom,textvariable=self.gst_var,width=7).pack(side="left",padx=5)
        ttk.Button(bottom,text="Remove Selected",command=self.remove_cart).pack(side="left",padx=15)
        ttk.Button(bottom,text="Generate Invoice PDF & Save",command=self.save_invoice).pack(side="right",padx=5)
        self.total_label=tk.Label(f,text="Subtotal: ₹0.00    GST: ₹0.00    Grand Total: ₹0.00",font=("Arial",14,"bold"))
        self.total_label.pack(pady=5)

    def refresh_invoice_lists(self):
        self.cc["values"]=[f"{r[0]} - {r[1]}" for r in get_customers()]
        self.pc["values"]=[f"{r[0]} - {r[1]}" for r in get_products()]
        self.inv_label.set(next_invoice())

    def add_to_cart(self):
        try:
            pid=self.product_var.get().split(" - ",1)[0]
            p=find_product(pid)
            if not p: raise ValueError("Select a product")
            qty=float(self.qty_var.get())
            stock=float(p[4] or 0)
            already=sum(x["qty"] for x in self.cart if x["product_id"]==pid)
            if qty<=0 or already+qty>stock: raise ValueError(f"Available stock: {stock}")
            item={"product_id":pid,"product":p[1],"category":p[2],"qty":qty,"price":float(p[3]),"amount":qty*float(p[3])}
            self.cart.append(item)
            self.refresh_cart()
        except Exception as e: messagebox.showerror("Error",str(e))

    def refresh_cart(self):
        for x in self.itree.get_children(): self.itree.delete(x)
        for x in self.cart: self.itree.insert("", "end",values=(x["product"],x["qty"],f"₹{x['price']:.2f}",f"₹{x['amount']:.2f}"))
        subtotal=sum(x["amount"] for x in self.cart)
        discount=max(0,float(self.discount_var.get() or 0))
        taxable=max(0,subtotal-discount)
        gst=taxable*float(self.gst_var.get() or 0)/100
        self.total_label.config(text=f"Subtotal: ₹{subtotal:,.2f}    GST: ₹{gst:,.2f}    Grand Total: ₹{taxable+gst:,.2f}")

    def remove_cart(self):
        sel=self.itree.selection()
        if sel:
            idx=self.itree.index(sel[0]); self.cart.pop(idx); self.refresh_cart()

    def save_invoice(self):
        try:
            if not self.cart: raise ValueError("Add at least one product.")
            cust=self.customer_var.get()
            if not cust: raise ValueError("Select a customer.")
            subtotal=sum(x["amount"] for x in self.cart)
            discount=max(0,float(self.discount_var.get() or 0))
            taxable=max(0,subtotal-discount)
            gst=taxable*float(self.gst_var.get() or 0)/100
            total=taxable+gst
            inv=self.inv_label.get()
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
            cname=cust.split(" - ",1)[1] if " - " in cust else cust
            append_row("sales",[inv,date,cname,subtotal,discount,gst,total])
            for x in self.cart:
                append_row("details",[inv,date,x["product_id"],x["product"],x["category"],x["qty"],x["price"],x["amount"]])
                update_stock(x["product_id"],x["qty"])
            path=create_invoice_pdf(inv,date,cname,self.cart,subtotal,discount,gst,total)
            messagebox.showinfo("Invoice Saved",f"Invoice saved successfully.\nPDF: {path}")
            self.cart=[]; self.refresh_cart(); self.refresh_all()
        except Exception as e: messagebox.showerror("Error",str(e))

    def build_sales(self):
        f=self.sales_tab
        ttk.Button(f,text="Refresh Sales",command=self.refresh_sales).pack(pady=8)
        self.stree=ttk.Treeview(f,columns=HEADERS["sales"],show="headings")
        for c in HEADERS["sales"]: self.stree.heading(c,text=c); self.stree.column(c,width=145)
        self.stree.pack(fill="both",expand=True,padx=10,pady=10)
        ttk.Button(f,text="Generate Charts",command=self.charts).pack(pady=5)

    def refresh_sales(self):
        for x in self.stree.get_children(): self.stree.delete(x)
        for r in globals()["rows"]("sales"): self.stree.insert("", "end",values=r)

    def charts(self):
        p1,p2=make_charts(globals()["rows"]("sales"),globals()["rows"]("details"))
        paths=[p for p in (p1,p2) if p]
        if paths:
            for p in paths: webbrowser.open(p.resolve().as_uri())
        else: messagebox.showinfo("Charts","No sales data available yet.")

    def refresh_all(self):
        self.refresh_products(); self.refresh_customers(); self.refresh_sales(); self.refresh_invoice_lists()

if __name__=="__main__":
    App().mainloop()
