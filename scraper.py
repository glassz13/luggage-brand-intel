import asyncio
import json
import random
import os
import csv
import hashlib
import re
from datetime import datetime
from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────────
BRANDS = ["Safari", "Skybags", "American Tourister", "VIP", "Aristocrat"]
MAX_PRODUCTS = 15
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")

BRAND_KEYWORDS = {
    "Safari": ["safari"],
    "Skybags": ["skybags"],
    "American Tourister": ["american tourister", "tourister", "kamiliant"],
    "VIP": ["vip"],
    "Aristocrat": ["aristocrat"],
}

# ── Helpers ───────────────────────────────────────────────────────────────────
async def human_delay(a=2.0, b=4.0):
    await asyncio.sleep(random.uniform(a, b))

async def safe_text(el, sel):
    try:
        e = await el.query_selector(sel)
        return (await e.inner_text()).strip() if e else ""
    except Exception:
        return ""

def brand_match(title, brand):
    t = title.lower()
    return any(k in t for k in BRAND_KEYWORDS.get(brand, [brand.lower()]))

def get_size(title):
    m = re.search(r'(\d{2,3})\s*(cm|l\b|ltr)', title.lower())
    if m:
        return f"{m.group(1)}{m.group(2).strip()}"
    for k in ["cabin", "check-in", "small", "medium", "large", "xl"]:
        if k in title.lower():
            return k.capitalize()
    return "Unknown"

def is_combo(title):
    return any(k in title.lower() for k in ["set of 2", "set of 3", "combo", "pack of"])

def rhash(text):
    return hashlib.md5(text.strip().lower().encode()).hexdigest()[:12]

def now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def save_csv(data, fname):
    if not data:
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, fname)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  Saved {len(data)} rows -> {fname}")

def save_json(data, fname):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved JSON -> {fname}")

# ── Step 1: Search ────────────────────────────────────────────────────────────
async def search_products(page, brand, seen_asins):
    products = []
    base_url = "https://www.amazon.in/s?k=" + brand.replace(" ", "+") + "+luggage+trolley"
    print(f"\n{'='*55}")
    print(f"[{brand}] Searching...")

    for pn in range(1, 4):
        if len(products) >= MAX_PRODUCTS:
            break

        url = base_url if pn == 1 else base_url + f"&page={pn}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"  Page load error: {e}")
            continue

        if "signin" in page.url:
            print("  Login wall. Log into Amazon in Edge and rerun.")
            return []

        cards = await page.query_selector_all("div[data-component-type='s-search-result']")
        print(f"  Page {pn} -> {len(cards)} cards")

        for card in cards:
            if len(products) >= MAX_PRODUCTS:
                break
            try:
                asin = await card.get_attribute("data-asin") or ""
                if not asin or asin in seen_asins:
                    continue

                title = await safe_text(card, "h2 span")
                if not title or not brand_match(title, brand):
                    continue

                pw = await safe_text(card, "span.a-price-whole")
                pf = await safe_text(card, "span.a-price-fraction")
                mrp_raw = await safe_text(card, "span.a-price.a-text-price span.a-offscreen")
                rating_raw = await safe_text(card, "span.a-icon-alt")

                try:
                    price = float(f"{pw}{pf}".replace(",", "")) if pw else None
                except ValueError:
                    price = None

                try:
                    mrp = float(mrp_raw.replace("₹", "").replace(",", "")) if mrp_raw else None
                except ValueError:
                    mrp = None

                try:
                    rating = float(rating_raw.split()[0]) if rating_raw else None
                except ValueError:
                    rating = None

                discount = round(((mrp - price) / mrp) * 100, 1) if price and mrp else None

                products.append({
                    "brand": brand,
                    "asin": asin,
                    "title": "",
                    "luggage_size": "",
                    "is_combo": False,
                    "price": price,
                    "mrp": mrp,
                    "discount_pct": discount,
                    "rating": rating,
                    "review_count": None,
                    "scraped_at": now()
                })
                seen_asins.add(asin)
                print(f"  + {asin} | {title[:55]}")

            except Exception:
                continue

        await human_delay(3, 5)

    print(f"  -> {len(products)} products collected")
    return products


# ── Step 2: Reviews (also fills title, size, review_count) ───────────────────
async def scrape_reviews(page, product, seen_hashes):
    asin = product["asin"]
    brand = product["brand"]
    reviews = []
    url = (
        f"https://www.amazon.in/product-reviews/{asin}"
        f"?ie=UTF8&reviewerType=all_reviews&sortBy=recent"
    )

    for attempt in range(1, 4):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            await page.evaluate("window.scrollTo(0, 500)")
            await page.wait_for_timeout(2000)

            if "signin" in page.url or "ap/signin" in page.url:
                print(f"  Login wall for {asin}.")
                return reviews

            if await page.query_selector("form[action='/errors/validateCaptcha']"):
                if attempt < 3:
                    wait = attempt * 20
                    print(f"  CAPTCHA - waiting {wait}s (attempt {attempt}/3)...")
                    await asyncio.sleep(wait)
                    continue
                else:
                    print(f"  CAPTCHA persists. Skipping {asin}.")
                    return reviews

            # Fill product meta while we are on this page
            title = await safe_text(page, "a[data-hook='product-link']")
            if title:
                product["title"] = title
                product["luggage_size"] = get_size(title)
                product["is_combo"] = is_combo(title)

            count_raw = await safe_text(page, "div[data-hook='total-review-count'] span")
            if not count_raw:
                count_raw = await safe_text(page, "span[data-hook='total-review-count']")
            count_digits = re.sub(r"[^\d]", "", count_raw)
            product["review_count"] = int(count_digits) if count_digits else None

            try:
                await page.wait_for_selector("li[data-hook='review']", timeout=8000)
            except Exception:
                print(f"  No reviews for {asin}.")
                return reviews

            review_cards = await page.query_selector_all("li[data-hook='review']")
            new_count = 0

            for card in review_cards:
                try:
                    star_el = await card.query_selector(
                        "i[data-hook='review-star-rating'] span.a-icon-alt"
                    )
                    if not star_el:
                        star_el = await card.query_selector(
                            "i[data-hook='cmps-review-star-rating'] span.a-icon-alt"
                        )

                    try:
                        stars = float((await star_el.inner_text()).split()[0]) if star_el else None
                    except ValueError:
                        stars = None

                    body = await safe_text(card, "span[data-hook='review-body'] span")
                    if not body:
                        continue

                    h = rhash(body)
                    if h in seen_hashes:
                        continue
                    seen_hashes.add(h)

                    verified = bool(await card.query_selector("span[data-hook='avp-badge']"))

                    reviews.append({
                        "brand": brand,
                        "asin": asin,
                        "star_rating": stars,
                        "review_body": body.strip(),
                        "verified_purchase": verified,
                        "review_hash": h,
                        "scraped_at": now()
                    })
                    new_count += 1

                except Exception:
                    continue

            print(f"  [{asin}] {new_count} reviews | {product['title'][:50]}")
            return reviews

        except Exception as e:
            print(f"  Attempt {attempt} error for {asin}: {e}")
            if attempt < 3:
                await asyncio.sleep(attempt * 5)

    return reviews


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_products = []
    all_reviews = []
    seen_asins = set()
    seen_hashes = set()

    edge_path = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            edge_path,
            channel="msedge",
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = await ctx.new_page()

        for brand in BRANDS:
            products = await search_products(page, brand, seen_asins)
            await human_delay(5, 8)

            for product in products:
                print(f"\n-- {brand} | {product['asin']} --")
                reviews = await scrape_reviews(page, product, seen_hashes)

                if not product["title"]:
                    print("  No title fetched. Skipping.")
                    continue

                all_products.append(product)
                all_reviews.extend(reviews)

                print(f"  Reviews: {len(reviews)} | Running total: {len(all_reviews)}")

                save_csv(all_products, "products_final.csv")
                save_csv(all_reviews, "reviews_final.csv")

                await human_delay(4, 7)

        await ctx.close()

    save_json(all_products, "products_final.json")
    save_json(all_reviews, "reviews_final.json")

    import pandas as pd
    df_p = pd.DataFrame(all_products) if all_products else pd.DataFrame()
    df_r = pd.DataFrame(all_reviews) if all_reviews else pd.DataFrame()

    print(f"\n{'='*50}")
    print(f"DONE")
    print(f"{'='*50}")
    print(f"Products : {len(all_products)}")
    print(f"Reviews  : {len(all_reviews)}")

    if not df_p.empty:
        print(f"\nProducts per brand:\n{df_p.groupby('brand').size().to_string()}")
        print(f"\nReviews per brand:\n{df_r.groupby('brand').size().to_string()}")
        print(f"\nSize distribution:\n{df_p['luggage_size'].value_counts().to_string()}")
        print(f"\nCombos: {df_p['is_combo'].sum()}")

if __name__ == "__main__":
    asyncio.run(main())
    