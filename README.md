# Smart Automated Invoice & Business Insight System — Web Edition

A professional browser-based billing and business analytics application built with **Python Flask + Excel + PDF**.

## Features
- Modern responsive browser dashboard
- KPI cards for sales, invoices, average invoice and GST
- Monthly sales and category-wise charts
- Product and stock management
- Customer management
- New invoice creation with cart
- Discount and GST calculation
- Automatic stock reduction after invoice creation
- PDF invoice generation
- Sales history
- Existing Excel files remain the data store

## Run in browser
1. Install Python 3.10+.
2. Open a terminal in this project folder.
3. Run:
   `pip install -r requirements.txt`
4. Start the browser version:
   `python run_browser.py`
5. The application opens at `http://127.0.0.1:5000`.

If the browser does not open automatically, manually visit the address above.

### Alternative
You can also run `python app.py` and then open `http://127.0.0.1:5000`.

Data is stored in `data/`. Generated invoices are stored in `invoices/`.
