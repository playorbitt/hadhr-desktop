"""Download everything the reader fetches from the internet into mirror/, so the desktop app is fully
offline: QUSX text for all 10 mushaf editions, the per-page mushaf fonts (v1, v2, v4 tajweed), the
Uthmanic Hafs font, the Google Arabic fonts and the English translation (Pickthall) for all 114 surahs.
Re-running only fetches what is missing.  Usage: python mirror_assets.py"""
import json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mirror")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
LAYOUTS = ["madani-v2", "madani-v1", "madani-v4-tajweed", "qatar", "indopak-15", "indopak-9-gaba",
           "indopak-13-qudratullah", "indopak-13-taj", "indopak-16-taj", "nastaleeq"]
QF = "https://verses.quran.foundation/fonts/quran/hafs/"
GFONTS = ("https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Harmattan:wght@400;500;600;700"
          "&family=Lateef:wght@400;500;600;700&family=Mirza:wght@400;500;600;700&family=Noto+Naskh+Arabic:wght@400;500;600"
          "&family=Noto+Nastaliq+Urdu:wght@400;500;600&family=Scheherazade+New:wght@400;700&display=swap")

def get(url, dest, ok404=False):
    if os.path.exists(dest) and os.path.getsize(dest) > 0: return "cached"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            open(dest + ".part", "wb").write(data); os.replace(dest + ".part", dest)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404 and ok404: return "404"
            if attempt == 3: return f"error {e.code}"
        except Exception as e:
            if attempt == 3: return f"error {e}"

jobs = []
for layout in LAYOUTS:
    for n in range(1, 115):
        jobs.append((f"https://raw.githubusercontent.com/dfordev1/usxv2/main/output/{layout}/{n:03d}.qusx.xml",
                     os.path.join(OUT, "usxv2", layout, f"{n:03d}.qusx.xml"), False))
for kind in ("v1/woff2", "v2/woff2", "v4/colrv1/woff2"):
    for p in range(1, 605):
        jobs.append((f"{QF}{kind}/p{p}.woff2", os.path.join(OUT, "qf-fonts", *kind.split("/"), f"p{p}.woff2"), True))
jobs.append((QF + "uthmanic_hafs/UthmanicHafs1Ver18.woff2", os.path.join(OUT, "qf-fonts", "uthmanic_hafs", "UthmanicHafs1Ver18.woff2"), False))
for n in range(1, 115):
    jobs.append((f"https://api.alquran.cloud/v1/surah/{n}/en.pickthall", os.path.join(OUT, "alquran", str(n), "en.pickthall"), False))

with ThreadPoolExecutor(16) as pool:
    results = list(pool.map(lambda j: (j[0], get(*j)), jobs))
bad = [(u, r) for u, r in results if r.startswith("error")]
print("files:", len(results), "| fetched:", sum(r == "ok" for _, r in results), "| cached:", sum(r == "cached" for _, r in results),
      "| absent upstream (404):", sum(r == "404" for _, r in results), "| errors:", len(bad))
for u, r in bad[:10]: print("  ", r, u)

# Google fonts: the CSS lists woff2 files on fonts.gstatic.com; mirror them and point the CSS at the copies.
css_path = os.path.join(OUT, "gfonts", "fonts.css")
os.makedirs(os.path.dirname(css_path), exist_ok=True)
css = urllib.request.urlopen(urllib.request.Request(GFONTS, headers=UA), timeout=60).read().decode()
urls = sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)))
def gfont(u):
    rel = u.replace("https://fonts.gstatic.com/", "")
    return u, get(u, os.path.join(OUT, "gfonts", *rel.split("/")))
with ThreadPoolExecutor(16) as pool:
    gres = list(pool.map(gfont, urls))
css = css.replace("https://fonts.gstatic.com/", "/mirror/gfonts/")
open(css_path, "w", encoding="utf-8").write(css)
print("google font files:", len(urls), "| errors:", sum(r.startswith("error") for _, r in gres))
total = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
print(f"mirror/ total: {total / 1e6:.0f} MB")
sys.exit(1 if bad else 0)
