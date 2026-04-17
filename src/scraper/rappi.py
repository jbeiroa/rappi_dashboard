import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os

async def scrape_rappi_restaurant(url: str, headless: bool = True):
    """
    Scrapes a Rappi restaurant page for basic metrics.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to: {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Wait for potential dynamic content
        await page.wait_for_timeout(5000)
        
        # Basic extraction (Selectors may need adjustment based on Rappi's current UI)
        # Note: These are example selectors and might need updates.
        data = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "restaurant_name": await page.inner_text("h1") if await page.query_selector("h1") else "Unknown",
        }
        
        # Attempt to find delivery fee, service fee, and ETA
        # Rappi often stores these in specific spans or divs
        try:
            # This is a speculative extraction logic for the minimal version
            # In a real scenario, we'd inspect the exact DOM.
            data["delivery_fee"] = await page.inner_text("span:has-text('$')") # Placeholder
            data["eta"] = await page.inner_text("span:has-text('min')") # Placeholder
        except Exception as e:
            print(f"Warning: Could not extract all metrics: {e}")
            data["delivery_fee"] = "N/A"
            data["eta"] = "N/A"

        await browser.close()
        return data

def save_to_csv(data: dict, filename: str = "data/raw/rappi_scrape.csv"):
    df = pd.DataFrame([data])
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if not os.path.isfile(filename):
        df.to_csv(filename, index=False)
    else:
        df.to_csv(filename, mode='a', header=False, index=False)
    
    print(f"Data saved to {filename}")
