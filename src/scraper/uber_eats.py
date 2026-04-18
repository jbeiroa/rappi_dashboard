import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import pandas as pd
from datetime import datetime
import os
import re
import json
from typing import List, Dict, Optional
from rapidfuzz import process, fuzz

async def scrape_uber_eats_by_address(address: str, restaurant_name: str, target_products: List[str], headless: bool = True, lat: Optional[float] = None, lng: Optional[float] = None, city: str = "Unknown", municipality: str = "Unknown"):
    """
    Sets the address on Uber Eats, searches for a restaurant, and extracts precise product prices.
    Returns a list of structured dictionaries for each target product found.
    """
    def normalize(text):
        return re.sub(r'\s+', ' ', text.strip().lower()).replace('®', '').replace('™', '')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1000},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to Uber Eats Mexico...")
        await page.goto("https://www.ubereats.com/mx", wait_until="domcontentloaded", timeout=60000)

        # 1. Set Address
        try:
            address_input_selector = "input#location-typeahead-home-input"
            
            if not await page.is_visible(address_input_selector):
                header_loc = page.locator("button[aria-label*='ubicación'], button[aria-label*='location']").first
                if await header_loc.is_visible():
                    await header_loc.click()
                    address_input_selector = "input#location-typeahead-search-input"

            await page.wait_for_selector(address_input_selector, timeout=15000)
            await page.fill(address_input_selector, address)
            await page.wait_for_timeout(4000)
            
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(1000)
            await page.keyboard.press("Enter")
            
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            print(f"Address set to: {address}")
        except Exception as e:
            print(f"Error setting address: {e}")

        # 2. Navigate to Restaurant Menu
        try:
            search_query = restaurant_name
            search_url = f"https://www.ubereats.com/mx/search?q={search_query.replace(' ', '%20')}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(8000)
            
            store_links = await page.locator("a[href*='/mx/store/']").all()
            target_store_url = None
            for link in store_links:
                href = await link.get_attribute("href")
                inner_text = await link.inner_text()
                if "/store/" in href and not any(x in href.lower() for x in ["/category/", "/brand/", "/tag/"]) and \
                   (restaurant_name.lower().replace("'", "") in inner_text.lower().replace("'", "") or \
                    restaurant_name.lower().replace("'", "") in href.lower()):
                    target_store_url = f"https://www.ubereats.com{href}" if href.startswith("/") else href
                    break
            
            if target_store_url:
                await page.goto(target_store_url, wait_until="domcontentloaded", timeout=60000)
            else:
                await page.get_by_text(restaurant_name, exact=False).first.click()

            await page.wait_for_timeout(10000)
            print(f"Final Store URL: {page.url}")
        except Exception as e:
            print(f"Error entering restaurant: {e}")

        # 3. Extract Metrics (Fee/ETA)
        delivery_fee = None
        eta = None
        try:
            body_text = await page.inner_text("body")
            
            # ETA: "10 min" or "10-20 min"
            eta_match = re.search(r'(\d+)\s*[–-]\s*(\d+)\s*min', body_text)
            if eta_match: eta = int(eta_match.group(2))
            else:
                eta_match = re.search(r'(\d+)\s*min', body_text, re.IGNORECASE)
                eta = int(eta_match.group(1)) if eta_match else None
            
            # Fee: "Costo de envío: MXN17.00" or "$15" or "Gratis"
            if any(term in body_text.lower() for term in ["costo de envío: $0", "envío gratis", "entrega gratis", "mxn0"]):
                delivery_fee = 0.0
            else:
                # Look for MXN or $ near "costo de envío"
                # Updated regex to handle potentially missing decimals or MXN prefix
                fee_match = re.search(r'(?:costo de envío|envío)[^$MXN]*(?:mxn|[\$])\s*(\d+(?:[\.,]\d+)?)', body_text, re.IGNORECASE)
                if fee_match:
                    fee_str = fee_match.group(1).replace(',', '')
                    delivery_fee = float(fee_str)
                    # Heuristic: if fee is > 500 and no decimal, it might be cents (e.g., 1700 -> 17.00)
                    if delivery_fee > 500 and '.' not in fee_str:
                        delivery_fee = delivery_fee / 100
                else:
                    # Last resort fallback
                    fee_match = re.search(r'(?:mxn|[\$])\s*(\d+(?:[\.,]\d+)?)', body_text, re.IGNORECASE)
                    if fee_match: delivery_fee = float(fee_match.group(1).replace(',', ''))
        except: pass

        # Scroll to load menu items
        for _ in range(5):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(2000)

        # 4. Extract Product Cards
        cards = await page.locator("[data-testid^='store-item-'], [data-testid='rich-item'], [data-testid='menu-item']").all()
        scraped_products = []
        for card in cards:
            try:
                text = await card.inner_text()
                if not text or "$" not in text.lower(): continue
                
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                # Stricter valid lines
                valid_lines = [l for l in lines if not any(x in l.lower() for x in ["popular", "nuevo", "más pedido", "vegetariano", "min", "calif", "ahorra", "promo"])]
                if not valid_lines: continue
                
                name = valid_lines[0]
                # Improved price regex
                prices = re.findall(r'(?:mxn|[\$])\s*(\d+(?:[\.,]\d+)?)', text.replace(',', '').lower())
                prices = sorted(list(set([float(p) for p in prices])))
                
                if not prices or len(name) < 3: continue
                
                scraped_products.append({
                    "name": name,
                    "prices": prices,
                    "html_snippet": str(await card.inner_html())[:1000]
                })
            except: continue

        # 5. Matching (Consistent with Rappi)
        results = []
        timestamp = datetime.now().isoformat()
        scraped_names = [p["name"] for p in scraped_products]
        
        for target in target_products:
            # Use WRatio as in Rappi
            match_res = process.extractOne(target, scraped_names, scorer=fuzz.WRatio)
            
            if match_res and match_res[1] > 80:
                match = next(p for p in scraped_products if p["name"] == match_res[0])
                prices = match["prices"]
                final_price = min(prices)
                original_price = max(prices)
                
                results.append({
                    "timestamp": timestamp, "app_name": "Uber Eats", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": match["name"],
                    "original_price": original_price, "final_price": final_price, "discount_amount": original_price - final_price,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": match["html_snippet"]
                })
            else:
                results.append({
                    "timestamp": timestamp, "app_name": "Uber Eats", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": "Not Found",
                    "original_price": None, "final_price": None, "discount_amount": None,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": None
                })

        await browser.close()
        return results

def save_to_json(data: List[dict], filename: Optional[str] = None):
    if filename is None:
        filename = "data/raw/uber_products.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    existing_data = []
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: existing_data = json.load(f)
            except: pass
    existing_data.extend(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
