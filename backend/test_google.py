import asyncio
import sys
import os
import urllib.parse

sys.path.append(os.getcwd())
from playwright.async_api import async_playwright
from scraper import extract_google_candidates, find_best_match

async def test_google():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        name = "Bosch GAS 12-40 MA"
        brand = "Bosch"
        fallback_query = f"site:cimri.com {name} {brand}".strip()
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(fallback_query)}&hl=tr"
        
        print(f"URL: {google_url}")
        await page.goto(google_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        candidates = await extract_google_candidates(page)
        print(f"Candidates: {candidates}")
        
        res = find_best_match(name, brand, candidates)
        print(f"Match: {res}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_google())
