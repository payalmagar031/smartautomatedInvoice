from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

def create_invoice_pdf(invoice_no, date, customer, items, subtotal, discount, gst, total):
    out = Path(__file__).parent / "invoices"
    out.mkdir(exist_ok=True)
    path = out / f"{invoice_no}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>SMART AUTOMATED INVOICE</b>", styles["Title"]),
        Paragraph(f"Invoice No: {invoice_no} &nbsp;&nbsp;&nbsp; Date: {date}", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(f"<b>Customer:</b> {customer}", styles["Normal"]),
        Spacer(1, 8),
    ]
    data = [["Product", "Qty", "Price", "Amount"]]
    for x in items:
        data.append([x["product"], x["qty"], f"₹{x['price']:.2f}", f"₹{x['amount']:.2f}"])
    data += [
        ["", "", "Subtotal", f"₹{subtotal:.2f}"],
        ["", "", "Discount", f"₹{discount:.2f}"],
        ["", "", "GST", f"₹{gst:.2f}"],
        ["", "", "Grand Total", f"₹{total:.2f}"],
    ]
    table = Table(data, colWidths=[90*mm, 20*mm, 35*mm, 35*mm])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), .5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME", (2,-4), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND", (2,-1), (-1,-1), colors.whitesmoke),
        ("BOTTOMPADDING", (0,0), (-1,0), 7),
        ("TOPPADDING", (0,0), (-1,0), 7),
    ]))
    story.append(table)
    story += [Spacer(1, 15), Paragraph("Thank you for your business.", styles["Normal"])]
    doc.build(story)
    return path
