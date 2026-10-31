#!/usr/bin/env python3
"""Скачивает реалистичную живопись и фото в assets/pics/<Категория>/ (запускать на компьютере).

Источники (все со свободной лицензией, ключи не нужны):
  met     — The Met, Open Access (CC0), европейская живопись
  aic     — Art Institute of Chicago, public domain (CC0)
  commons — Wikimedia Commons (NASA, ранние фильмы; только PD/CC0, с --allow-cc ещё CC BY/BY-SA)

    pip install pillow
    python fetch_art.py                       # всё из CATEGORIES
    python fetch_art.py --per-cat 24          # до 24 картин на категорию
    python fetch_art.py --only Море Пейзажи   # только эти категории
    python fetch_art.py --hires               # Met: исходник вместо web-large (дольше и тяжелее)

Каждая картина обрезается по центру в квадрат и сохраняется 1280x1280 JPEG (~250-400 КБ).
assets/credits.json хранит название, автора, лицензию и ссылку: игра показывает автора под картиной.
Просмотри результат глазами и удали лишнее: поиск иногда приносит не то.
"""
import argparse
import io
import json
import os
import random
import re
import time
import urllib.parse
import urllib.request

from PIL import Image

UA = "PicrossArtFetcher/1.0 (personal hobby app; replace-with-your-email@example.com)"
MET = "https://collectionapi.metmuseum.org/public/collection/v1"
AIC = "https://api.artic.edu/api/v1/artworks/search"
COMMONS = "https://commons.wikimedia.org/w/api.php"

CATEGORIES = {
    "Пейзажи": [("met", "landscape"), ("met", "mountains landscape"), ("met", "river valley"),
                ("met", "forest trees"), ("met", "sunset landscape"), ("aic", "landscape")],
    "Море": [("met", "seascape"), ("met", "ships at sea"), ("met", "harbor"),
             ("met", "coast cliffs sea"), ("met", "stormy sea"), ("aic", "seascape")],
    "Цветы и натюрморты": [("met", "bouquet of flowers"), ("met", "still life fruit"),
                           ("met", "roses"), ("aic", "flowers")],
    "Зима": [("met", "winter landscape snow"), ("met", "skaters ice"), ("aic", "winter snow")],
    "Города": [("met", "view of Venice"), ("met", "street scene city"),
               ("met", "Paris boulevard"), ("aic", "city street")],
    "Портреты": [("met", "portrait of a lady"), ("met", "portrait of a man"),
                 ("met", "girl portrait"), ("aic", "portrait")],
    "Мифы и сказки": [("met", "mythology"), ("met", "angels"), ("met", "knight"),
                      ("met", "fairy tale"), ("aic", "mythological")],
    "Животные": [("met", "horses"), ("met", "dogs"), ("met", "birds"), ("met", "lion"), ("aic", "animals")],
    "Космос": [("commons", "NASA Hubble nebula"), ("commons", "NASA James Webb image"),
               ("commons", "NASA Pillars of Creation"), ("commons", "NASA Earthrise Apollo 8")],
    "Кино и мультики (до 1931)": [("commons", "Nosferatu 1922 film still"),
                                  ("commons", "Metropolis 1927 film still"),
                                  ("commons", "Charlie Chaplin The Kid 1921"),
                                  ("commons", "Steamboat Willie 1928"),
                                  ("commons", "A Trip to the Moon 1902 Melies")],
}

OK_FREE = re.compile(r"public domain|^pd\b|cc0|cc[- ]zero", re.I)
OK_CC = re.compile(r"cc[- ]by", re.I)


def fetch_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "AIC-User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def jget(url, **params):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    return json.loads(fetch_bytes(url, 40).decode("utf-8"))


def strip(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def slug(s):
    return re.sub(r"[^\w\-]+", "_", s, flags=re.U).strip("_")[:50] or "image"


# ───────────── источники: каждый yield-ит dict(id, title, author, license, url, page) ─────────────
def met_candidates(q, args, rng):
    d = jget(MET + "/search", q=q, hasImages="true", isPublicDomain="true",
             medium="Paintings", departmentId=11)
    ids = d.get("objectIDs") or []
    rng.shuffle(ids)
    for oid in ids[:80]:
        try:
            o = jget(MET + "/objects/%d" % oid)
        except Exception:
            continue
        url = o.get("primaryImage") if args.hires else (o.get("primaryImageSmall") or o.get("primaryImage"))
        if not o.get("isPublicDomain") or not url:
            continue
        yield dict(id="met%d" % oid, title=o.get("title", ""), author=o.get("artistDisplayName", ""),
                   license="CC0 (The Met)", url=url, page=o.get("objectURL", ""))


def aic_candidates(q, args, rng):
    d = jget(AIC, q=q, limit=60, fields="id,title,artist_title,image_id,is_public_domain,artwork_type_title",
             **{"query[term][is_public_domain]": "true"})
    rows = d.get("data") or []
    rng.shuffle(rows)
    for a in rows:
        if not a.get("image_id") or not a.get("is_public_domain"):
            continue
        if a.get("artwork_type_title") not in (None, "Painting"):
            continue
        yield dict(id="aic%s" % a["id"], title=a.get("title", ""), author=a.get("artist_title") or "",
                   license="CC0 (Art Institute of Chicago)",
                   url="https://www.artic.edu/iiif/2/%s/full/843,/0/default.jpg" % a["image_id"],
                   page="https://www.artic.edu/artworks/%s" % a["id"])


def commons_candidates(q, args, rng):
    d = jget(COMMONS, action="query", format="json", generator="search", gsrnamespace=6,
             gsrsearch=q + " filetype:bitmap", gsrlimit=40, prop="imageinfo",
             iiprop="url|size|mime|extmetadata", iiurlwidth=1600)
    pages = list(d.get("query", {}).get("pages", {}).values())
    pages.sort(key=lambda p: p.get("index", 0))
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = strip(meta.get("LicenseShortName", {}).get("value", ""))
        if not (OK_FREE.search(lic) or (args.allow_cc and OK_CC.search(lic))):
            continue
        if ii.get("mime") not in ("image/jpeg", "image/png"):
            continue
        yield dict(id="wc%s" % pg.get("pageid"), title=re.sub(r"\.\w+$", "", pg["title"].replace("File:", "")),
                   author=strip(meta.get("Artist", {}).get("value", ""))[:80], license=lic,
                   url=ii.get("thumburl") or ii["url"], page=ii.get("descriptionurl", ""))


SOURCES = {"met": met_candidates, "aic": aic_candidates, "commons": commons_candidates}


def process(raw, dst, args):
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    if min(w, h) < args.min_side or min(w, h) / max(w, h) < args.min_ratio:
        return False
    s = min(w, h)
    x0, y0 = (w - s) // 2, (h - s) // 2
    img = img.crop((x0, y0, x0 + s, y0 + s))
    if s != args.size:
        img = img.resize((args.size, args.size), Image.LANCZOS)
    img.save(dst, "JPEG", quality=88, optimize=True)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets")
    ap.add_argument("--per-cat", type=int, default=16)
    ap.add_argument("--per-query", type=int, default=4)
    ap.add_argument("--only", nargs="*", help="названия категорий")
    ap.add_argument("--allow-cc", action="store_true")
    ap.add_argument("--hires", action="store_true")
    ap.add_argument("--size", type=int, default=1280)
    ap.add_argument("--min-side", type=int, default=700)
    ap.add_argument("--min-ratio", type=float, default=0.62, help="отсев слишком вытянутых картин")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    cpath = os.path.join(args.out, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}

    for cat, queries in CATEGORIES.items():
        if args.only and cat not in args.only:
            continue
        cdir = os.path.join(args.out, "pics", cat)
        os.makedirs(cdir, exist_ok=True)
        got = len([f for f in os.listdir(cdir) if f.lower().endswith(".jpg")])
        print("== %s (уже %d) ==" % (cat, got))
        for src, q in queries:
            if got >= args.per_cat:
                break
            took = 0
            try:
                cands = SOURCES[src](q, args, rng)
                for c in cands:
                    if took >= args.per_query or got >= args.per_cat:
                        break
                    rel = "%s/%s_%s.jpg" % (cat, c["id"], slug(c["title"]))
                    dst = os.path.join(args.out, "pics", rel)
                    if os.path.exists(dst):
                        continue
                    try:
                        if not process(fetch_bytes(c["url"]), dst, args):
                            continue
                    except Exception as e:
                        print("  не скачалось:", c["title"][:40], e)
                        continue
                    credits[rel] = {"title": c["title"][:60], "author": c["author"][:80],
                                    "license": c["license"], "page": c["page"]}
                    got += 1
                    took += 1
                    print("  [%s] %s — %s" % (src, c["title"][:50], c["author"][:30]))
                    time.sleep(args.delay)
            except Exception as e:
                print("  источник %s / %r не ответил: %s" % (src, q, e))
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(credits, f, ensure_ascii=False, indent=1)
    print("Готово. Положи папку assets рядом с main.py, закоммить и пересобери APK.")


if __name__ == "__main__":
    main()
