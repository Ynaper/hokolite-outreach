#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_catalog.py — 产品库构建（确定性脚本，属「手」）

职责：
  1. 抓取 Shopify 公开 JSON（/products.json、/collections/{handle}/products.json）
  2. 归一化客观字段 → HOKOLITE 产品库 catalog.json
  3. 合并用户提供的 CSV 文件（products/raw/*.csv），用户值覆盖自动值

不做（属「脑」，交给 agent）：
  - 补语义字段：one_liner / selling_points / use_scenarios / audience / competitor_analogs
  - xlsx / pdf / docx 解析（用 sheetagent / pdf / docx skill）

用法：
  python build_catalog.py \
    --shopify https://hokolite.com/products.json \
    --collections work-lights,headlamps,edc-flashlights,camping-lanterns,best-sellers,new-arrivals \
    --inbox products/raw \
    --out products/catalog.json

路径说明：`products/raw`、`products/catalog.json` 均相对 **skill 目录**（产品库打包在 skill 内，
随 `npx skills add` 一起分发）。也可传任意绝对路径覆盖。
"""
import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

UA = "Mozilla/5.0 (compatible; hokolite-catalog-builder/1.0)"
TODAY = date.today().isoformat()

CATEGORY_RULES = [
    ("headlamp", ["headlamp", "head lamp", "head-light", "head light"]),
    ("work_light", ["work light", "work-light", "underhood", "flood light", "mechanic light"]),
    ("camping_lantern", ["lantern", "camp light", "camping light"]),
    ("bike_light", ["bike light", "bicycle light", "tail light", "front rear"]),
    ("spotlight", ["spotlight", "search light", "spot light"]),
    ("edc_flashlight", ["flashlight", "edc", "pen light", "torch", "keychain light"]),
]


# ---------------------------------------------------------------- HTTP

def fetch_json(url, retries=3, timeout=30):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retries - 1:
                time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"fetch failed: {url} ({last})")


def fetch_all_products(base, limit=250):
    """分页抓取 /products.json，直到返回不足一页。"""
    out, page = [], 1
    while True:
        url = f"{base}?limit={limit}&page={page}"
        data = fetch_json(url)
        items = data.get("products", []) or []
        out.extend(items)
        print(f"  page {page}: +{len(items)} (total {len(out)})", file=sys.stderr)
        if len(items) < limit:
            break
        page += 1
        time.sleep(0.5)
    return out


def fetch_collections(base_root, handles):
    """返回 {product_handle: [collection_handle, ...]}。失败不致命。"""
    membership = {}
    for ch in handles:
        ch = ch.strip()
        if not ch:
            continue
        try:
            data = fetch_json(f"{base_root}/collections/{ch}/products.json?limit=250")
            for p in data.get("products", []) or []:
                h = p.get("handle")
                if h:
                    membership.setdefault(h, []).append(ch)
            print(f"  collection {ch}: {len(data.get('products', []))}", file=sys.stderr)
            time.sleep(0.3)
        except Exception as e:  # noqa: BLE001
            print(f"  ! collection {ch} failed: {e}", file=sys.stderr)
    return membership


# ---------------------------------------------------------------- normalize

def strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|li|h[1-6]|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "• ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def extract_bullets(body_html):
    if not body_html:
        return []
    out = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", body_html, flags=re.I | re.S):
        t = strip_html(li)
        if t:
            out.append(t)
    return out


def infer_category(p):
    hay = " ".join(
        [
            str(p.get("product_type") or ""),
            str(p.get("title") or ""),
            " ".join(p.get("tags") or []),
        ]
    ).lower()
    for cat, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in hay:
                return cat
    return "other"


def normalize(p, membership, collections):
    variants = p.get("variants") or []
    prices = []
    for v in variants:
        try:
            prices.append(float(v.get("price")))
        except (TypeError, ValueError):
            pass
    in_stock = any(bool(v.get("available")) for v in variants) if variants else True
    sku = next((v.get("sku") for v in variants if v.get("sku")), "")
    images = p.get("images") or []
    handle = p.get("handle") or str(p.get("id"))
    body_html = p.get("body_html") or ""
    cols = membership.get(handle, [])
    return {
        # ---- 客观字段 ----
        "id": handle,
        "sku": sku,
        "name": p.get("title") or "",
        "brand": p.get("vendor") or "HOKOLITE",
        "category": infer_category(p),
        "product_type_raw": p.get("product_type") or "",
        "price_usd": round(min(prices), 2) if prices else None,
        "url": f"https://hokolite.com/products/{handle}",
        "image_url": images[0].get("src") if images else None,
        "in_stock": in_stock,
        "tags": p.get("tags") or [],
        "collections": cols,
        "body_text": strip_html(body_html),
        "bullets": extract_bullets(body_html),
        "published_at": p.get("published_at"),
        "source_ref": f"shopify:products.json#{p.get('id')}",
        "observed_at": TODAY,
        # ---- 语义字段（agent 补） ----
        "one_liner": "",
        "key_specs": {
            "lumens": None,
            "battery_mah": None,
            "recharge": None,
            "runtime_h": None,
            "weight_g": None,
            "waterproof": None,
        },
        "selling_points": [],
        "use_scenarios": [],
        "audience": [],
        "competitor_analogs": [],
        "claims_to_avoid": [],
    }


# ---------------------------------------------------------------- inbox (CSV)

LIST_SPLIT = re.compile(r"\s*[;|]\s*")


def _split_list(v):
    if not v:
        return []
    return [x.strip() for x in LIST_SPLIT.split(str(v)) if x.strip()]


def merge_csv(path, products_by_key):
    """用户 CSV 覆盖。列名尽量宽松匹配。"""
    applied = 0
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            low = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            key = low.get("handle") or low.get("sku") or low.get("name") or low.get("id")
            prod = None
            if key:
                prod = (
                    products_by_key.get(("handle", key))
                    or products_by_key.get(("sku", key))
                    or products_by_key.get(("name", key))
                )
            if not prod:
                continue
            # 直接覆盖的标量字段
            if low.get("name"):
                prod["name"] = low["name"]
            if low.get("category"):
                prod["category"] = low["category"]
            if low.get("price_usd"):
                try:
                    prod["price_usd"] = float(low["price_usd"])
                except ValueError:
                    pass
            if low.get("one_liner"):
                prod["one_liner"] = low["one_liner"]
            if low.get("url"):
                prod["url"] = low["url"]
            # 列表字段
            for col, field in (
                ("use_scenarios", "use_scenarios"),
                ("audience", "audience"),
                ("competitor_analogs", "competitor_analogs"),
                ("claims_to_avoid", "claims_to_avoid"),
                ("tags", "tags"),
            ):
                if low.get(col):
                    prod[field] = _split_list(low[col])
            # 卖点：格式 "point|benefit|scenario1,scenario2;;point2|benefit2|..."
            if low.get("selling_points"):
                sp = []
                for chunk in re.split(r"\s*;;\s*", low["selling_points"]):
                    parts = [x.strip() for x in chunk.split("|")]
                    if not parts or not parts[0]:
                        continue
                    sp.append(
                        {
                            "point": parts[0],
                            "benefit": parts[1] if len(parts) > 1 else "",
                            "scenarios": _split_list(parts[2].replace(",", ";"))
                            if len(parts) > 2
                            else [],
                        }
                    )
                if sp:
                    prod["selling_points"] = sp
            prod["_user_override"] = True
            applied += 1
    return applied


SEMANTIC_FIELDS = (
    "one_liner", "key_specs", "selling_points",
    "use_scenarios", "audience", "competitor_analogs", "claims_to_avoid",
)


def merge_semantics(path, products_by_key):
    """合并 agent 撰写的语义字段。优先级最高（覆盖 CSV 与自动值）。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = data.get("products", data) if isinstance(data, dict) else data
    applied = 0
    for entry in entries:
        key = entry.get("id") or entry.get("handle") or entry.get("sku") or entry.get("name")
        prod = (
            products_by_key.get(("handle", key))
            or products_by_key.get(("sku", key))
            or products_by_key.get(("name", key))
        )
        if not prod:
            print(f"  ! semantics: no match for {key}", file=sys.stderr)
            continue
        for f in SEMANTIC_FIELDS:
            if f in entry and entry[f] not in (None, "", [], {}):
                prod[f] = entry[f]
        applied += 1
    return applied


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="构建 HOKOLITE 产品库 catalog.json")
    ap.add_argument("--shopify", default="https://hokolite.com/products.json",
                    help="Shopify products.json 端点")
    ap.add_argument("--collections", default="",
                    help="逗号分隔的 collection handle（可选，用于标注归属）")
    ap.add_argument("--inbox", default="", help="用户产品文件目录（解析 *.csv）")
    ap.add_argument("--semantics", default="",
                    help="agent 撰写的语义字段 JSON（keyed by id/sku/name），优先级最高")
    ap.add_argument("--out", default="catalog.json", help="输出 catalog.json 路径")
    args = ap.parse_args(argv)

    base = args.shopify.rstrip("/")
    root = base[: -len("/products.json")] if base.endswith("/products.json") else base

    print(f"[1/4] 抓取产品列表 {base}", file=sys.stderr)
    raw_products = fetch_all_products(base)
    print(f"      → {len(raw_products)} 个产品", file=sys.stderr)

    membership = {}
    if args.collections:
        print("[2/4] 抓取 collection 归属", file=sys.stderr)
        membership = fetch_collections(root, args.collections.split(","))
    else:
        print("[2/4] 跳过 collections", file=sys.stderr)

    products = [normalize(p, membership, args.collections) for p in raw_products]

    # 去重（同 handle）
    seen, uniq = set(), []
    for p in products:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
    products = uniq

    # 索引，供 CSV 覆盖
    by_key = {}
    for p in products:
        by_key[("handle", p["id"])] = p
        if p["sku"]:
            by_key[("sku", p["sku"])] = p
        by_key[("name", p["name"])] = p

    applied = 0
    if args.inbox:
        inbox = Path(args.inbox)
        if inbox.is_dir():
            csvs = sorted(inbox.glob("*.csv"))
            print(f"[3/4] 合并用户文件 {len(csvs)} 个 CSV", file=sys.stderr)
            for c in csvs:
                n = merge_csv(c, by_key)
                applied += n
                print(f"      {c.name}: 覆盖 {n} 行", file=sys.stderr)
        else:
            print(f"[3/4] inbox 不存在，跳过：{inbox}", file=sys.stderr)
    else:
        print("[3/4] 未指定 inbox", file=sys.stderr)

    sem_applied = 0
    if args.semantics and Path(args.semantics).is_file():
        sem_applied = merge_semantics(args.semantics, by_key)
        print(f"      合并语义字段 {sem_applied} 个产品", file=sys.stderr)

    catalog = {
        "version": TODAY,
        "brand": "HOKOLITE",
        "sources": [f"shopify:{base}"] + ([f"user:{args.inbox}"] if args.inbox else []),
        "product_count": len(products),
        "products": products,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")

    # 统计
    cats = {}
    semantic_ready = 0
    for p in products:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
        if p["selling_points"] and p["use_scenarios"] and p["audience"]:
            semantic_ready += 1

    print(f"[4/4] 写出 {out}", file=sys.stderr)
    print(json.dumps({
        "product_count": len(products),
        "by_category": cats,
        "in_stock": sum(1 for p in products if p["in_stock"]),
        "csv_overrides_applied": applied,
        "semantics_applied": sem_applied,
        "semantic_fields_ready": semantic_ready,
        "note": "semantic_fields_ready 为 0 属正常——语义字段需 agent 后续补齐",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
