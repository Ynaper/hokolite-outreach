# HOKOLITE Outreach — Personalized KOL Outreach Skill

A portable [Agent Skills](https://agentskills.io) skill for first-touch outreach to creators.
Give it a creator profile link (YouTube / Instagram / Facebook) and it:

1. **researches** the channel (via the host's WebFetch / WebSearch),
2. **matches** the best-fitting HOKOLITE product from the catalog,
3. **writes a personalized** English outreach email (subject + body + a Chinese rationale),
4. **outputs** a structured JSON record.

Draft-only by default. Nothing is ever sent unless you explicitly opt in (`--send --yes`).

> Skill documentation (`SKILL.md` and `references/`) is written in Chinese; the generated emails are in English.

---

## Install

```bash
# install into the current project (works in Claude Code, Codex, Cursor, WorkBuddy, …)
npx skills add Ynaper/hokolite-outreach

# or target a specific host / skill explicitly
npx skills add Ynaper/hokolite-outreach --skill kol-personalized-outreach -a claude-code
```

Then, in your agent, just hand it a link:

> 给这个达人写开发信 https://www.youtube.com/@somecreator

---

## After install

The product catalog ships **inside the skill**, so `npx skills add` gives you a fully working
skill with no extra steps:

```
<your-project>/
└── .claude/skills/kol-personalized-outreach/
    ├── SKILL.md
    ├── references/
    ├── scripts/
    └── products/            ← bundled: catalog + brand facts
        ├── catalog.json
        ├── brand-facts.md
        └── semantic-fields.json
```

- **Brand facts** — edit `products/brand-facts.md` (inside the installed skill) and replace
  `[YOUR NAME]` / `[TITLE]` with a real name and title. This is a CAN-SPAM requirement and
  affects how the email reads.
- **Your own catalog** — swap `products/catalog.json` for your brand's, or rebuild it with
  `scripts/build_catalog.py --shopify <your-site>/products.json`.
- **Sending (optional)** — SMTP setup lives in `references/sending.md`.
  Config template: `references/send-config.example.json`
  (copy it to `<project>/.secrets/send-config.json`). Never commit real credentials.

> `output/` and `.secrets/` are resolved relative to your **project root**, not the skill dir.

---

## Repo layout

```
hokolite-outreach/
└── skills/kol-personalized-outreach/     # the skill (discovered by `npx skills add`)
    ├── SKILL.md                          # single contract + 7-step workflow
    ├── references/                       # 9 spec docs + send-config.example.json
    ├── scripts/                          # build_catalog.py / check_email.py / send_emails.py
    └── products/                         # bundled HOKOLITE catalog + brand facts
```

## Notes

- The catalog (`products/catalog.json`) is HOKOLITE's own product data, rebuilt from the
  public Shopify feed with `scripts/build_catalog.py`.
- Competitor brand names appear only as neutral reference points for email bridging.
- Never commit `.secrets/`, `output/`, or `send-log.jsonl` — they contain credentials and
  real creator/contact data. See `.gitignore`.
