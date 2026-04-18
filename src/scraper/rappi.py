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

async def scrape_rappi_by_address(address: str, restaurant_name: str, target_products: List[str], headless: bool = True, lat: Optional[float] = None, lng: Optional[float] = None, city: str = "Unknown", municipality: str = "Unknown"):
    """
    Sets the address on Rappi, searches for a restaurant, and extracts precise product prices.
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
        
        print(f"Navigating to Rappi Mexico...")
        await page.goto("https://www.rappi.com.mx/", wait_until="domcontentloaded", timeout=60000)

        # 1. Set Address
        try:
            await page.wait_for_timeout(3000)
            try:
                # Handle initial popups
                await page.get_by_text("Ok, entendido", exact=False).first.click(timeout=3000)
            except: pass

            address_input = page.get_by_placeholder("¿Dónde quieres recibir tu compra?").first
            if not await address_input.is_visible():
                city_btn = page.get_by_text("Ciudad de México", exact=False).first
                if await city_btn.is_visible(): await city_btn.click()
                address_input = page.get_by_placeholder("¿Dónde quieres recibir tu compra?").first

            await address_input.click()
            await address_input.fill(address)
            await page.wait_for_timeout(4000)
            
            # Select first autocomplete specifically
            first_option = page.locator("div[class*='AddressList'], ul li, div[data-qa='address-item']").first
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
            # Search for "McDonalds" (more common in URLs/tags)
            search_query = "McDonalds"
            search_url = f"https://www.rappi.com.mx/busqueda?query={search_query}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(10000)
            
            # Helper to find store link
            async def find_store():
                # Check for "McDonald" in any link
                links = await page.locator("a[href*='/restaurantes/']").all()
                for link in links:
                    inner_text = await link.inner_text()
                    href = await link.get_attribute("href")
                    if "mcdonald" in inner_text.lower() or "mcdonald" in href.lower():
                        return link
                return None

            target = await find_store()
            if target:
                await target.click()
                store_entered = True
            else:
                print(f"Restaurant {restaurant_name} not found in search results.")
            
            if store_entered:
                await page.wait_for_timeout(10000)
                # Handle hub pages
                if "/delivery/" in page.url or "/brand/" in page.url or "busqueda" in page.url:
                    store_link = page.locator("a[href*='/restaurantes/']").first
                    if await store_link.count() > 0:
                        await store_link.click()
                        await page.wait_for_timeout(8000)
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
            eta_match = re.search(r'(\d+)\s*(?:-)\s*(\d+)\s*min', body_text)
            if eta_match: eta = int(eta_match.group(2))
            else:
                eta_match = re.search(r'(\d+)\s*min', body_text, re.IGNORECASE)
                eta = int(eta_match.group(1)) if eta_match else None
            
            if any(term in body_text.lower() for term in ["envío gratis", "entrega gratis", "envío $ 0"]):
                delivery_fee = 0.0
            else:
                fee_match = re.search(r'Envío[^$]*\$\s*(\d+(?:\.\d+)?)', body_text, re.IGNORECASE)
                if not fee_match: fee_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', body_text)
                delivery_fee = float(fee_match.group(1)) if fee_match else None
        except: pass

        # Scroll to load menu items
        for _ in range(4):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(2000)

        # 4. Extract Product Cards
        cards = await page.locator("div[data-qa^='product-item-'], div[data-testid^='product-item-']").all()
        scraped_products = []
        for card in cards:
            try:
                text = await card.inner_text()
                name_el = card.locator("h4, h3, span").first
                name = await name_el.inner_text()
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
                discount_amount = original_price - final_price
                results.append({
                    "timestamp": timestamp, "app_name": "Rappi", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": match["name"],
                    "original_price": original_price, "final_price": final_price, "discount_amount": discount_amount,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": match["html_snippet"]
                })
            else:
                results.append({
                    "timestamp": timestamp, "app_name": "Rappi", "store_name": restaurant_name,
                    "full_address": address, "lat": lat, "lng": lng, "city": city, "municipality": municipality,
                    "target_product": target, "scraped_product_name": "Not Found",
                    "original_price": None, "final_price": None, "discount_amount": None,
                    "delivery_fee": delivery_fee, "eta": eta, "html_snippet": None
                })
        await browser.close()
        return results

async def get_available_products(address: str, restaurant_name: str, count: int = 3, headless: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto("https://www.rappi.com.mx/", wait_until="domcontentloaded")
        try:
            addr_input = page.get_by_placeholder("¿Dónde quieres recibir tu compra?").first
            await addr_input.fill(address)
            await page.wait_for_timeout(4000)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(6000)
            search_url = f"https://www.rappi.com.mx/busqueda?query=McDonalds"
            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(8000)
            link = page.locator("a[href*='/restaurantes/']").first
            if await link.count() > 0:
                await link.click()
                await page.wait_for_timeout(10000)
                names = await page.locator("h4").all_inner_texts()
                valid_names = [n.strip() for n in names if len(n.strip()) > 3][:count]
                await browser.close()
                return valid_names
        except: pass
        await browser.close()
        return []

def save_to_json(data: List[dict], filename: Optional[str] = None):
    if filename is None:
        filename = "data/raw/rappi_products.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    existing_data = []
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try: existing_data = json.load(f)
            except: pass
    existing_data.extend(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
