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

def normalize_match_text_akakce(text):
    if not text: return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\.,]', ' ', text)
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text

def normalize_match_text_cimri(text):
    if not text: return ""
    text = text.lower()
    replacements = {'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'}
    for k, v in replacements.items(): text = text.replace(k, v)
    text = re.sub(r'[^a-z0-9\s\.,]', ' ', text)
    return text

def find_best_match(query, brand, candidates, threshold=80, lenient=False, is_cimri=False):
    if not candidates: return None
    
    clean_query = query.lower().strip()
    norm_query = normalize_match_text_cimri(clean_query) if is_cimri else normalize_match_text_akakce(clean_query)
    
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
        norm_title = normalize_match_text_cimri(title) if is_cimri else normalize_match_text_akakce(title)
        
        # --- STRICT MODEL CODE CHECK ---
        model_code_fail = False
        t_words = norm_title.split()
        title_no_spaces = norm_title.replace(" ", "")
        title_clean = title_no_spaces.replace('.', '').replace(',', '')
        for mc in query_model_codes:
            found = False
            for tw in t_words:
                if tw == mc:
                    found = True
                    break
                if mc.isalpha() and tw.endswith(mc) and tw[:-len(mc)].isdigit():
                    found = True
                    break
            
            mc_clean = mc.replace('.', '').replace(',', '')
            if not found and len(mc_clean) > 3 and mc_clean in title_clean:
                found = True
                
            if not found:
                model_code_fail = True
                break
        if model_code_fail and not lenient: continue

        # --- SMART WORD COVERAGE CHECK ---
        match_count = sum(1 for qw in q_words if qw in norm_title)
        coverage = match_count / len(q_words) if q_words else 1.0
        min_coverage = 0.50 if lenient else 0.75
        if is_cimri and not lenient:
            min_coverage = 0.50
        if coverage < min_coverage: continue
        
        # --- ABSOLUTE BRAND CHECK ---
        if clean_brand and clean_brand not in norm_title:
            if not lenient:
                continue

        # --- SMART NUMERIC CHECK ---
        title_nums = extract_smart_nums(title)
        num_fail = False
        raw_title_no_spaces = title.replace(" ", "").replace("-", "")
        for qn in query_nums:
            if qn not in title_nums and qn not in raw_title_no_spaces:
                if len(qn) > 2: num_fail = True; break
                continue
        if num_fail and not lenient and not is_cimri: continue

        # --- ABSOLUTE SPEC CHECK ---
        t_specs = extract_specs(norm_title)
        spec_fail = False
        spec_match_bonus = 0
        for unit, q_vals in q_specs.items():
            if q_vals:
                if not q_vals.issubset(t_specs[unit]):
                    spec_fail = True; break
                spec_match_bonus += 25 
        if spec_fail and not lenient and not is_cimri: continue

        # --- FINAL SCORE ---
        score = fuzz.token_set_ratio(norm_query, norm_title)
        score += spec_match_bonus
            
        if score > highest_score:
            highest_score = score
            best_candidate = cand['url']
            
    adjusted_threshold = threshold - 15 if lenient else threshold
    if highest_score >= adjusted_threshold: return best_candidate
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
    brand = cleanup_text(brand) if brand else ""
    
    if hasattr(page_or_context, 'new_page'):
        page = await page_or_context.new_page()
    else:
        page = page_or_context

    search_stages = [name]
    
    # 1. Broad fallbacks (first 3 and 4 words)
    words = name.split()
    if len(words) >= 3:
        search_stages.append(" ".join(words[:3]))
    if len(words) >= 4:
        search_stages.append(" ".join(words[:4]))
        
    # 2. Extract complex model codes (words with both letters and numbers)
    for w in words:
        if any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
            if len(w) > 3:
                search_stages.append(f"{brand} {w}")
    
    # 3. Simple model match (fallback)
    model_match = re.search(r"([A-Z]{1,}\d+-\d+|[A-Z]{1,}-\d+|[A-Z]{1,}\d+|\d+-\d+|\d+)", name.upper())
    if model_match: search_stages.append(f"{brand} {model_match.group(1)}")
    
    # 4. Only numbers
    only_nums = "".join(re.findall(r"\d+", name))
    if only_nums and len(only_nums) >= 2 and len(only_nums) < 10: 
        search_stages.append(f"{brand} {only_nums}")
        
    # 5. Core name without generic specs
    clean_core = re.sub(r"\d+\s*hp|\d+\s*v|\d+\s*ah|benzinli|dizel|capa makinesi|elektrikli|islak|kuru", "", name, flags=re.I).strip()
    if clean_core and clean_core != name: search_stages.append(f"{brand} {clean_core}")

    search_stages = list(dict.fromkeys(search_stages))

    best_res = None
    for stage_query in search_stages:
        search_url = f"https://www.akakce.com/arama/?q={urllib.parse.quote(stage_query)}"
        try:
            await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)
            raw_candidates = await extract_candidates(page)
            candidates = []
            for c in raw_candidates:
                if "/c/?" in c['url'] or "/c?" in c['url']: continue
                if not c['url'].startswith("http"): c['url'] = f"https://www.akakce.com{c['url']}"
                candidates.append(c)
            
            res = find_best_match(name, brand, candidates, lenient=lenient)
            if res:
                best_res = res
                break
        except Exception as e:
            continue

    if hasattr(page_or_context, 'new_page'): await page.close()
    return best_res

async def agentic_search_cimri(name, brand, page_or_context, lenient=False):
    name = cleanup_text(name)
    brand = cleanup_text(brand) if brand else ""
    
    if hasattr(page_or_context, 'new_page'):
        page = await page_or_context.new_page()
    else:
        page = page_or_context

    search_stages = [name]
    
    # 1. Broad fallbacks (first 3 and 4 words)
    words = name.split()
    if len(words) >= 3:
        search_stages.append(" ".join(words[:3]))
    if len(words) >= 4:
        search_stages.append(" ".join(words[:4]))
        
    # 2. Extract complex model codes (words with both letters and numbers)
    for w in words:
        if any(c.isdigit() for c in w) and any(c.isalpha() for c in w):
            if len(w) > 3:
                search_stages.append(f"{brand} {w}")
    
    # 3. Simple model match (fallback)
    model_match = re.search(r"([A-Z]{1,}\d+-\d+|[A-Z]{1,}-\d+|[A-Z]{1,}\d+|\d+-\d+|\d+)", name.upper())
    if model_match: search_stages.append(f"{brand} {model_match.group(1)}")
        
    # 4. Only numbers
    only_nums = "".join(re.findall(r"\d+", name))
    if only_nums and len(only_nums) >= 2 and len(only_nums) < 10: 
        search_stages.append(f"{brand} {only_nums}")
        
    # 5. Core name without generic specs
    clean_core = re.sub(r"\d+\s*hp|\d+\s*v|\d+\s*ah|benzinli|dizel|capa makinesi|elektrikli|islak|kuru", "", name, flags=re.I).strip()
    if clean_core and clean_core != name: search_stages.append(f"{brand} {clean_core}")

    search_stages = list(dict.fromkeys(search_stages))

    best_res = None
    for stage_query in search_stages:
        search_url = f"https://www.cimri.com/arama?q={urllib.parse.quote(stage_query)}"
        try:
            await page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)
            candidates = await extract_candidates(page)
            for c in candidates:
                if not c['url'].startswith("http"): c['url'] = f"https://www.cimri.com{c['url']}"
            
            res = find_best_match(name, brand, candidates, lenient=lenient, is_cimri=True)
            if res:
                best_res = res
                break
        except Exception as e:
            continue

    if hasattr(page_or_context, 'new_page'): await page.close()
    return best_res

async def search_product(source: str, query: str, brand: str = "", page_or_context=None, lenient=False):
    if source.lower() == "akakce":
        return await agentic_search_akakce(query, brand, page_or_context, lenient)
    elif source.lower() == "cimri":
        return await agentic_search_cimri(query, brand, page_or_context, lenient)
    return None
