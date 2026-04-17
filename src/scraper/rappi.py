import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
import re
from typing import List, Dict

async def scrape_rappi_by_address(address: str, restaurant_name: str, products: List[str], headless: bool = True):
    """
    Sets the address on Rappi, searches for a restaurant, and extracts product prices.
    Uses regex and card-based extraction for better reliability.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
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
            await address_input.fill(address)
            await page.wait_for_timeout(3000)
            
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            
            await page.wait_for_load_state("networkidle", timeout=30000)
            print(f"Address set to: {address}")
        except Exception as e:
            print(f"Error setting address: {e}")

        # 2. Search for Restaurant
        try:
            search_url = f"https://www.rappi.com.mx/busqueda?query={restaurant_name.replace(' ', '%20')}"
            print(f"Navigating to search URL: {search_url}")
            await page.goto(search_url, wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(5000)
            
            restaurant_card = page.locator("[data-testid=\"store-card\"], [data-qa=\"store-item\"], a[href*=\"restaurantes\"]").first
            if await restaurant_card.is_visible():
                await restaurant_card.click()
            else:
                await page.get_by_text(restaurant_name, exact=False).first.click()
            
            await page.wait_for_load_state("networkidle", timeout=30000)
            print(f"Entered restaurant page: {restaurant_name}")
        except Exception as e:
            print(f"Error searching for restaurant: {e}")

        # 3. Extract Product Prices
        data = {
            "timestamp": datetime.now().isoformat(),
            "address": address,
            "restaurant_name": restaurant_name,
        }
        
        try:
            await page.wait_for_timeout(5000)
            # Find elements containing price-like patterns or specific labels
            header_text = await page.locator("header, div[class*='header']").first.inner_text()
            # Try to extract ETA and Delivery Fee from header text
            eta_match = re.search(r'(\d+)\s*min', header_text)
            data["eta"] = f"{eta_match.group(1)} min" if eta_match else "N/A"
            
            fee_match = re.search(r'Envío\s*:\s*\$\s*(\d+)', header_text)
            data["delivery_fee"] = f"${fee_match.group(1)}" if fee_match else "N/A"
        except:
            data["delivery_fee"] = "N/A"
            data["eta"] = "N/A"

        # Scroll to load all products
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(2000)

        for product in products:
            try:
                # Find any text matching the product and extract the price from its container
                # We'll look for all divs that might be product cards
                cards = await page.locator("div[data-testid='product-item'], div[class*='Card'], div[class*='item']").all()
                found = False
                for card in cards:
                    text = await card.inner_text()
                    if product.lower() in text.lower():
                        # Extract the first price found in the card
                        price_match = re.search(r'\$\s*(\d+(?:,\d+)?(?:\.\d+)?)', text)
                        if price_match:
                            data[f"price_{product.lower().replace(' ', '_')}"] = price_match.group(0)
                            found = True
                            break
                
                if not found:
                    data[f"price_{product.lower().replace(' ', '_')}"] = "Not Found"
            except Exception as e:
                data[f"price_{product.lower().replace(' ', '_')}"] = f"Error: {e}"

        await browser.close()
        return data

def save_to_csv(data: dict, filename: str = "data/raw/rappi_scrape.csv"):
    df = pd.DataFrame([data])
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if not os.path.isfile(filename):
        df.to_csv(filename, index=False)
    else:
        existing_df = pd.read_csv(filename)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_csv(filename, index=False)
    
    print(f"Data saved to {filename}")
