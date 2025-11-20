import os
import time
import argparse
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

REQUIRED_ENV = ["SHOPIFY_SHOP", "SHOPIFY_ADMIN_TOKEN", "SHOPIFY_API_VERSION"]


def get_env():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k, "").strip()]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)} in .env")

    shop = os.environ["SHOPIFY_SHOP"].strip()
    token = os.environ["SHOPIFY_ADMIN_TOKEN"].strip()
    version = os.environ["SHOPIFY_API_VERSION"].strip()
    endpoint = f"https://{shop}.myshopify.com/admin/api/{version}/graphql.json"
    return endpoint, token


def graphql_request(query, variables, endpoint, token, max_retries=5):
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token,
    }
    payload = {"query": query, "variables": variables}

    backoff = 1
    for _ in range(max_retries):
        resp = requests.post(endpoint, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if "errors" in data:
                raise RuntimeError(f"GraphQL errors: {data['errors']}")
            return data["data"]

        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(backoff)
            backoff = min(backoff * 2, 16)
            continue

        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

    raise RuntimeError("Max retries exceeded for GraphQL request")


def read_products_from_file(path: str, sheet: str | None = None):
    ext = os.path.splitext(path)[1].lower()

    if ext in (".xlsx", ".xls"):
        # If no sheet is specified, use the first sheet (index 0)
        sheet_arg = 0 if sheet is None else sheet
        df = pd.read_excel(path, sheet_name=sheet_arg)
    elif ext == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    required_cols = [
        "Handle",
        "Title",
        "Body (HTML)",
        "Type",
        "Vendor",
        "Tags",
        "Variant SKU",
        "Variant Price",
        "Option1 Value",
    ]

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in file: {', '.join(missing)}")

    df = df.fillna("")
    return df



def get_product_by_handle(handle: str, endpoint: str, token: str):
    query = """
    query GetProductByHandle($handle: String!) {
      productByHandle(handle: $handle) {
        id
        title
        handle
        variants(first: 50) {
          edges {
            node {
              id
              sku
              price
              title
            }
          }
        }
        images(first: 50) {
          edges {
            node {
              id
              src
            }
          }
        }
      }
    }
    """
    vars_ = {"handle": handle}
    data = graphql_request(query, vars_, endpoint, token)
    return data.get("productByHandle")



def build_product_input(row, existing_product=None):
    tags_str = str(row["Tags"]).strip()
    tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]

    product_input = {
        "title": str(row["Title"]).strip(),
        "handle": str(row["Handle"]).strip(),
        "descriptionHtml": str(row["Body (HTML)"]).strip(),
        "productType": str(row["Type"]).strip(),
        "vendor": str(row["Vendor"]).strip(),
        "tags": tags_list,
    }

    if existing_product:
        product_input["id"] = existing_product["id"]

    return product_input


def build_variant_update_input(product: dict, row) -> dict | None:
    variant_sku = str(row["Variant SKU"]).strip()
    variant_price = str(row["Variant Price"]).strip()

    edges = product.get("variants", {}).get("edges", [])
    if not edges:
        return None

    variant_id = None

    if variant_sku:
        for edge in edges:
            node = edge["node"]
            if node.get("sku") == variant_sku:
                variant_id = node["id"]
                break

    if not variant_id:
        variant_id = edges[0]["node"]["id"]

    # Only use fields allowed in ProductVariantsBulkInput
    variant_input = {
        "id": variant_id,
    }

    if variant_price:
        variant_input["price"] = str(variant_price)

    if variant_sku:
        variant_input["sku"] = variant_sku

    return variant_input



def collect_image_srcs(product: dict | None):
    srcs = set()
    if not product:
        return srcs
    images = product.get("images", {}).get("edges", [])
    for edge in images:
        node = edge["node"]
        if node.get("src"):
            srcs.add(node["src"])
    return srcs


def create_product_image(product_id: str, image_src: str, endpoint: str, token: str):
    query = """
    mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
      productCreateMedia(productId: $productId, media: $media) {
        media {
          preview {
            image {
              url
            }
          }
        }
        mediaUserErrors {
          field
          message
        }
      }
    }
    """

    variables = {
        "productId": product_id,
        "media": [{
            "originalSource": image_src,
            "mediaContentType": "IMAGE"
        }]
    }

    data = graphql_request(query, variables, endpoint, token)
    result = data["productCreateMedia"]

    errors = result.get("mediaUserErrors", [])
    if errors:
        raise RuntimeError(f"productCreateMedia errors: {errors}")

    return result["media"]


def product_create(product_input: dict, endpoint: str, token: str, row, image_src: str | None) -> dict:
    query = """
    mutation CreateProduct($input: ProductInput!) {
      productCreate(input: $input) {
        product {
          id
          title
          handle
          variants(first: 20) {
            edges {
              node {
                id
                sku
                price
                title
              }
            }
          }
          images(first: 20) {
            edges {
              node {
                id
                src
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    vars_ = {"input": product_input}
    data = graphql_request(query, vars_, endpoint, token)
    result = data["productCreate"]
    errors = result.get("userErrors", [])
    if errors:
        raise RuntimeError(f"productCreate errors: {errors}")

    product = result["product"]

    v_input = build_variant_update_input(product, row)
    if v_input:
        variant_update(product["id"], v_input, endpoint, token)


    if image_src:
        existing_srcs = collect_image_srcs(product)
        if image_src not in existing_srcs:
            create_product_image(product["id"], image_src, endpoint, token)

    return product



def product_update(product_input: dict, existing_product: dict, endpoint: str, token: str, row, image_src: str | None) -> dict:
    query = """
    mutation UpdateProduct($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          id
          title
          handle
          variants(first: 20) {
            edges {
              node {
                id
                sku
                price
                title
              }
            }
          }
          images(first: 20) {
            edges {
              node {
                id
                src
              }
            }
          }
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    vars_ = {"input": product_input}
    data = graphql_request(query, vars_, endpoint, token)
    result = data["productUpdate"]
    errors = result.get("userErrors", [])
    if errors:
        raise RuntimeError(f"productUpdate errors: {errors}")

    product = result["product"]

    v_input = build_variant_update_input(product, row)
    if not v_input and existing_product:
        v_input = build_variant_update_input(existing_product, row)

    if v_input:
        # use the product id that matches the variant we built
        product_id_for_variant = product["id"] if v_input["id"].startswith("gid://shopify/ProductVariant") else existing_product["id"]
        variant_update(product_id_for_variant, v_input, endpoint, token)


    if image_src:
        existing_srcs = collect_image_srcs(existing_product)
        existing_srcs.update(collect_image_srcs(product))
        if image_src not in existing_srcs:
            create_product_image(product["id"], image_src, endpoint, token)

    return product



def variant_update(product_id: str, variant_input: dict, endpoint: str, token: str) -> dict:
    query = """
    mutation UpdateVariant($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
      productVariantsBulkUpdate(productId: $productId, variants: $variants) {
        productVariants {
          id
          sku
          price
          title
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    vars_ = {
        "productId": product_id,
        "variants": [variant_input],
    }
    data = graphql_request(query, vars_, endpoint, token)
    result = data["productVariantsBulkUpdate"]
    errors = result.get("userErrors", [])
    if errors:
        raise RuntimeError(f"productVariantsBulkUpdate errors: {errors}")
    # we only updated one variant, so return the first
    return result["productVariants"][0]



def process_row(row, endpoint, token, dry_run=False):
    handle = str(row["Handle"]).strip()
    if not handle:
        raise ValueError("Each row must have a 'Handle' value")

    image_src = str(row.get("Image Src", "")).strip()

    existing = get_product_by_handle(handle, endpoint, token)
    product_input = build_product_input(row, existing_product=existing)

    if dry_run:
        action = "update" if existing else "create"
        extra = " + image" if image_src else ""
        print(f"[DRY-RUN] Would {action} product '{product_input['title']}' ({handle}){extra}")
        return

    if existing:
        p = product_update(product_input, existing, endpoint, token, row, image_src)
        print(f"Updated product: {p['title']} ({p['id']})")
    else:
        p = product_create(product_input, endpoint, token, row, image_src)
        print(f"Created product: {p['title']} ({p['id']})")



def main():
    parser = argparse.ArgumentParser(
        description="Import/update Shopify products from Excel/CSV via GraphQL Admin API."
    )
    parser.add_argument("file_path", help="Path to .xlsx or .csv file")
    parser.add_argument("--sheet", help="Sheet name (for Excel)", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Just print what would be done, without calling Shopify",
    )
    args = parser.parse_args()

    endpoint, token = get_env()
    df = read_products_from_file(args.file_path, args.sheet)

    for idx, row in df.iterrows():
        try:
            process_row(row, endpoint, token, dry_run=args.dry_run)
        except Exception as e:
            print(f"Row {idx} failed: {e}")


if __name__ == "__main__":
    main()

