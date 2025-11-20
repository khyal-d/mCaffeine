
# Shopify Product Importer – Mcaffeine Assignment  
### Developed by **Khyal Deware**

A complete Python-based command-line tool that automates syncing Shopify products from Excel/CSV using the **Shopify Admin GraphQL API (2025-10)**.  
It supports product creation, updates, variant syncing, image uploads, rate-limit handling, and strict GraphQL mutation compliance.

---

## 🚀 Features

- End-to-end product sync via Shopify GraphQL Admin API  
- Automatically creates or updates products  
- Prevents duplicate variants and images  
- Reads **.xlsx** and **.csv** files  
- Supports Title, Description, Vendor, Tags, SKU, Price, Image URL  
- Smart variant matching via SKU  
- Uses `productVariantsBulkUpdate` for strict mutation updates  
- Automatic retry on 429 rate-limit and Shopify 5xx errors  
- `--dry-run` mode to preview actions  
- Clean, modular Python architecture  

---

## 🛠 Tech Stack

| Component | Technology |
|----------|------------|
| Language | Python 3.10+ |
| API | Shopify Admin GraphQL API (2025-10) |
| Data Processing | pandas, openpyxl |
| Networking | requests |
| Env Management | python-dotenv |

---

## 📦 Installation

```bash
pip install -r requirements.txt
````

---

## 🔧 Environment Setup

Create a `.env` file:

```
SHOPIFY_SHOP=yourshopname
SHOPIFY_ADMIN_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2025-10
```

Example used:

```
SHOPIFY_SHOP=khyaldeware21je0471
```

---

## 📂 Input File Format

| Column        | Description                 |
| ------------- | --------------------------- |
| Handle        | Unique Shopify handle       |
| Title         | Product title               |
| Body (HTML)   | Product description         |
| Type          | Product type                |
| Vendor        | Vendor name                 |
| Tags          | Comma-separated tags        |
| Variant SKU   | SKU identifier              |
| Variant Price | Price                       |
| Option1 Value | Variant option              |
| Image Src     | Public image URL (optional) |

### Example Row

```
coffee-mug, Coffee Mug, "<p>Nice mug</p>", Mugs, Brand A, kitchen, SKU001, 299, Default, https://example.com/mug.jpg
```

---

## ▶️ Running the Script

### 1️⃣ Basic command (actual import)

```bash
python shopify_import.py products.xlsx
```

### 2️⃣ Run CSV file

```bash
python shopify_import.py products.csv
```

### 3️⃣ Use a specific Excel sheet

```bash
python shopify_import.py products.xlsx --sheet Sheet1
```

### 4️⃣ Dry-run (no API calls, preview only)

```bash
python shopify_import.py products.xlsx --dry-run
```

### ✔️ Actual run after dry-run

Use this command to perform the real Shopify import:

```bash
python shopify_import.py products.xlsx
```

---

## 🔄 How Updates Work

### If product exists:

* Updates title, body_html, vendor, productType, tags
* Matches variant by SKU
* Updates variant price
* Uploads image only if new

### If product does NOT exist:

* Creates a new product
* Creates/updates variant
* Uploads image if provided

Variant updates follow Shopify’s strict `productVariantsBulkUpdate` mutation.

---

## 🧠 Error Handling

* Automatic exponential backoff on 429 rate limits
* Shopify 500/502/503/504 retry logic
* Detects missing columns before processing
* Row-level failure isolation:

```
Row 3 failed: productVariantsBulkUpdate errors: Invalid price
```

---

## 🛠 Code Structure

```
shopify_import.py
│
├── get_env()
├── read_products_from_file()
├── get_product_by_handle()
├── build_product_input()
├── build_variant_update_input()
├── product_create()
├── product_update()
├── variant_update()
└── process_row()
```

---

## 📁 Project Structure

```
.
├── shopify_import.py
├── products.xlsx
├── products_export_l (I).csv
├── requirements.txt
├── .env
└── venv/
```

---

## 👨‍💻 Author

**Khyal Deware**
Python Developer • Shopify Automation • API Engineering

---

## ⭐ If this project helps you, please give it a star!

```
