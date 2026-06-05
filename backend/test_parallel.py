import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())
from playwright.async_api import async_playwright
from scraper import agentic_search_cimri

async def test_parallel():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        print("Testing Kaan Cp-280 S3 7 Hp Benzinli Çapa Makinesi...")
        start_time = time.time()
        res1 = await agentic_search_cimri("Kaan Cp-280 S3 7 Hp Benzinli Çapa Makinesi", "Kaan", context)
        print(f"Result 1: {res1} (Took: {time.time() - start_time:.2f} seconds)")
        
        print("\nTesting Bosch GAS 12-40 MA...")
        start_time = time.time()
        res2 = await agentic_search_cimri("Bosch GAS 12-40 MA", "Bosch", context)
        print(f"Result 2: {res2} (Took: {time.time() - start_time:.2f} seconds)")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_parallel())
