---
name: kol-personalized-outreach
version: "1.0.0"
compatibility: "Claude Code, Codex, and other Agent Skills hosts"
allowed-tools: WebFetch, WebSearch, Read, Write, Bash
description: Use when the user gives a creator profile link (YouTube / Instagram / Facebook) and wants an outreach email — "给这个达人写开发信", "达人建联邮件", "写 outreach email", "联系这个博主", "分析这个达人并写邮件", "把这个链接跑一下". Researches the creator's channel content, matches a HOKOLITE product from the catalog, and outputs a structured JSON record (creator info + match reason + English email subject & body + Chinese rationale) written individually per creator — never a template swap. Not for discovering KOL lists — use kol-discovery-youtube.
---

# 达人个性化开发邮件 · KOL Personalized Outreach

> **路径约定**：`scripts/…` 相对本 skill 目录；`products/…`、`output/…`、`.secrets/…` 相对项目根目录。脚本会自动探测项目根（可用环境变量 `KOL_WORKSPACE` 覆盖），因此换机器或换宿主（WorkBuddy / Claude Code / Codex …）都无需改路径。

## 唯一契约：输入链接 → 输出邮件

**输入**：一个达人主页链接。

| 平台 | 链接格式 | 实测状态 |
|---|---|---|
| YouTube | `https://www.youtube.com/@handle`（或 `/channel/UC...`） | ✅ 可用 |
| Instagram | `https://www.instagram.com/handle/` | ✅ 可用 |
| Facebook | `https://www.facebook.com/pagename` | ✅ 可用 |

**输出**：一份 JSON 文件，schema 见 `references/output-schema.md`。一次跑完即产出全部信息：

- 达人信息（名称、链接、粉丝数、简介、频道类型、受众分析）
- 调研依据（相关帖子/视频 + 原始链接 + 来源 + 观察日期）
- 匹配结果（推荐产品 + 分数 + 逐维度理由）
- **英文邮件**（主题行 1 主 2 备 + 正文）
- **中文说明**（为什么这样写，逐条对应达人信号）
- 数据缺口（哪些字段没拿到）

**本 skill 不做**：批量发现 KOL 名单（用 `kol-discovery-youtube`）、获取联系方式（由第三方 ERP 提供）。**发送是可选的最后一环**（见 `references/sending.md`）——默认只出草稿，需显式 `--send --yes` 才真发，且本 skill 从不自动发。

---

## 第一原则：脑和手分开

- **你（agent）负责脑** —— 判断平台与身份、理解达人内容、抽取信号、做产品匹配决策、写邮件、事实核查、Tone 复核。**这些需要理解语义，脚本做不了。**
- **脚本负责手** —— 抓 Shopify 产品 JSON、归一化产品库、算字数、扫禁用词、校验必备要素。**确定性重复计算，别用 LLM 逐条做。**

判据：需要「理解语义」的归你；「确定性重复计算」的归脚本。

## 前置条件

1. 产品库存在：`products/catalog.json`。若不存在或需更新，先跑：
   ```bash
   python scripts/build_catalog.py \
     --shopify https://hokolite.com/products.json \
     --collections work-lights,headlamps,edc-flashlights,camping-lanterns,best-sellers,new-arrivals \
     --inbox products/raw \
     --out products/catalog.json
   ```
2. 品牌事实：`products/brand-facts.md`（署名、口吻、禁用声明）。缺失则邮件署名用 `[YOUR NAME]` 占位符。

## 工作流

### 第 0 步：解析链接 → 定平台
从用户给的链接判断平台（youtube / instagram / facebook），提取 handle 或 page name。**三平台均已实测可用**，无需询问用户。

### 第 1 步：达人调研（你来做，联网）
按 `references/platform-adapters.md` 里对应平台的抓取清单联网调研。**调研必须走 agent 的 WebFetch/WebSearch，不要写抓取脚本**（三平台的反爬与登录墙决定了脚本跑不通）。

**硬要求**：
- 每一条事实都要带 `source_ref`（可回指的来源）+ `observed_at`（观察日期）。
- **先做人号一致性校验**（IG/FB 高危）：比对 bio 互链、内容主题、粉丝量级，对不上就不认。
- 拿不到的字段**如实标 `data_gap`**，不要猜。

### 第 2 步：内容信号提取（你来做）
抽出匹配层要用的信号：品类(niche) / 使用场景(scenarios) / 受众(audience) / **历史测评过的品牌(brand_hits)** / 最佳引用素材(best_citation)。

`brand_hits` 要专门扫：Olight、NEBO、Fenix、Nitecore、Sofirn、Streamlight、Wurkkos、Acebeam、Wuben 等（HOKOLITE 同赛道竞品，**命中即是最强的邮件桥接点**）。

### 第 3 步：产品匹配（你决策 + 规则打分）
按 `references/product-matching.md` 的规则，对 `catalog.json` 里每个在售产品算分，选 **1 个主推产品**。

- 匹配分 **≥ 30 且** 账号活跃 **且** 量级达标 → `recommended=true`，出邮件。
- 任一不达标 → `recommended=false`，**不出邮件**，但在记录里写明匹配分与不推荐理由（这本身是有价值的结论）。

### 第 4 步：邮件生成（你来做，本 skill 的核心）
严格按 `references/email-spec.md` 写：
- 主题行 1 主 + 2 备选；正文 **100–160 英文单词**；5 个 move（Hook / Bridge / Product / Value / CTA）。
- 必须用达人真实姓名或频道名；开头引用其**真实**内容并说明为什么关注；自然引出对应产品 + 1–2 个卖点（不堆参数）；从达人和粉丝角度讲合作价值；软 CTA。
- **绝不承诺**免费样品 / 付费 / 佣金。
- 拿不到具体内容标题时，按 `email-spec.md` 的**事实降级规则**处理，**绝不编造**。
- **内容合规判断**：若唯一可引用的内容题材敏感（如事故、失踪纪念），**主动放弃引用**，降级到频道定位。不为凑 hook 而消费悲剧。

参考完整示例见 `references/email-examples.md`。

### 第 5 步：硬门校验（脚本）
```bash
python scripts/check_email.py \
  --json output/outreach/<批次名>.json
```
校验每条 `email_body`：字数 ∈ [100,160]、无禁用词、首词非 I/We/Our、无链接、含达人名与产品名关键词。
**不过门 → 回炉重写，不带病交付。** 通过后再按 `references/qa-checklist.md` 逐条复核（R1–R6 + G1–G5 + 事实性核查）。

### 第 6 步：输出与交付
写出 JSON 到 `output/outreach/<批次名>.json`（schema 见 `references/output-schema.md`），然后**交付给用户**：宿主若支持预览工具（如 WorkBuddy 的 `present_files`）就直接调用打开；不支持则把文件路径告知用户。并说清：
- 主推哪个产品、为什么（依据哪个信号）
- 邮件引用了哪条真实内容（附来源）
- **哪些数据是估算的、哪些字段没拿到**（如实告知，不粉饰）

### 第 7 步（可选）：发送 —— 只在用户明确要求时做
规则与操作见 `references/sending.md`。**默认永远是 dry-run**，本 skill 从不自动发送。

```bash
# 预览（不连服务器）
python scripts/send_emails.py --json output/outreach/<批次>.json \
    --provider gmail --from-name "名字" --from-email you@gmail.com
# 真发需同时给 --send --yes，并已配好 SMTP 凭据（环境变量 SMTP_PASS 或 .secrets/send-config.json）
```

发送器会自动：跳过 `recommended=false`、跳过无邮箱记录、发送前重跑硬门、限速、写日志（不含密码）。
**发送前必须向用户确认三件事**：用哪个邮箱（**强烈建议独立域名而非个人 Gmail/QQ**）、发多少封、退订说明文案。

## 能力边界（必须如实告知）

| 平台 | 能拿到 | 拿不到 |
|---|---|---|
| **YouTube** | 频道名、简介、订阅数、部分视频列表（频道页 `/@handle` 经 WebFetch；撞同意墙时用 `r.jina.ai` 阅读代理） | 完整视频列表、精确平均播放量、受众画像 |
| **Instagram** | 帖子 caption 全文 + hashtags（`pixnoy.com/profile/<handle>/`，原 pixwox）、帖子链接 + 相对日期 + 点赞评论（`imginn.com/<handle>/`）、bio、粉丝数（部分账号） | 绝对日期、受众画像；直连 IG / r.jina.ai+IG / dumpor 全部不可用 |
| **Facebook** | 页面名、粉丝数、分类、简介、**公开邮箱**、外链、**最新 1 条帖** | 第 2 条起的帖子（登录墙硬截断）、绝对日期 |

- **调研只能走 agent 联网**：本机 Bash 出网是白名单制（只有 hokolite.com / github.com 放行），且 IG/FB 站点本身有 Cloudflare 反爬 → **脚本抓不了，别写脚本**。
- **IG/FB 头号陷阱：handle ≠ 同一人**（实测 `@bunnyandbeyond` 在 YT 是 vanlife、在 IG 是插画师）。每个 handle 必须先做人号一致性校验。
- **FB 只有 1 条最新帖**，且常与产品无关 → FB 更适合当「联系方式补充 + 人号交叉验证」，内容调研以 YT/IG 为主。
- **受众画像是官方 API 都拿不到的**，第三方全是估算——涉及受众匹配必须标注「估算」。

## 合规与红线

1. **不编造**（最高优先级）：不虚构视频标题、播放量、互动数据、合作历史。证据不足就降级或打占位符。
2. **不承诺**：邮件里不得出现免费样品、付费、佣金、保证效果等承诺。
3. **不自动发送**：本 skill 默认只产出草稿（`DRAFT — NOT SENT`）。发送是独立的第 7 步，必须用户明确要求 + 显式 `--send --yes`，并保留退订机制。**永远不要用 GUI/浏览器操控去点「发送」**（见 `references/sending.md`）。
4. **只做单个/单批链接**，不做 KOL 名单发现（用 `kol-discovery-youtube`）。

## 打包 / 移植给别人（Packaging & portability）

本 skill 可以直接打包分享，但**别人拿到后必须自己配 SMTP** —— 你的凭据不在 skill 目录里。分享前按此清单清理：

| 要改什么 | 在哪 | 为什么 |
|---|---|---|
| **SMTP 凭据** | 不在 skill 内（在 `.secrets/send-config.json`） | 别人拿不到你的密码，需自建 `.secrets/send-config.json` 或设环境变量 `SMTP_PASS` |
| **工作目录** | 脚本自动探测项目根，或用环境变量 `KOL_WORKSPACE` 覆盖 | **无需手动改路径** |
| **品牌** | 全文的 `HOKOLITE` | 换成对方品牌 |
| **产品库** | `products/catalog.json`（HOKOLITE 专属，67 个产品） | 换对方产品库；用 `build_catalog.py --shopify <对方站点>/products.json` 重建 |
| **品牌事实** | `products/brand-facts.md` | 署名 / 口吻 / 禁用声明换成对方的 |

**绝对不要打进包里的东西**：
- `.secrets/`（含 SMTP 密码）
- `output/outreach/*.json` 与 `send-log.jsonl`（含**达人真实资料 + 收发件地址**）
- `.workbuddy-ai/memory/`（工作记录）

**打包范围**：只打 `skills/kol-personalized-outreach/` 这一个目录；若连产品库一起给，另附 `products/catalog.json` + `products/brand-facts.md`。

### 跨宿主兼容（Agent Skills 开放标准）

本 skill 遵循 [Agent Skills](https://agentskills.io) 开放标准（`SKILL.md` + YAML frontmatter），可在 Codex / Claude Code 等 70+ 个 SKILL.md 宿主运行：

| 宿主 | 安装方式 |
|---|---|
| **Codex / 其他宿主** | `npx skills add <本目录或仓库> -a codex` → 落到 `.agents/skills/` |
| **WorkBuddy** | 放进 `<项目>/.workbuddy-ai/skills/` |

宿主差异已用「兼容写法」抹平，无需改文件：

- **文件交付**：宿主支持预览工具时（WorkBuddy 的 `present_files`）直接调用；否则把文件路径告知用户。
- **联网调研**：用宿主自带的联网工具（WebFetch / WebSearch 或等价物）。
- **路径**：一律相对 skill 目录或项目根，**不含任何绝对路径**。

## 参考文件

- `references/output-schema.md` — **输出契约（JSON schema，本 skill 的交付标准）**
- `references/platform-adapters.md` — 各平台能拿到什么 + 抓取清单 + 实测通道
- `references/creator-research-spec.md` — 达人调研字段表
- `references/product-catalog-schema.md` — 产品库字段定义
- `references/product-matching.md` — 匹配打分规则 + 建联资格门槛
- `references/email-spec.md` — **邮件规格（核心）**
- `references/email-examples.md` — 完整邮件示例 + 逐条映射
- `references/qa-checklist.md` — 质量自检门清单
- `references/sending.md` — **发送环节（第 7 步）：SMTP 配置 + 送达率/封号风险 + 合规**
