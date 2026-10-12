#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_email.py — 邮件质量硬门（确定性脚本，属「手」）

校验 references/email-spec.md 里的机器可判定项：
  1. 正文字数 ∈ [min, max]（默认 100–160）
  2. 禁用词扫描（AI 模板味 / 过度推销承诺 / 硬 CTA）
  3. 正文首词 ∉ {I, We, Our}
  4. 首触正文链接数 = 0
  5. 必备 token：达人名 + 产品名

不做（属「脑」，交给 agent 自检）：事实性核查、Tone 复核、卖点一致性。

用法：
  python check_email.py --email path/to/email.md \
    --creator-name "Marcus Reed" --product-name "CLAKAP W7"
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---- 禁用短语（大小写不敏感子串匹配）----
BANNED_PHRASES = [
    # AI 模板味
    "i came across your profile", "impressed by your content", "perfect fit",
    "authentic style", "this will resonate", "your inbox must be busy",
    "as a passionate", "leverage", "synergy", "game-changer", "game changer",
    "revolutionary", "cutting-edge", "cutting edge", "elevate", "unleash",
    "seamless", "dive into", "in today's landscape", "we're excited to",
    # 过度推销 / 承诺（绝对禁止）
    "free sample", "free samples", "we'll pay", "we will pay", "commission",
    "sponsorship fee", "guaranteed", "100%", "risk-free", "risk free",
    "limited time", "act now", "don't miss", "dont miss",
    # 硬 CTA（首触禁用）
    "book a call", "are you free", "let's hop on a call", "lets hop on a call",
    "schedule a meeting", "schedule a call",
    # 开头套话
    "hope this finds you well", "i'm reaching out", "i am reaching out",
    "i wanted to",
]

FIRST_WORD_BAN = {"i", "we", "our", "i'm", "we're", "i've", "we've"}

# 首触禁用词里，单独的 "I/We/Our" 只查首词；这里额外给个提醒
FIRST_PERSON = re.compile(r"\b(i|we|our|us|my|mine|ours)\b", re.I)

LINK_RE = re.compile(r"(https?://\S+|www\.\S+)", re.I)

# 引号内容（多为引用的视频/帖子标题）不计入作者口吻统计
QUOTED_RE = re.compile(r'"[^"]*"|\u201c[^\u201d]*\u201d|\u2018[^\u2019]*\u2019')


def strip_quoted(text):
    """移除引号内的引用内容，只保留作者自己写的话。"""
    return QUOTED_RE.sub(" ", text)


def extract_body(md_text):
    """从 email.md 取 ## Body 段（到下一个 ## 或 --- 或 EOF）。"""
    m = re.search(r"^##\s+Body\s*$", md_text, re.M | re.I)
    if not m:
        return None
    rest = md_text[m.end():]
    stop = re.search(r"^(##\s|---\s*$)", rest, re.M)
    body = rest[: stop.start()] if stop else rest
    return body.strip()


def word_count(text):
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def validate_body(body, creator_name, product_name, min_words, max_words):
    """对一段正文文本做全部硬门检查，返回 (problems, warnings, oks)。"""
    problems, warnings, oks = [], [], []

    # 1. 字数
    n = word_count(body)
    if min_words <= n <= max_words:
        oks.append(f"字数 {n} 词 ∈ [{min_words},{max_words}]")
    else:
        problems.append(f"字数 {n} 词，超出 [{min_words},{max_words}]")

    # 2. 禁用词
    low = body.lower()
    hits = []
    for ph in BANNED_PHRASES:
        idx = low.find(ph)
        if idx != -1:
            hits.append(ph)
    if hits:
        problems.append("命中禁用词：" + ", ".join(sorted(set(hits))))
    else:
        oks.append("无禁用词")

    # 3. 首词
    tokens = re.findall(r"[A-Za-z']+", body)
    first = tokens[0].lower() if tokens else ""
    if first in FIRST_WORD_BAN:
        problems.append(f"正文首词为 '{first}'（禁止 I/We/Our）")
    else:
        oks.append(f"首词 '{first}' 合规")

    # 4. 链接
    links = LINK_RE.findall(body)
    if links:
        problems.append(f"正文含 {len(links)} 个链接（首触应为 0）：{links}")
    else:
        oks.append("无链接")

    # 5. 必备 token
    for label, tok in (("达人名", creator_name), ("产品名", product_name)):
        if not tok:
            warnings.append(f"未提供{label}，跳过校验")
            continue
        if tok.lower() in low:
            oks.append(f"含{label} '{tok}'")
            continue
        # 宽松匹配：名字/产品名可能只写了其中一部分（如 "Mr Baz Reviews" 只写 "Baz"）
        parts = [w for w in re.findall(r"[A-Za-z0-9]{3,}", tok)]
        hit = [w for w in parts if w.lower() in low]
        if hit:
            oks.append(f"含{label}关键词 {hit}（宽松匹配）")
        else:
            problems.append(f"未找到{label} '{tok}'")

    # 6. 第一人称频率（提醒，不失败）；引号内引用标题不计入
    fp = FIRST_PERSON.findall(strip_quoted(body))
    if len(fp) > 2:
        warnings.append(f"第一人称出现 {len(fp)} 次（建议 ≤2，保持克制）")

    return problems, warnings, oks


def report(label, problems, warnings, oks):
    print("=" * 60)
    print(f"邮件校验：{label}")
    print("=" * 60)
    for o in oks:
        print(f"  [OK]   {o}")
    for w in warnings:
        print(f"  [WARN] {w}")
    for p in problems:
        print(f"  [FAIL] {p}")
    print("-" * 60)
    if problems:
        print(f"结果：FAIL（{len(problems)} 项未通过）—— 回炉重写")
        return 1
    print("结果：PASS（硬门通过，仍需 agent 做事实性核查与 Tone 复核）")
    return 0


def check(email_path, creator_name, product_name, min_words, max_words):
    md = Path(email_path).read_text(encoding="utf-8")
    body = extract_body(md)
    if body is None:
        print("FAIL: 未找到 '## Body' 段落，无法校验。")
        return 1
    problems, warnings, oks = validate_body(body, creator_name, product_name,
                                             min_words, max_words)
    print(f"  达人名={creator_name!r}  产品名={product_name!r}")
    return report(email_path, problems, warnings, oks)


def check_json_batch(json_path, min_words, max_words):
    """批量校验 JSON 记录。每条需含 email_body；recommended=false 或 email_body 为空的跳过。"""
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data
    total, passed, failed, skipped = 0, 0, 0, 0
    for rec in records:
        name = rec.get("creator_name") or rec.get("channel_name") or rec.get("id") or "?"
        body = rec.get("email_body")
        prod = rec.get("recommended_product") or {}
        pname = prod.get("name") if isinstance(prod, dict) else rec.get("product_name")
        if not body or rec.get("recommended") is False:
            print(f"[SKIP] {name} — 无邮件正文（{rec.get('skip_reason', 'recommended=false')}）")
            skipped += 1
            continue
        total += 1
        problems, warnings, oks = validate_body(body, name, pname or "", min_words, max_words)
        rc = report(f"{name}  ({rec.get('id', '')})", problems, warnings, oks)
        passed += (rc == 0)
        failed += (rc != 0)
        print()
    print("=" * 60)
    print(f"批量结果：{passed}/{total} PASS，{failed} FAIL，{skipped} 跳过")
    return 0 if failed == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="邮件质量硬门校验")
    ap.add_argument("--email", help="单个 email.md 路径")
    ap.add_argument("--json", help="批量：记录 JSON 路径（每条含 email_body）")
    ap.add_argument("--creator-name", default="", help="达人姓名或频道名")
    ap.add_argument("--product-name", default="", help="主推产品名")
    ap.add_argument("--min-words", type=int, default=100)
    ap.add_argument("--max-words", type=int, default=160)
    args = ap.parse_args(argv)
    if args.json:
        return check_json_batch(args.json, args.min_words, args.max_words)
    if not args.email:
        ap.error("需要 --email 或 --json 之一")
    return check(args.email, args.creator_name, args.product_name,
                 args.min_words, args.max_words)


if __name__ == "__main__":
    sys.exit(main())
