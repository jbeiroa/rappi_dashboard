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

async def scrape_chedraui_by_address(address: str, target_products: List[str], headless: bool = True, lat: Optional[float] = None, lng: Optional[float] = None, city: str = "Unknown", municipality: str = "Unknown"):
    """
    Sets the location on Chedraui and extracts product prices.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to Chedraui Mexico...")
        await page.goto("https://www.chedraui.com.mx/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # 1. Set Address/Location
        try:
            # Handle initial delivery type modal if it appears
            # Look for "Enviar a domicilio" or similar
            delivery_btn = page.locator("button:has-text('Enviar a domicilio'), div:has-text('Enviar a domicilio')").first
            if await delivery_btn.is_visible():
                await delivery_btn.click()
                await page.wait_for_timeout(2000)

            # ZIP Code (CP) extraction
            cp_match = re.search(r'\b\d{5}\b', address)
            cp = cp_match.group(0) if cp_match else "06000"
            
            cp_input = page.locator("input[placeholder*='código postal'], input[name*='zipCode']").first
            if await cp_input.is_visible():
                await cp_input.fill(cp)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(4000)
            
            # Confirm button if any
            confirm_btn = page.locator("button:has-text('Confirmar'), button:has-text('Guardar')").first
            if await confirm_btn.is_visible():
                await confirm_btn.click()
                await page.wait_for_timeout(3000)

            print(f"Location set to CP: {cp}")
        except Exception as e:
            print(f"Error setting location: {e}")

        # 2. Search and Scrape
        timestamp = datetime.now().isoformat()
        results = []
        
        for target in target_products:
            try:
                print(f"Searching for {target}...")
                # Search using the site's internal search parameter
                search_url = f"https://www.chedraui.com.mx/search?_query={target.replace(' ', '%20')}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(6000)
                
                # Scroll to ensure load
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(2000)

                # Extract products from search results
                # Common VTEX selectors
                cards = await page.locator("div[class*='product-summary'], div[class*='vtex-product-summary'], div[class*='product-item']").all()
                scraped_products = []
                for card in cards:
                    try:
                        text = await card.inner_text()
                        if "$" not in text: continue
                        
                        # Name usually in a span or h3
                        name_el = card.locator("span[class*='brandName'], h3[class*='productName'], span[class*='productBrand']").first
                        name = await name_el.inner_text() if await name_el.count() > 0 else text.split('\n')[0]
                        
                        # Price extraction
                        prices = re.findall(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)', text.replace(',', ''))
                        prices = sorted(list(set([float(p) for p in prices])))
                        
                        if prices and len(name) > 3:
                            scraped_products.append({
                                "name": name,
                                "prices": prices,
                                "html_snippet": str(await card.inner_html())[:500]
                            })
                    except: continue
                
                # Match
                scraped_names = [p["name"] for p in scraped_products]
                match_res = process.extractOne(target, scraped_names, scorer=fuzz.WRatio)
                
                if match_res and match_res[1] > 70:
                    match = next(p for p in scraped_products if p["name"] == match_res[0])
                    price = min(match["prices"])
                    results.append({
                        "timestamp": timestamp, "app_name": "Chedraui", "store_name": "Chedraui Super",
                        "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                        "target_product": target, "scraped_product_name": match["name"],
                        "original_price": price, "final_price": price, "discount_amount": 0.0,
                        "delivery_fee": 0.0, "eta": 0, "html_snippet": match["html_snippet"]
                    })
                else:
                    results.append({
                        "timestamp": timestamp, "app_name": "Chedraui", "store_name": "Chedraui Super",
                        "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                        "target_product": target, "scraped_product_name": "Not Found",
                        "original_price": None, "final_price": None, "discount_amount": None,
                        "delivery_fee": None, "eta": None, "html_snippet": None
                    })
            except Exception as e:
                print(f"Error scraping {target}: {e}")
                
        await browser.close()
        return results

def save_to_json(data: List[dict], filename: Optional[str] = None):
    if filename is None:
        filename = "data/raw/chedraui_products.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    existing_data = []
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: existing_data = json.load(f)
            except: pass
    existing_data.extend(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
