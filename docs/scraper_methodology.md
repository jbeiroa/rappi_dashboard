# Rappi Scraper Development Methodology

This document outlines the technical approach, challenges, and solutions encountered during the development of the Rappi Competitive Intelligence scraper.

## 🎯 Objective
Extract precise pricing (original, final, discount), delivery fees, and ETAs for three benchmark products across 50 strategic locations in Mexico for McDonald's.

## ✅ What Worked
- **Playwright + Stealth:** Using `playwright-stealth` was essential to bypass initial bot detection and ensure the page loaded the same way as a real user session.
- **Search URL Bypass:** Instead of interacting with the flaky search input UI, navigating directly to `https://www.rappi.com.mx/busqueda?query=...` proved much more reliable.
- **Hub Escape Logic:** A critical addition. Rappi often lands search results on "Brand Hubs" (directories of stores) rather than a specific store menu. The logic now detects this and automatically selects the first link with a numeric ID to reach the actual menu.
- **Fuzzy Product Matching:** Integrating `rapidfuzz` allowed the scraper to map target product strings (e.g., "Big Mac + Coca") to actual menu titles even when they varied slightly by region or include extras (e.g., "Big Mac Tocino").
- **Structured JSON Schema:** Moving from a wide CSV to a "long-format" JSON array where each product is an individual record. This includes location metadata (Zone, Municipality, State) and HTML snippets for auditing.
- **Price Tiering Logic:** Successfully identifying original vs. final prices by parsing all dollar amounts in a card and assuming the higher value is the original price when a discount is present.

## ❌ What Didn't Work
- **Direct UI Interactions:** Clicking search icons and typing into inputs often failed due to dynamic overlays or elements not being "visible" according to Playwright, even when present in the DOM.
- **Static Store Selectors:** Simple selectors like `text="McDonald's"` often clicked the brand logo or directory links instead of the actual orderable store menu.
- **General Body Parsing:** Initially trying to find prices anywhere on the page led to false positives. The card-based approach (`data-qa="product-item-..."`) proved necessary.

## 🔑 Key User Inputs
The development was accelerated by specific insights provided during the session:
1.  **Benchmark Products:** Precise naming for the three target products enabled the setup of the fuzzy matching layer.
2.  **Verified Address:** Providing the exact string `"Calle Polanco, Polanco V Sección 11560 Miguel Hidalgo"` allowed for a "gold standard" test case.
3.  **Precise XPath:** The full XPath for header metrics (`/html/body/div[1]/div[3]/div[2]/div[2]/div[2]/div[2]/div[1]`) solved the difficulty of extracting delivery fees from Rappi's highly dynamic and nested header structure.

## 🚀 Strategy for Future Scrapers (Uber Eats / DiDi Food)
- **Address First:** Always lock in the geolocation context before searching.
- **JSON Blob Inspection:** Use `__NEXT_DATA__` or similar script tags as a fallback for price extraction if the DOM becomes too obscured.
- **Metadata Splitting:** Continue splitting address strings into Municipality/Zone fields at the source to simplify the Gold Layer analysis.
- **App Tagging:** Maintain the `app_name` field for easy cross-service comparison in the Dash dashboard.
