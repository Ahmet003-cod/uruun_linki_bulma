import asyncio
from playwright.async_api import async_playwright
import urllib.parse
from thefuzz import fuzz
import re
import random
import unicodedata
import sys
import io

# Ensure UTF-8 on Windows for prints
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def safe_log(message):
    try:
        print(message)
    except:
        pass

def cleanup_text(text):
    if not isinstance(text, str): return text
    text = unicodedata.normalize('NFC', text)
    text = text.replace('\u0307', '')
    text = text.replace('İ', 'i').replace('I', 'ı').lower()
    return text.strip()

NEGATIVES = [
    "torba", "filtre", "hortum", "aksesuar", "yedek parça", "batarya", 
    "şarj cihazı", "kablo", "uç set", "mandren", "adaptör", "kağıt", 
    "bezi", "başlığı", "fırçası", "aparatı", "akü", "akülü", "seti", "set",
    "piston", "karter", "silindir", "bilya", "buji", "kapak", "zincir",
    "şanzıman", "dişli", "segman", "yağ", "yakıt", "karbüratör", "motoru değil"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edge/120.0.0.0"
]

def clean_name(name):
    suffixes = [
        r"taşıma çantalı", r"çantalı", r"solo", r"akülü", r"vidalama", 
        r"kırıcı-delici", r"zımba çakma", r"çivi ve", r"şarjlı", r"li-ion",
        r"li-i", r"li", r"-\d+v", r"\d+v", r"18v", r"12v", r"36v", r"54v"
    ]
    cleaned = name.lower()
    for s in suffixes: cleaned = re.sub(s, "", cleaned)
    return cleaned.strip()

def normalize_match_text(text):
    if not text: return ""
    text = text.lower()
    # Preserve dots and commas for decimal numbers (4.0, 5,5 etc)
    text = re.sub(r'[^a-z0-9\s\.,]', ' ', text)
    # Turkish char normalization
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text

def find_best_match(query, brand, candidates, threshold=80):
    """
    INTELLIGENT ACCURACY MODE:
    - Every word in query MUST be in title (except ignored).
    - Every significant number in query MUST be in title.
    - Technical specs (V, Ah, Watt) MUST match exactly.
    - Brand MUST be present.
    """
    if not candidates: return None
    
    clean_query = query.lower().strip()
    norm_query = normalize_match_text(clean_query)
    
    # --- MODEL CODE EXTRACTION ---
    MODEL_KEYWORDS = {"m", "l", "xl", "xxl", "g", "k", "c", "s", "pro", "max", "plus", "rca"}
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
    
    # 1. Words to match
    IGNORED = {"seti", "makinesi", "fiyatlari", "+", "-", "ve", "ile", "adet", "icin"}
    q_words = [w for w in norm_query.split() if len(w) > 2 and w not in IGNORED]
    
    # 2. Numbers to match
    def extract_smart_nums(text):
        nums = re.findall(r"\d+-\d+|\d+", text)
        all_parts = set(nums)
        for n in nums:
            if '-' in n: all_parts.update(n.split('-'))
        return {n for n in all_parts if len(n) > 1 or (n.isdigit() and int(n) > 5)}

    query_nums = extract_smart_nums(clean_query)
    
    # 3. Specs to match
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

    q_specs = extract_specs(norm_query)
    clean_brand = brand.lower().strip() if brand else ""
    
    best_candidate = None
    highest_score = -1

    for cand in candidates:
        title = cand['title'].lower().strip()
        norm_title = normalize_match_text(title)
        
        # --- SMART WORD COVERAGE CHECK ---
        match_count = sum(1 for qw in q_words if qw in norm_title)
        coverage = match_count / len(q_words) if q_words else 1.0
        if coverage < 0.75: continue
        
        # --- ABSOLUTE BRAND CHECK ---
        if clean_brand and clean_brand not in norm_title:
            continue

        # --- STRICT MODEL CODE CHECK ---
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
                model_code_fail = True
                break
        if model_code_fail: continue

        # --- SMART NUMERIC CHECK ---
        title_nums = extract_smart_nums(title)
        num_fail = False
        raw_title_no_spaces = title.replace(" ", "").replace("-", "")
        for qn in query_nums:
            if qn not in title_nums and qn not in raw_title_no_spaces:
                if len(qn) > 2: num_fail = True; break
                continue
        if num_fail: continue

        # --- ABSOLUTE SPEC CHECK ---
        t_specs = extract_specs(norm_title)
        spec_fail = False
        spec_match_bonus = 0
        for unit, q_vals in q_specs.items():
            if q_vals:
                if not q_vals.issubset(t_specs[unit]):
                    spec_fail = True; break
                spec_match_bonus += 25 
        if spec_fail: continue

        # --- FINAL SCORE ---
        score = fuzz.token_set_ratio(norm_query, norm_title)
        score += spec_match_bonus
            
        if score > highest_score:
            highest_score = score
            best_candidate = cand['url']
            
    if highest_score >= threshold: return best_candidate
    return None

async def extract_candidates(page):
    """Universal extractor for search results."""
    return await page.evaluate("""() => {
        const results = [];
        const elements = document.querySelectorAll("h2, h3, .product-name, [class*='title'], [class*='ProductTitle']");
        elements.forEach(el => {
            const title = el.innerText.trim();
            if (title.length < 5) return;
            let a = el.closest('a') || el.querySelector('a');
            if (!a) {
                const card = el.closest('div, li, article, [class*="ProductCard"]');
                if (card) {
                    a = card.querySelector('a[href*="/en-ucuz-"], a[href*="/product/"], a[href*="/market/"]') || card.querySelector('a[href]');
                }
            }
            if (a && a.getAttribute('href')) {
                results.push({title, url: a.getAttribute('href')});
            }
        });
        return results;
    }""")

async def agentic_search_akakce(name, brand, page_or_context, lenient=False):
    name = cleanup_text(name)
    if hasattr(page_or_context, 'new_page'): page = await page_or_context.new_page()
    else: page = page_or_context
    search_url = f"https://www.akakce.com/arama/?q={urllib.parse.quote(name)}"
    try:
        await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
        candidates = await extract_candidates(page)
        for c in candidates:
            if not c['url'].startswith("http"): c['url'] = f"https://www.akakce.com{c['url']}"
        res = find_best_match(name, brand, candidates)
        if hasattr(page_or_context, 'new_page'): await page.close()
        return res
    except:
        if hasattr(page_or_context, 'new_page'): await page.close()
        return None

async def agentic_search_cimri(name, brand, page_or_context, lenient=False):
    name = cleanup_text(name)
    brand = cleanup_text(brand) if brand else ""
    
    if hasattr(page_or_context, 'new_page'):
        context = page_or_context
    else:
        context = page_or_context.context
    
    model_num = "".join(re.findall(r"\d+", name))
    search_queries = [name]
    
    model_match = re.search(r"([A-Z]{1,}\d+-\d+|[A-Z]{1,}-\d+|[A-Z]{1,}\d+|\d+-\d+|\d+)", name.upper())
    if model_match:
        model_part = model_match.group(1)
        search_queries.append(f"{brand} {model_part}")
        
    only_nums = "".join(re.findall(r"\d+", name))
    if only_nums and len(only_nums) >= 2:
        search_queries.append(f"{brand} {only_nums}")
        
    clean_core = re.sub(r"\d+\s*hp|\d+\s*v|\d+\s*ah|benzinli|dizel|capa makinesi|elektrikli|islak|kuru", "", name, flags=re.I).strip()
    if clean_core and clean_core != name:
        search_queries.append(f"{brand} {clean_core}")

    search_queries = list(dict.fromkeys(search_queries))

    async def fetch_stage(stage_query):
        try:
            stage_page = await context.new_page()
        except Exception as e:
            print(f"Error creating new page in fetch_stage: {e}")
            return []
            
        search_url = f"https://www.cimri.com/arama?q={urllib.parse.quote(stage_query)}"
        try:
            await stage_page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)
            candidates = await extract_candidates(stage_page)
            for c in candidates:
                if not c['url'].startswith("http"):
                    c['url'] = f"https://www.cimri.com{c['url']}"
            await stage_page.close()
            return candidates
        except Exception as e:
            print(f"Error in fetch_stage: {e}")
            await stage_page.close()
            return []

    fetch_tasks = [fetch_stage(sq) for sq in search_queries]
    results = await asyncio.gather(*fetch_tasks)
    
    all_candidates = []
    for cands in results:
        all_candidates.extend(cands)
        
    res = find_best_match(name, brand, all_candidates)
    return res

async def search_product(source: str, query: str, brand: str = "", page_or_context=None, lenient=False):
    if source.lower() == "akakce":
        return await agentic_search_akakce(query, brand, page_or_context, lenient)
    elif source.lower() == "cimri":
        return await agentic_search_cimri(query, brand, page_or_context, lenient)
    return None
