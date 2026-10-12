# 输出契约 · Output Schema

本 skill 的**唯一交付物**是一份 JSON 文件。三平台（YouTube / Instagram / Facebook）输出**同一个 schema**，下游处理无需区分平台。

**文件位置**：`output/outreach\<批次名>.json`

---

## 顶层结构

```json
{
  "meta": { ... },
  "records": [ { ... }, { ... } ]
}
```

单条链接也走同一结构（`records` 长度为 1）。

---

## `meta`

| 字段 | 说明 |
|---|---|
| `generated_at` | 生成日期 `YYYY-MM-DD` |
| `platform` | 若本批次单一平台则填；混合批次可省略（记录级有） |
| `brand` | 固定 `HOKOLITE` |
| `product_catalog` | 产品库路径 |
| `skill` | 固定 `kol-personalized-outreach` |
| `status` | 固定 `DRAFT — NOT SENT（仅测试，未发送、也不会发送）` |
| `method` | 调研/匹配/邮件/校验各步用的通道与规则 |
| `platform_findings` | （可选）本批次的平台能力边界发现 |

## `records[]`（每条 = 一位达人）

### 1. 身份与来源

| 字段 | 必填 | 说明 |
|---|---|---|
| `platform` | ✅ | `youtube` / `instagram` / `facebook` |
| `id` | ✅ | 如 `yt-mrbazreviews`、`ig-gtdunn`、`fb-danbeckeroutdoors` |
| `handle` | ✅ | 如 `@mrbazreviews` |
| `creator_name` | ✅ | 真实姓名或频道名（邮件里必须用到的那个） |
| `profile_url` | ✅ | 用户给的原始链接 |
| `followers` | ⬜ | 数字；拿不到填 `null` |
| `followers_note` | ⬜ | 粉丝数来源/估算标签/为何缺失 |
| `bio` | ⬜ | 频道简介原文 |
| `page_type` | ⬜ | FB 专用：`Page · Public figure` 等 |
| `email` | ⬜ | **若公开渠道拿到才填**；否则 `null` |
| `email_source` | ⬜ | 邮箱从哪来（渠道 + 是否已核验） |

### 2. 校验（两道，都必须有）

| 字段 | 说明 |
|---|---|
| `identity_check` | `{verdict: 通过/不通过, method: 依据}` —— 防同名不同人（IG/FB 高危） |
| `activity_check` | `{verdict: 活跃/不活跃, note: 依据}` —— 最新内容距今多久 |

### 3. 内容分析

| 字段 | 说明 |
|---|---|
| `channel_type` | 频道定位 |
| `audience_analysis` | 受众分析（估算须标注） |
| `competitor_brands` | 历史测评/提及的竞品品牌数组 |
| `competitor_note` | 竞品桥接判断说明 |
| `relevant_posts` | 数组，每条：`{title, url, date, type, why_relevant, source_ref, observed_at, label}` |

### 4. 匹配结果

| 字段 | 说明 |
|---|---|
| `recommended_product` | `{id, name, price_usd}`；不匹配时 `null` |
| `match_score` | 0–100 |
| `match_reason` | 逐维度说明（品类/场景/受众/竞品/形态） |
| `recommended` | `true/false`（= 匹配分 ≥30 **且** 活跃 **且** 量级达标） |

### 5. 邮件（本 skill 的核心）

| 字段 | 说明 |
|---|---|
| `email_subject_primary` | 主题行（主） |
| `email_subject_alternatives` | 主题行备选（2 条） |
| `email_body` | 正文，100–160 英文单词，5 move |
| `email_word_count` | 词数（脚本回填） |
| `email_rationale_zh` | **中文说明：为什么这样写**（逐条对应达人信号） |

`recommended=false` 时：上述邮件字段全部为 `null` / 空数组，并在 `match_reason` 里写明不推荐理由。

### 6. 诚实标注

| 字段 | 说明 |
|---|---|
| `data_gaps` | 数组：本记录哪些字段没拿到、为什么 |

---

## 硬性要求

1. **每条事实都要有 `source_ref` + `observed_at`**，拿不到就标 `data_gap`，**绝不编造**。
2. `email_body` 必须过 `check_email.py` 硬门（字数/禁用词/首词/链接/必备 token）。
3. `recommended=false` 的记录**也要输出**（含匹配分与不推荐理由）——这本身是有价值的结论。
4. 平台特有的缺失字段（如 FB 只有 1 条帖）在 `data_gaps` 里**必须**如实列出。
