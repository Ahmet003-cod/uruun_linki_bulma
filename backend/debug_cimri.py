import asyncio
import sys
import os
import re

sys.path.append(os.getcwd())
from playwright.async_api import async_playwright
from scraper import extract_candidates, normalize_match_text, fuzz
import urllib.parse

def extract_smart_nums(text):
    nums = re.findall(r"\d+-\d+|\d+", text)
    all_parts = set(nums)
    for n in nums:
        if '-' in n: all_parts.update(n.split('-'))
    return {n for n in all_parts if len(n) > 1 or (n.isdigit() and int(n) > 5)}

def extract_specs(text):
    def norm(val):
        if not val: return None
        try: return str(float(val.replace(",", "."))).replace(".0", "")
        except: return None
    res = {
        "v": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*v", text)},
        "ah": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*ah", text)},
        "w": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*w", text)},
        "l": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*l", text)},
        "kg": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*kg", text)},
        "bar": {norm(x) for x in re.findall(r"(\d+[\.,]\d+|\d+)\s*bar", text)},
    }
    qty_raw = re.findall(r"(\d+)\s*[xX*]|(\d+)\s*adet", text)
    res["qty"] = {norm(x) for tup in qty_raw for x in tup if x}
    for k in res: res[k].discard(None)
    return res

async def debug_search(query, brand):
    clean_query = query.lower().strip()
    norm_query = normalize_match_text(clean_query)
    
    MODEL_KEYWORDS = {"m", "l", "xl", "xxl", "g", "k", "c", "s", "pro", "max", "plus", "rca", "ma"}
    query_model_codes = []
    for w in norm_query.split():
        if w in MODEL_KEYWORDS:
            query_model_codes.append(w)
        elif any(c.isalpha() for c in w) and any(c.isdigit() for c in w):
            is_spec_word = False
            for unit in ['v', 'ah', 'w', 'l', 'kg', 'bar', 'mm', 'cm']:
                if w.endswith(unit) and w[:-len(unit)].replace('.', '').replace(',', '').isdigit():
                    is_spec_word = True
                    break
            if not is_spec_word:
                query_model_codes.append(w)
                
    IGNORED = {"seti", "makinesi", "fiyatlari", "+", "-", "ve", "ile", "adet", "icin"}
    q_words = [w for w in norm_query.split() if len(w) > 2 and w not in IGNORED]
    query_nums = extract_smart_nums(clean_query)
    q_specs = extract_specs(norm_query)
    clean_brand = brand.lower().strip() if brand else ""

    print(f"\n=======================")
    print(f"SEARCHING: {query}")
    print(f"norm_query: {norm_query}")
    print(f"query_model_codes: {query_model_codes}")
    print(f"q_words: {q_words}")
    print(f"query_nums: {query_nums}")
    print(f"q_specs: {q_specs}")
    
    # Generate stages
    search_queries = [query]
    model_match = re.search(r"([A-Z]{1,}\d+-\d+|[A-Z]{1,}-\d+|[A-Z]{1,}\d+|\d+-\d+|\d+)", query.upper())
    if model_match:
        search_queries.append(f"{brand} {model_match.group(1)}")
        
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for stage_query in list(dict.fromkeys(search_queries)):
            search_url = f"https://www.cimri.com/arama?q={urllib.parse.quote(stage_query)}"
            print(f"\n>>> Executing Stage: {stage_query} | URL: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            candidates = await extract_candidates(page)
            print(f"Found {len(candidates)} candidates.")
            for c in candidates:
                title = c['title']
                norm_title = normalize_match_text(title.lower().strip())
                
                print(f"  - Testing: {title}")
                
                match_count = sum(1 for qw in q_words if qw in norm_title)
                coverage = match_count / len(q_words) if q_words else 1.0
                if coverage < 0.75:
                    print(f"    FAIL: Coverage {coverage} < 0.75")
                    continue
                    
                if clean_brand and clean_brand not in norm_title:
                    print(f"    FAIL: Brand missing")
                    continue
                    
                model_code_fail = False
                t_words = norm_title.split()
                title_no_spaces = norm_title.replace(" ", "")
                for mc in query_model_codes:
                    found = False
                    for tw in t_words:
                        if tw == mc:
                            found = True
                            break
                        if mc.isalpha() and tw.endswith(mc) and tw[:-len(mc)].isdigit():
                            found = True
                            break
                    if not found and len(mc) > 3 and mc in title_no_spaces:
                        found = True
                    if not found:
                        print(f"    FAIL: Model code '{mc}' missing in title")
                        model_code_fail = True
                        break
                if model_code_fail: continue
                
                title_nums = extract_smart_nums(title.lower().strip())
                raw_title_no_spaces = title.lower().strip().replace(" ", "").replace("-", "")
                num_fail = False
                for qn in query_nums:
                    if qn not in title_nums and qn not in raw_title_no_spaces:
                        if len(qn) > 2:
                            print(f"    FAIL: Number '{qn}' missing")
                            num_fail = True
                            break
                if num_fail: continue
                
                t_specs = extract_specs(norm_title)
                spec_fail = False
                for unit, q_vals in q_specs.items():
                    if q_vals and not q_vals.issubset(t_specs[unit]):
                        print(f"    FAIL: Spec {unit}={q_vals} missing")
                        spec_fail = True
                        break
                if spec_fail: continue
                
                score = fuzz.token_set_ratio(norm_query, norm_title)
                print(f"    SUCCESS: Score = {score}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_search("Bosch GAS 12-40 M", "Bosch"))
    asyncio.run(debug_search("Bosch Gas 12-40 Ma Professional", "Bosch"))
