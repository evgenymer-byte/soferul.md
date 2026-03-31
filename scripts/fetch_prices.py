import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timezone

def fetch_anre_prices():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # Try main ANRE page
    urls = [
        "https://anre.md",
        "https://www.anre.md",
        "https://ecarburanti.anre.md",
    ]
    
    prices = {"benzin95": None, "diesel": None, "gpl": None}
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            
            # Try to find patterns like "28,47" or "28.47" near "95" or "diesel"
            pattern = r'(\d{2}[.,]\d{2})'
            matches = re.findall(pattern, text)
            nums = [float(m.replace(",", ".")) for m in matches if 20 <= float(m.replace(",", ".")) <= 40]
            
            if len(nums) >= 2:
                nums_sorted = sorted(set(nums))
                if len(nums_sorted) >= 2:
                    prices["benzin95"] = nums_sorted[0]
                    prices["diesel"] = nums_sorted[1] if len(nums_sorted) > 1 else nums_sorted[0]
                    break
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue
    
    # Try fetching from tv8.md or nokta.md news as backup
    if not prices["benzin95"]:
        try:
            r = requests.get("https://tv8.md/search?q=ANRE+carburanti", headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            text = soup.get_text(" ", strip=True)
            nums = re.findall(r'(\d{2}[.,]\d{2})', text)
            fuel_nums = [float(m.replace(",", ".")) for m in nums if 20 <= float(m.replace(",", ".")) <= 40]
            if len(fuel_nums) >= 2:
                unique = sorted(set(fuel_nums))
                prices["benzin95"] = unique[0]
                prices["diesel"] = unique[1]
        except:
            pass
    
    # Fallback to last known prices if scraping fails
    if not prices["benzin95"]:
        prices = {"benzin95": 28.47, "diesel": 29.21, "gpl": 14.20}
        prices["fallback"] = True
    else:
        prices["fallback"] = False

    prices["updated"] = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    prices["valid_from"] = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    
    return prices

if __name__ == "__main__":
    prices = fetch_anre_prices()
    print(json.dumps(prices, indent=2, ensure_ascii=False))
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=2, ensure_ascii=False)
    print("prices.json updated!")
