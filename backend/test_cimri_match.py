import asyncio
import sys
import os

sys.path.append(os.getcwd())
from scraper import find_best_match

def test_m_series():
    query = "Bosch GAS 12-40 M Islak Kuru Süpürge"
    brand = "Bosch"
    
    candidates = [
        {"title": "Bosch GAS 12-40 L Profesyonel Islak Kuru Süpürge", "url": "fail_url_L"},
        {"title": "Bosch GAS 12-40 Elektrikli Süpürge", "url": "fail_url_none"},
        {"title": "Bosch GAS 12-40 M Islak Kuru Süpürge", "url": "success_url"}
    ]
    
    print(f"Testing Query: {query}")
    result = find_best_match(query, brand, candidates)
    print(f"Result for M series: {result}")
    assert result == "success_url"

def test_dcd():
    query = "Dewalt DCD796"
    brand = "Dewalt"
    
    candidates = [
        {"title": "Dewalt DCD795 Darbeli Matkap", "url": "fail_url"},
        {"title": "Dewalt DCD796 P2 Darbeli Matkap", "url": "success_url"},
        {"title": "Dewalt DCD 796 Şarjlı Matkap", "url": "success_url_spaced"}
    ]
    
    print(f"Testing Query: {query}")
    result = find_best_match(query, brand, candidates)
    print(f"Result for DCD: {result}")
    assert result in ["success_url", "success_url_spaced"]

if __name__ == "__main__":
    test_m_series()
    test_dcd()
    print("ALL TESTS PASSED")
