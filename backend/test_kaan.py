import asyncio
import sys
import os

sys.path.append(os.getcwd())
from scraper import find_best_match

def test_kaan():
    query = "Kaan Cp-280 S3 7 Hp Benzinli Çapa Makinesi"
    brand = "Kaan"
    
    candidates = [
        {"title": "Kaan 280 S 7 Hp Benzinli Çapa Makinesi", "url": "fail_url_s"},
        {"title": "Kaan 280 S", "url": "fail_url_s_short"},
        {"title": "Kaan 280 S3 7 Hp Benzinli Çapa Makinesi", "url": "success_url_s3"}
    ]
    
    print(f"Testing Query: {query}")
    result = find_best_match(query, brand, candidates)
    print(f"Result for Kaan: {result}")

if __name__ == "__main__":
    test_kaan()
