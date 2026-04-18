import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import pandas as pd
import os
import re

async def resolve_one_address(context, original_address):
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    
    try:
        # Search on Google Maps
        search_query = urllib.parse.quote(original_address)
        await page.goto(f"https://www.google.com/maps/search/{search_query}", wait_until="domcontentloaded", timeout=60000)
        
        # Wait for either the results list or a specific pin
        await page.wait_for_timeout(5000)
        
        # Current URL usually contains coordinates after @
        # Example: https://www.google.com/maps/place/Polanco.../@19.4304375,-99.1881168,15z/...
        url = page.url
        lat, lng = None, None
        coord_match = re.search(r'@([-?\d.]+),([-?\d.]+)', url)
        if coord_match:
            lat = float(coord_match.group(1))
            lng = float(coord_match.group(2))
        
        # Get the resolved address and CP
        resolved_address = original_address
        cp = None
        try:
            h1 = page.locator("h1").first
            if await h1.is_visible():
                resolved_address = await h1.inner_text()
            
            # Try to find CP in the full address string (usually in a specific div)
            address_text = await page.locator("div[aria-label*='Dirección']").inner_text()
            cp_match = re.search(r'\b\d{5}\b', address_text)
            if cp_match:
                cp = cp_match.group(0)
        except:
            # Fallback: search for CP in the whole page content
            content = await page.content()
            cp_match = re.search(r'\b\d{5}\b', content)
            if cp_match:
                cp = cp_match.group(0)
            
        return resolved_address, lat, lng, cp
    finally:
        await page.close()

import urllib.parse

async def resolve_addresses(input_file="data/raw/addresses.csv", output_file="data/raw/resolved_addresses.csv"):
    df = pd.read_csv(input_file)
    addresses = df['address'].tolist()
    
    resolved_data = []
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        resolved_data = existing_df.to_dict('records')
        resolved_original = set(existing_df['original_address'].tolist())
        print(f"Resuming: {len(resolved_original)} addresses already checked.")
    else:
        resolved_original = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        for idx, addr in enumerate(addresses):
            # Check if CP is missing even if address is resolved
            existing_record = next((r for r in resolved_data if r['original_address'] == addr), None)
            if existing_record and existing_record.get('cp'):
                continue
                
            print(f"Resolving [{idx+1}/{len(addresses)}]: {addr}")
            res_addr, lat, lng, cp = addr, None, None, None
            try:
                res_addr, lat, lng, cp = await resolve_one_address(context, addr)
                print(f"  -> {res_addr} ({lat}, {lng}) CP: {cp}")
            except Exception as e:
                print(f"  Failed: {e}")
            
            if existing_record:
                existing_record['resolved_address'] = res_addr
                existing_record['lat'] = lat
                existing_record['lng'] = lng
                existing_record['cp'] = cp
            else:
                resolved_data.append({
                    "original_address": addr,
                    "resolved_address": res_addr,
                    "lat": lat,
                    "lng": lng,
                    "cp": cp
                })
            pd.DataFrame(resolved_data).to_csv(output_file, index=False)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(resolve_addresses())
