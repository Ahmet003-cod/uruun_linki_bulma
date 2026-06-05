import asyncio
import sys
import os
import re

# Add backend to path
sys.path.append(os.getcwd())

from scraper import find_best_match, normalize_match_text

def test_complex_match():
    query = "Bosch Procore Akü Seti 4x4.0Ah + 2x8.0Ah"
    brand = "Bosch"
    
    # Simulate Cimri results
    candidates = [
        {"title": "Bosch ProCore 18V 4.0 Ah + 8.0 Ah Akü Seti", "url": "match_url_1"},
        {"title": "Bosch ProCore 18V 4x4.0Ah + 2x8.0Ah Profesyonel Set", "url": "match_url_2"},
        {"title": "Bosch ProCore 18V 5.0 Ah Akü", "url": "fail_url_1"},
        {"title": "Bosch ProCore 18V 4.0 Ah Akü", "url": "fail_url_2"}
    ]
    
    print(f"--- TESTING COMPLEX MATCHING ---")
    print(f"Query: {query}")
    
    result = find_best_match(query, brand, candidates)
    
    print(f"\nResult: {result}")
    if result == "match_url_2" or result == "match_url_1":
        print("SUCCESS: System correctly identified the complex battery set!")
    else:
        print("FAILED: System could not identify the set correctly.")

if __name__ == "__main__":
    test_complex_match()
