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

async def scrape_didi_by_address(address: str, restaurant_name: str, target_products: List[str], headless: bool = True, lat: Optional[float] = None, lng: Optional[float] = None, city: str = "Unknown", municipality: str = "Unknown"):
    """
    Sets the address on Didi Food, searches for a restaurant, and extracts precise product prices.
    Returns a list of structured dictionaries for each target product found.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to Didi Food Mexico...")
        await page.goto("https://www.didiglobal.com/food/mx/", wait_until="domcontentloaded", timeout=60000)

        # 1. Set Address
        try:
            await page.wait_for_timeout(3000)
            # Find the address selector button/input
            # Often it's a div that looks like an input
            address_trigger = page.locator("div[class*='address'], div[class*='location'], span:has-text('Selecciona')").first
            if await address_trigger.is_visible():
                await address_trigger.click()
                await page.wait_for_timeout(2000)

            # In the modal or search bar
            address_input = page.get_by_placeholder("calle, número").first
            if not await address_input.is_visible():
                 address_input = page.locator("input[class*='input'], input[id*='location']").first

            await address_input.click()
            await address_input.fill(address)
            await page.wait_for_timeout(5000)
            
            # Autocomplete selection
            # Didi usually shows a list of addresses
            first_option = page.locator("div[class*='address-item'], div[class*='suggestion'], li[class*='item']").first
            if await first_option.count() > 0:
                await first_option.click()
            else:
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
            
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)
            print(f"Address set to: {address}")
        except Exception as e:
            print(f"Error setting address: {e}")

        # 2. Navigate to Restaurant Menu
        store_entered = False
        try:
            # Search for restaurant
            # Didi might have a search bar on the dashboard
            search_bar = page.locator("input[placeholder*='restaurante'], input[placeholder*='comida']").first
            if await search_bar.is_visible():
                await search_bar.fill("McDonalds")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(8000)
            else:
                # If no search bar, maybe we need to navigate to a search URL
                await page.goto(f"https://www.didiglobal.com/food/mx/search?q=McDonalds", wait_until="domcontentloaded")
                await page.wait_for_timeout(8000)
            
            # Find McDonald's card
            cards = await page.locator("a[href*='/store/'], div[class*='StoreCard'], div[class*='restaurant']").all()
            for card in cards:
                text = await card.inner_text()
                if "mcdonald" in text.lower():
                    await card.click()
                    store_entered = True
                    break
            
            if store_entered:
                await page.wait_for_timeout(10000)
                print(f"Final Store URL: {page.url}")
        except Exception as e:
            print(f"Error entering restaurant: {e}")

        if not store_entered:
            await browser.close()
            return []

        # 3. Extract Metrics (Fee/ETA)
        delivery_fee = None
        eta = None
        try:
            body_text = await page.inner_text("body")
            # Look for ETA like "15-25 min"
            eta_match = re.search(r'(\d+)\s*-\s*(\d+)\s*min', body_text)
            if eta_match: eta = int(eta_match.group(2))
            else:
                eta_match = re.search(r'(\d+)\s*min', body_text)
                if eta_match: eta = int(eta_match.group(1))

            # Look for fee like "$15.00" or "Envío gratis"
            if "gratis" in body_text.lower():
                delivery_fee = 0.0
            else:
                fee_match = re.search(r'Envío\s*\$\s*(\d+(?:\.\d+)?)', body_text, re.IGNORECASE)
                if fee_match: delivery_fee = float(fee_match.group(1))
        except: pass

        # 4. Extract Product Cards
        # Common selectors for Didi items
        cards = await page.locator("div[class*='item-card'], div[class*='product'], div[data-qa='item']").all()
        scraped_products = []
        for card in cards:
            try:
                text = await card.inner_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                if not lines: continue
                name = lines[0]
                prices = re.findall(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)', text.replace(',', ''))
                prices = sorted(list(set([float(p) for p in prices])))
                if not prices: continue
                scraped_products.append({"name": name, "prices": prices, "html_snippet": str(await card.inner_html())[:1000]})
            except: continue

        # 5. Matching (Fuzzy)
        results = []
        timestamp = datetime.now().isoformat()
        scraped_names = [p["name"] for p in scraped_products]
        
        for target in target_products:
            match_res = process.extractOne(target, scraped_names, scorer=fuzz.WRatio)
            if match_res and match_res[1] > 75:
                match = next(p for p in scraped_products if p["name"] == match_res[0])
                prices = match["prices"]
                final_price = min(prices)
                original_price = max(prices)
                results.append({
                    "timestamp": timestamp, "app_name": "Didi Food", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": match["name"],
                    "original_price": original_price, "final_price": final_price, "discount_amount": original_price - final_price,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": match["html_snippet"]
                })
            else:
                results.append({
                    "timestamp": timestamp, "app_name": "Didi Food", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": "Not Found",
                    "original_price": None, "final_price": None, "discount_amount": None,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": None
                })
        await browser.close()
        return results

def save_to_json(data: List[dict], filename: str = "data/raw/didi_products.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    existing_data = []
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: existing_data = json.load(f)
            except: pass
    existing_data.extend(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
