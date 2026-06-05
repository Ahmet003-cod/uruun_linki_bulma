import asyncio
import sys
import os

sys.path.append(os.getcwd())
from playwright.async_api import async_playwright
from scraper import agentic_search_cimri

async def test_fallback():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Testing Kaan Cp-280...")
        res1 = await agentic_search_cimri("Kaan Cp-280 S3 7 Hp Benzinli Çapa Makinesi", "Kaan", page)
        print(f"Result 1: {res1}")
        
        print("\nTesting Bosch GAS 12-40 MA...")
        res2 = await agentic_search_cimri("Bosch GAS 12-40 MA", "Bosch", page)
        print(f"Result 2: {res2}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_fallback())
