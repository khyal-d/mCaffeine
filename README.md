
# Shopify Product Importer – Mcaffeine Assignment  
### Developed by **Khyal Deware**

A complete Python-based command-line tool that automates syncing Shopify products from Excel/CSV using the **Shopify Admin GraphQL API (2025-10)**.  
It supports product creation, updates, variant syncing, image uploads, rate-limit recovery, and strict GraphQL mutation compliance.

---

## 🚀 Features

- End-to-end product sync via Shopify GraphQL Admin API  
- Safely creates or updates products  
- Prevents duplicate variants or images  
- Reads **.xlsx** and **.csv** files  
- Supports Title, Description, Type, Vendor, Tags, SKU, Price, Image URL  
- Smart variant matching (by SKU)  
- Uses `productVariantsBulkUpdate` for API correctness  
- Automatic retry on 429 rate-limit & Shopify server errors  
- `--dry-run` mode for safe previews  
- Modular, production-ready Python architecture  

---

## 🛠 Tech Stack

| Component | Technology |
|----------|------------|
| Language | Python 3.10+ |
| API | Shopify Admin GraphQL API (2025-10) |
| Data Processing | pandas + openpyxl |
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

Example:

```
SHOPIFY_SHOP=khyaldeware21je0471
```

---

## 📂 Input File Format

Your Excel/CSV file must contain:

| Column                 | Description          |
| ---------------------- | -------------------- |
| Handle                 | Shopify handle       |
| Title                  | Product title        |
| Body (HTML)            | Product description  |
| Type                   | Product type         |
| Vendor                 | Vendor/brand         |
| Tags                   | Comma-separated tags |
| Variant SKU            | Variant SKU          |
| Variant Price          | Variant price        |
| Option1 Value          | Variant option       |
| Image Src *(optional)* | Public image URL     |

### Example Row

```
coffee-mug, Coffee Mug, "<p>Nice mug</p>", Mugs, Brand A, kitchen, SKU001, 299, Default, https://example.com/mug.jpg
```

---

## ▶️ Running the Script

### Import products:

```bash
python shopify_import.py products.xlsx
```

### Import CSV:

```bash
python shopify_import.py products.csv
```

### Use specific Excel sheet:

```bash
python shopify_import.py products.xlsx --sheet Sheet1
```

### Dry-run (no API calls):

```bash
python shopify_import.py products.xlsx --dry-run
```

Example:

```
[DRY-RUN] Would create product 'Coffee Mug' (coffee-mug) + image
```

---

## 🔄 How Updates Work

### If product exists:

* Updates title, description, tags, vendor, type
* Matches variant using SKU
* Updates variant price
* Uploads image only if new

### If product does not exist:

* Creates product shell
* Creates/updates variant
* Uploads image

All variant updates use **productVariantsBulkUpdate**.

---

## 🧠 Error Handling

* Automatic exponential backoff on Shopify 429 errors
* Retries on 500/502/503/504
* Detects missing columns before execution
* Row-level isolation (other rows continue):

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

## ⭐ If this project helped you, please give it a star!

```

---

Just copy the block above into your GitHub `README.md` — nothing else needed.
```
