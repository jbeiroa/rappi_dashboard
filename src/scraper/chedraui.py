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
    Sets the location on Chedraui and extracts product prices using a robust text-based method.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 1000},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print(f"Navigating to Chedraui Mexico...")
        await page.goto("https://www.chedraui.com.mx/", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # 0. Handle Cookie Popup
        try:
            cookie_btn = page.get_by_role("button", name="Aceptar").first
            if await cookie_btn.is_visible():
                await cookie_btn.click()
                print("Accepted cookies.")
        except: pass

        # 1. Set Address/Location
        try:
            # ZIP Code (CP) extraction from address
            cp_match = re.search(r'\b\d{5}\b', address)
            cp = cp_match.group(0) if cp_match else "06000"
            
            # Click location trigger
            loc_trigger = page.locator("div[class*='header-location'], span[class*='location-text'], div[class*='vtex-address-manager']").first
            if await loc_trigger.is_visible():
                await loc_trigger.click()
                await page.wait_for_timeout(2000)

            cp_input = page.locator("input[placeholder*='código postal'], input[name*='zipCode'], input[id*='zipCode']").first
            if await cp_input.is_visible():
                await cp_input.fill(cp)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(4000)
            
            confirm_btn = page.locator("button:has-text('Confirmar'), button:has-text('Guardar'), button[class*='confirm']").first
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
                # Use UI search instead of direct URL which might be blocked or flaky
                search_input = page.get_by_placeholder("¿Qué estás buscando?").first
                if not await search_input.is_visible():
                    search_input = page.locator("input[id*='search'], input[class*='search']").first
                
                if await search_input.is_visible():
                    await search_input.click()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await search_input.fill(target)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(8000)
                else:
                    # Fallback to direct search URL
                    search_url = f"https://www.chedraui.com.mx/search?_query={target.replace(' ', '%20')}"
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                    await page.wait_for_timeout(8000)
                
                # Scroll to ensure rendering
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(2000)

                # Extract products using a more general locator (search for divs containing $)
                # Chedraui/VTEX structure is often deeply nested
                product_elements = await page.locator("div:has(h3, span):has-text('$')").all()
                scraped_products = []
                
                # Deduplicate and extract
                seen_names = set()
                for el in product_elements:
                    try:
                        text = await el.inner_text()
                        if "$" not in text or len(text) < 10: continue
                        
                        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
                        if not lines: continue
                        
                        name = lines[0]
                        if name in seen_names: continue
                        
                        prices = re.findall(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)', text.replace(',', ''))
                        prices = sorted(list(set([float(p) for p in prices])))
                        
                        if prices:
                            scraped_products.append({
                                "name": name,
                                "prices": prices,
                                "html_snippet": (await el.inner_html())[:500] if not headless else None
                            })
                            seen_names.add(name)
                    except: continue
                
                # Filter to most relevant candidates (those that mention target words)
                target_words = set(target.lower().split())
                candidates = [p for p in scraped_products if any(w in p["name"].lower() for w in target_words)]
                
                # Matching
                scraped_names = [p["name"] for p in candidates]
                match_res = process.extractOne(target, scraped_names, scorer=fuzz.WRatio) if scraped_names else None
                
                if match_res and match_res[1] > 65:
                    match = next(p for p in candidates if p["name"] == match_res[0])
                    price = min(match["prices"])
                    results.append({
                        "timestamp": timestamp, "app_name": "Chedraui", "store_name": "Chedraui Super",
                        "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                        "target_product": target, "scraped_product_name": match["name"],
                        "original_price": price, "final_price": price, "discount_amount": 0.0,
                        "delivery_fee": 0.0, "eta": 0, "html_snippet": match.get("html_snippet")
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
