import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import pandas as pd
from datetime import datetime
import os
import re
import json
from typing import List, Dict
from rapidfuzz import process, fuzz

async def scrape_rappi_by_address(address: str, restaurant_name: str, target_products: List[str], headless: bool = True):
    """
    Sets the address on Rappi, searches for a restaurant, and extracts precise product prices.
    Returns a list of structured dictionaries for each target product found.
    """
    # Parse address components (Assuming format: "Zone, Municipality, State")
    address_parts = [p.strip() for p in address.split(',')]
    zone = address_parts[0] if len(address_parts) > 0 else "N/A"
    municipality = address_parts[1] if len(address_parts) > 1 else "N/A"
    state = address_parts[2] if len(address_parts) > 2 else "N/A"
    country = "México"

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
                await page.get_by_text("Ok, entendido", exact=False).first.click(timeout=3000)
            except:
                pass

            address_input = page.get_by_placeholder("¿Dónde quieres recibir tu compra?").first
            if not await address_input.is_visible():
                await page.get_by_text("Ciudad de México").first.click()
                address_input = page.get_by_placeholder("¿Dónde quieres recibir tu compra?").first

            await address_input.click()
            # Special case for the Polanco address to ensure match
            target_addr = address if "Calle Polanco" in address else "Calle Polanco, Polanco V Sección 11560 Miguel Hidalgo, Ciudad de México"
            if address != "Calle Polanco, Polanco V Sección 11560 Miguel Hidalgo":
                 target_addr = address
            
            await address_input.fill(target_addr)
            await page.wait_for_timeout(3000)
            
            await page.keyboard.press("ArrowDown")
            await page.wait_for_timeout(500)
            await page.keyboard.press("Enter")
            
            await page.wait_for_load_state("networkidle", timeout=30000)
            print(f"Address set to: {target_addr}")
        except Exception as e:
            print(f"Error setting address: {e}")

        # 2. Navigate to Restaurant Menu
        try:
            print(f"Searching for {restaurant_name}...")
            search_query = "Mc Donald's" if "mcdonald" in restaurant_name.lower() else restaurant_name
            search_url = f"https://www.rappi.com.mx/busqueda?query={search_query.replace(' ', '%20')}"
            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(10000)
            
            # Helper to find a specific store link on the current page
            async def get_specific_store_link():
                links = await page.locator("a[href*='/restaurantes/']").all()
                for link in links:
                    href = await link.get_attribute("href")
                    # Specific stores have numeric IDs > 5 digits and NO /delivery/ or /brand/ or /category/
                    if re.search(r"/restaurantes/\d{5,}-", href) and not any(x in href for x in ["/delivery/", "/brand/", "/category/", "/tag/"]):
                        return link
                return None

            target_link = await get_specific_store_link()
            
            if target_link:
                print(f"Clicking specific store link: {await target_link.get_attribute('href')}")
                await target_link.click()
            else:
                if "/delivery/" in page.url or "/brand/" in page.url:
                    print("Landed on brand hub, looking for specific store link on this page...")
                    await page.wait_for_timeout(5000)
                    target_link = await get_specific_store_link()
                    if target_link:
                         print(f"Clicking store from hub: {await target_link.get_attribute('href')}")
                         await target_link.click()
                    else:
                         await page.get_by_text("Menú", exact=False).first.click()
                else:
                    print("No numeric store link found. Trying text match fallback...")
                    await page.get_by_text(restaurant_name, exact=False).first.click()

            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(15000)
            
            # Final check: if we are still on a hub, try one more time to enter a store
            if "/delivery/" in page.url or "/brand/" in page.url:
                 print("Still on hub page. Attempting one last redirect to specific store...")
                 links = await page.locator("a[href*='/restaurantes/']").all()
                 for link in links:
                      href = await link.get_attribute("href")
                      if re.search(r"/restaurantes/\d{5,}-", href) and "/delivery/" not in href:
                           await page.goto(f"https://www.rappi.com.mx{href}" if href.startswith("/") else href)
                           break

            print(f"Final Store URL: {page.url}")
        except Exception as e:
            print(f"Error entering restaurant: {e}")

        # 3. Extract Precise Metrics
        delivery_fee = None
        eta = None
        
        try:
            # User Full XPath: /html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/div[1]
            full_xpath = '/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/div[1]'
            header_locator = page.locator(f"xpath={full_xpath}")
            
            if await header_locator.count() > 0 and await header_locator.is_visible(timeout=10000):
                header_text = await header_locator.inner_text()
            else:
                print("Full XPath not found, trying user's short XPath fallback...")
                short_xpath = '//*[@id="restaurantLayoutContainer"]/div[2]/div[2]/div[2]'
                header_locator = page.locator(f"xpath={short_xpath}")
                if await header_locator.count() > 0 and await header_locator.is_visible(timeout=5000):
                    header_text = await header_locator.inner_text()
                else:
                    print("XPaths failed, searching page content for ETA/Fee patterns...")
                    header_text = await page.inner_text("body")
            
            # Extract ETA
            eta_match = re.search(r'(\d+)\s*min', header_text, re.IGNORECASE)
            eta = int(eta_match.group(1)) if eta_match else None
            
            # Extract Delivery Fee
            if any(term in header_text.lower() for term in ["gratis", "free"]):
                delivery_fee = 0.0
            else:
                fee_match = re.search(r'Envío[^$]*\$\s*(\d+(?:\.\d+)?)', header_text, re.IGNORECASE)
                if not fee_match:
                    fee_match = re.search(r'\$\s*(\d+(?:\.\d+)?)', header_text)
                delivery_fee = float(fee_match.group(1)) if fee_match else None
                
        except Exception as e:
            print(f"Error in header extraction: {e}")

        # Scroll to load menu items
        for _ in range(3):
            await page.mouse.wheel(0, 1500)
            await page.wait_for_timeout(2000)

        # Get all product cards
        cards = await page.locator("div[data-qa^='product-item-'], div[data-testid^='product-item-']").all()
        print(f"Found {len(cards)} product cards.")

        scraped_products = []
        for card in cards:
            try:
                text = await card.inner_text()
                parts = [p.strip() for p in text.split('\n') if p.strip()]
                name = await card.locator("h4").inner_text() if await card.locator("h4").count() > 0 else parts[0]
                # Clean comma for numeric parsing
                prices = re.findall(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)', text.replace(',', ''))
                prices = [float(p) for p in prices]
                
                scraped_products.append({
                    "name": name,
                    "prices": sorted(prices),
                    "raw_text": text,
                    "html_snippet": str(await card.inner_html())[:1000]
                })
            except:
                continue

        results = []
        timestamp = datetime.now().isoformat()
        
        # Match target products
        for target in target_products:
            match_res = process.extractOne(target, [p["name"] for p in scraped_products], scorer=fuzz.WRatio)
            
            if match_res and match_res[1] > 80:
                best_match = next(p for p in scraped_products if p["name"] == match_res[0])
                prices = best_match["prices"]
                
                if len(prices) >= 2:
                    final_price = min(prices)
                    original_price = max(prices)
                elif len(prices) == 1:
                    final_price = prices[0]
                    original_price = prices[0]
                else:
                    final_price = None
                    original_price = None
                    
                discount_amount = original_price - final_price if original_price is not None and final_price is not None else 0.0
                
                record = {
                    "timestamp": timestamp,
                    "app_name": "Rappi",
                    "store_name": restaurant_name,
                    "full_address": address,
                    "zone": zone,
                    "municipality": municipality,
                    "state": state,
                    "country": country,
                    "target_product": target,
                    "scraped_product_name": best_match["name"],
                    "original_price": original_price,
                    "final_price": final_price,
                    "discount_amount": discount_amount,
                    "delivery_fee": delivery_fee,
                    "eta": eta,
                    "html_snippet": best_match["html_snippet"]
                }
                results.append(record)
            else:
                record = {
                    "timestamp": timestamp,
                    "app_name": "Rappi",
                    "store_name": restaurant_name,
                    "full_address": address,
                    "zone": zone,
                    "municipality": municipality,
                    "state": state,
                    "country": country,
                    "target_product": target,
                    "scraped_product_name": "Not Found",
                    "original_price": None,
                    "final_price": None,
                    "discount_amount": None,
                    "delivery_fee": delivery_fee,
                    "eta": eta,
                    "html_snippet": None
                }
                results.append(record)

        await browser.close()
        return results

def save_to_json(data: List[dict], filename: str = "data/raw/rappi_products.json"):
    """
    Saves a list of dictionaries to a JSON file (appending to existing array).
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    existing_data = []
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
                
    existing_data.extend(data)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
        
    print(f"Data appended to {filename}")

def save_to_csv(data: List[dict], filename: str = "data/raw/rappi_scrape.csv"):
    """
    Saves a list of dictionaries to a CSV file (appending to existing).
    """
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.isfile(filename):
        df.to_csv(filename, index=False)
    else:
        existing_df = pd.read_csv(filename)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
