#!/usr/bin/env python3
"""Скачивает картины и фото из Wikimedia Commons ТОЛЬКО со свободной лицензией
(общественное достояние / CC0; с флагом --allow-cc ещё CC BY и CC BY-SA) и кладёт их в assets/.

Запуск (на компьютере, не на телефоне):
    pip install pillow
    python fetch_art.py                 # все категории из QUERIES
    python fetch_art.py --per-cat 20    # до 20 картин на категорию
    python fetch_art.py --allow-cc      # добавить CC BY / CC BY-SA (автор попадёт в credits.json)

Результат:
    assets/pics/<Категория>/<имя>.jpg   (квадрат 1024x1024, ~150 КБ)
    assets/credits.json                 (название, автор, лицензия — игра показывает автора под картиной)

Редактируй QUERIES под себя. Результаты поиска просмотри глазами и удали лишнее.
"""
import argparse
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
UA = "PicSudokuArtFetcher/1.0 (personal hobby app; replace-with-your-email@example.com)"

QUERIES = {
    "Живопись": ["Aivazovsky painting sea", "Claude Monet landscape", "Van Gogh painting",
                 "Shishkin painting forest", "Levitan painting", "Hokusai woodblock print",
                 "Caspar David Friedrich painting", "Albert Bierstadt painting", "Turner painting",
                 "Roerich painting mountains", "Kuindzhi painting", "Vasnetsov painting fairy tale"],
    "Фантастика": ["Gustave Dore illustration", "Arthur Rackham fairy illustration",
                   "Vasnetsov bogatyrs", "Warwick Goble illustration", "Edmund Dulac illustration",
                   "Viktor Vasnetsov Alyonushka"],
    "Космос": ["NASA Hubble nebula", "NASA James Webb image", "NASA Earthrise Apollo 8",
               "NASA Pillars of Creation", "NASA galaxy Hubble"],
    "Знаменитые портреты": ["Mona Lisa Leonardo", "Girl with a Pearl Earring Vermeer",
                            "Portrait of Pushkin Kiprensky", "Portrait of Peter the Great painting",
                            "Napoleon crossing the Alps David", "Birth of Venus Botticelli"],
    "Кино и мультики (до 1931)": ["Nosferatu 1922 film still", "Metropolis 1927 film still",
                                  "Charlie Chaplin The Kid 1921", "Steamboat Willie 1928",
                                  "A Trip to the Moon 1902 Melies"],
}

OK_FREE = re.compile(r"public domain|^pd\b|cc0|cc[- ]zero", re.I)
OK_CC = re.compile(r"cc[- ]by", re.I)


def api(**params):
    params.update(format="json", action="query")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def slug(s):
    return re.sub(r"[^\w\-]+", "_", s, flags=re.U).strip("_")[:60] or "image"


def search(q, limit=40):
    data = api(generator="search", gsrnamespace=6, gsrsearch=q + " filetype:bitmap", gsrlimit=limit,
               prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=1400)
    return list(data.get("query", {}).get("pages", {}).values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets")
    ap.add_argument("--per-cat", type=int, default=12)
    ap.add_argument("--per-query", type=int, default=3)
    ap.add_argument("--allow-cc", action="store_true")
    ap.add_argument("--min-side", type=int, default=800)
    a = ap.parse_args()

    cpath = os.path.join(a.out, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}

    for cat, queries in QUERIES.items():
        cdir = os.path.join(a.out, "pics", cat)
        os.makedirs(cdir, exist_ok=True)
        got = len([f for f in os.listdir(cdir) if f.lower().endswith(".jpg")])
        for q in queries:
            if got >= a.per_cat:
                break
            took = 0
            try:
                pages = search(q)
            except Exception as e:
                print("  поиск не удался:", q, e)
                continue
            for pg in sorted(pages, key=lambda p: p.get("index", 0)):
                if took >= a.per_query or got >= a.per_cat:
                    break
                ii = (pg.get("imageinfo") or [{}])[0]
                meta = ii.get("extmetadata", {})
                lic = strip(meta.get("LicenseShortName", {}).get("value", ""))
                free = OK_FREE.search(lic) or (a.allow_cc and OK_CC.search(lic))
                if not free or ii.get("mime") not in ("image/jpeg", "image/png"):
                    continue
                if min(ii.get("width", 0), ii.get("height", 0)) < a.min_side:
                    continue
                title = re.sub(r"\.\w+$", "", pg["title"].replace("File:", ""))
                rel = "%s/%s.jpg" % (cat, slug(title))
                dst = os.path.join(a.out, "pics", rel)
                if os.path.exists(dst):
                    continue
                try:
                    req = urllib.request.Request(ii.get("thumburl") or ii["url"], headers={"User-Agent": UA})
                    with urllib.request.urlopen(req, timeout=60) as r:
                        img = Image.open(io.BytesIO(r.read())).convert("RGB")
                    w, h = img.size
                    s = min(w, h)
                    x0, y0 = (w - s) // 2, (h - s) // 2
                    img = img.crop((x0, y0, x0 + s, y0 + s)).resize((1024, 1024), Image.LANCZOS)
                    img.save(dst, "JPEG", quality=86, optimize=True)
                except Exception as e:
                    print("  не скачалось:", title, e)
                    continue
                credits[rel] = {"title": title.replace("_", " ")[:60],
                                "author": strip(meta.get("Artist", {}).get("value", ""))[:80],
                                "license": lic}
                got += 1
                took += 1
                print("[%s] %s  (%s)" % (cat, title[:60], lic))
                time.sleep(1.0)  # не нагружаем Commons
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(credits, f, ensure_ascii=False, indent=1)
    print("Готово. Положи папку assets рядом с main.py и пересобери APK.")


if __name__ == "__main__":
    main()
