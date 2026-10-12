#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_emails.py — HOKOLITE KOL 开发信 SMTP 发送器

把 kol-personalized-outreach 产出的 JSON 批次，经 SMTP 真实发送。
这是「手」：确定性的连接/发送/限速/日志。是否该发、发给谁，是「脑」的事，不在这里。

设计红线：
  1. 默认 dry-run —— 不加 --send 只做本地预览，绝不连服务器。
  2. 真发必须同时给 --send --yes，防止手滑。
  3. 密码永不写死在代码里：优先环境变量 SMTP_PASS，其次 --config 指向的本地文件。
  4. 发送前复用 check_email.py 的硬门；不过门的邮件直接跳过，不带病发出。
  5. 只发 recommended=true 且 email 非空的记录；其余跳过并说明原因。
  6. 单条失败不中断整批；全程写 JSONL 日志（不含密码）。

用法：
  # 预览（默认）
  python send_emails.py --json output/outreach/<batch>.json \\
      --provider gmail --from-name "Your Name" --from-email you@gmail.com

  # 真发（Gmail，先设环境变量）
  set SMTP_PASS=xxxx xxxx xxxx xxxx
  python send_emails.py --json ... --provider gmail \\
      --from-name "Your Name" --from-email you@gmail.com --send --yes --limit 3 --delay 45
"""
import argparse
import json
import os
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

# 复用硬门（同目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_email import validate_body, word_count  # noqa: E402

# ---- 邮箱服务商预设 ----
PROVIDERS = {
    "gmail": {
        "host": "smtp.gmail.com", "port": 465, "ssl": True,
        "note": "需先开启两步验证，再生成 16 位 App Password（不是登录密码）",
    },
    "qq": {
        "host": "smtp.qq.com", "port": 465, "ssl": True,
        "note": "设置→账户→开启 SMTP 服务，生成『授权码』（16 位，不是 QQ 密码）",
    },
    "163": {
        "host": "smtp.163.com", "port": 465, "ssl": True,
        "note": "开启 SMTP 后生成授权码",
    },
    "outlook": {
        "host": "smtp-mail.outlook.com", "port": 587, "ssl": False,
        "note": "STARTTLS；个人账户常被限，建议用 app password",
    },
}

def _find_workspace():
    """定位项目根（含 .workbuddy-ai/ 或 products/catalog.json 的目录）。
    可用环境变量 KOL_WORKSPACE 覆盖；探测失败时按 skill 目录层级推导。"""
    env = os.environ.get("KOL_WORKSPACE")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / ".workbuddy-ai").is_dir() or (p / "products" / "catalog.json").exists():
            return p
    # <ws>/.workbuddy-ai/skills/<skill>/scripts/x.py -> parents[4]
    return here.parents[4] if len(here.parents) > 4 else here.parent


WORKSPACE = _find_workspace()
DEFAULT_CONFIG = str(WORKSPACE / ".secrets" / "send-config.json")
DEFAULT_LOG = str(WORKSPACE / "output" / "outreach" / "send-log.jsonl")


def load_config(path):
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {}


def resolve(args, cfg):
    """优先级：CLI > 配置文件 > 环境变量。返回 (host, port, use_ssl, user, password, from_email, from_name, reply_to)。"""
    provider = args.provider or cfg.get("provider")
    preset = PROVIDERS.get(provider, {})
    host = args.host or cfg.get("smtp_host") or preset.get("host")
    port = args.port or cfg.get("smtp_port") or preset.get("port") or 465
    use_ssl = cfg.get("use_ssl", preset.get("ssl", True)) if not args.starttls else False
    if args.starttls:
        use_ssl = False
    user = args.smtp_user or cfg.get("smtp_user") or os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS") or cfg.get("smtp_pass")
    if password:
        # Gmail App Password 常以 4 组 4 位、空格分隔显示；SMTP 用无空格形式。
        password = password.replace(" ", "").strip()
    from_email = args.from_email or cfg.get("from_email") or user
    from_name = args.from_name or cfg.get("from_name") or ""
    reply_to = args.reply_to or cfg.get("reply_to") or from_email
    return host, int(port), use_ssl, user, password, from_email, from_name, reply_to


def build_message(rec, from_email, from_name, reply_to, unsubscribe):
    body = rec["email_body"].strip()
    if unsubscribe:
        body = body + "\n\n" + unsubscribe
    msg = EmailMessage()
    msg["Subject"] = rec["email_subject_primary"]
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = rec["email"]
    msg["Reply-To"] = reply_to
    msg["Date"] = None  # 交给 smtplib 填
    msg.set_content(body, subtype="plain", charset="utf-8")
    return msg


def collect_targets(data, only=None):
    """返回 (targets, skips)。targets 为可发送记录；skips 为 [(name, reason)]。"""
    records = data.get("records", data) if isinstance(data, dict) else data
    targets, skips = [], []
    for rec in records:
        name = rec.get("creator_name") or rec.get("id") or "?"
        if only and rec.get("id") not in only:
            continue
        if rec.get("recommended") is False:
            skips.append((name, "recommended=false（未达建联门槛）"))
            continue
        if not rec.get("email"):
            skips.append((name, "无邮箱（email 为空，需由第三方 ERP 补）"))
            continue
        if not rec.get("email_body"):
            skips.append((name, "无邮件正文"))
            continue
        targets.append(rec)
    return targets, skips


def precheck(rec, min_words, max_words):
    """发送前复用硬门。返回 problems 列表。"""
    prod = rec.get("recommended_product") or {}
    pname = prod.get("name") if isinstance(prod, dict) else ""
    problems, _warn, _oks = validate_body(
        rec["email_body"], rec.get("creator_name", ""), pname or "", min_words, max_words
    )
    return problems


def log_line(path, entry):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="HOKOLITE 开发信 SMTP 发送器")
    ap.add_argument("--json", required=True, help="outreach 批次 JSON 路径")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help="本地配置 JSON（含凭据）")
    ap.add_argument("--provider", choices=list(PROVIDERS), help="邮箱服务商预设")
    ap.add_argument("--host")
    ap.add_argument("--port", type=int)
    ap.add_argument("--starttls", action="store_true", help="用 587 STARTTLS 而非 465 SSL")
    ap.add_argument("--smtp-user", help="SMTP 登录名（通常=邮箱）")
    ap.add_argument("--from-email", help="发件地址")
    ap.add_argument("--from-name", help="发件显示名")
    ap.add_argument("--reply-to", help="回信地址，默认同发件")
    ap.add_argument("--unsubscribe", default="", help="附加退订说明（合规，建议填）")
    ap.add_argument("--only", nargs="*", help="只发指定 id（空格分隔）")
    ap.add_argument("--limit", type=int, default=0, help="最多发 N 条（0=不限）")
    ap.add_argument("--delay", type=float, default=45.0, help="每条间隔秒数（默认 45）")
    ap.add_argument("--min-words", type=int, default=100)
    ap.add_argument("--max-words", type=int, default=160)
    ap.add_argument("--log", default=DEFAULT_LOG, help="JSONL 发送日志路径")
    ap.add_argument("--send", action="store_true", help="真的发送（默认只预览）")
    ap.add_argument("--yes", action="store_true", help="确认发送，与 --send 同时给")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    targets, skips = collect_targets(data, set(args.only) if args.only else None)

    print("=" * 64)
    print(f"批次：{args.json}")
    print(f"可发送：{len(targets)} 条   跳过：{len(skips)} 条")
    print("=" * 64)

    for name, reason in skips:
        print(f"  [SKIP] {name} — {reason}")

    # 硬门预检
    ready, blocked = [], []
    for rec in targets:
        problems = precheck(rec, args.min_words, args.max_words)
        if problems:
            blocked.append((rec, problems))
        else:
            ready.append(rec)

    for rec, problems in blocked:
        print(f"  [GATE] {rec.get('creator_name')} 未过硬门，跳过：{'; '.join(problems)}")

    if args.limit:
        ready = ready[: args.limit]

    if not ready:
        print("\n没有可发送的邮件。结束。")
        return 0

    host, port, use_ssl, user, password, from_email, from_name, reply_to = resolve(args, cfg)

    print("\n将要发送：")
    for rec in ready:
        print(f"  → {rec.get('creator_name'):<28} <{rec['email']}>  |  {rec['email_subject_primary']}")

    # ---- 预览模式 ----
    if not (args.send and args.yes):
        print("\n[DRY-RUN] 未发送。确认无误后加 --send --yes 真实发送。")
        if not (args.send and args.yes):
            missing = []
            if not from_email:
                missing.append("发件地址 --from-email")
            if not user:
                missing.append("SMTP 登录名 --smtp-user")
            if not password:
                missing.append("密码（环境变量 SMTP_PASS 或配置文件 smtp_pass）")
            if missing:
                print("[DRY-RUN] 真发前还缺：" + "、".join(missing))
        return 0

    # ---- 真发 ----
    if not all([host, user, password, from_email]):
        print("错误：真发需要 host / smtp_user / password / from_email 齐全。")
        return 2

    print(f"\n连接 {host}:{port} ({'SSL' if use_ssl else 'STARTTLS'}) ...")
    context = ssl.create_default_context()
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
        else:
            server = smtplib.SMTP(host, port, timeout=30)
            server.starttls(context=context)
        server.login(user, password)
    except Exception as e:
        print(f"连接/登录失败：{e}")
        return 2

    sent, failed = 0, 0
    try:
        for i, rec in enumerate(ready, 1):
            msg = build_message(rec, from_email, from_name, reply_to, args.unsubscribe)
            try:
                server.send_message(msg)
                sent += 1
                print(f"  [{i}/{len(ready)}] SENT  {rec.get('creator_name')} <{rec['email']}>")
                log_line(args.log, {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "status": "sent", "id": rec.get("id"),
                    "to": rec["email"], "subject": rec["email_subject_primary"],
                    "from": from_email,
                })
            except Exception as e:
                failed += 1
                print(f"  [{i}/{len(ready)}] FAIL  {rec.get('creator_name')} — {e}")
                log_line(args.log, {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "status": "failed", "id": rec.get("id"),
                    "to": rec.get("email"), "error": str(e),
                })
            if i < len(ready) and args.delay > 0:
                time.sleep(args.delay)
    finally:
        try:
            server.quit()
        except Exception:
            pass

    print("=" * 64)
    print(f"完成：成功 {sent}，失败 {failed}。日志：{args.log}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
