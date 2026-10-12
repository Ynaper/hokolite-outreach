# 达人调研规格 · Creator Research Spec

单人深挖用的字段表。**每条事实都要带来源与观察日期；拿不到的如实标 `unconfirmed`，不猜。**

> 说明：本规格基于 aaron 库的 `creator-dossier.md`，但**去掉了 PII 伪名化机制**——
> 本项目要求邮件里使用达人**真实姓名/频道名**，且联系方式由第三方 ERP 提供，不在此处抓取。

---

## 字段表

| 字段 | 填什么 | 来源 | 证据标签 |
|---|---|---|---|
| **平台** | youtube / instagram / facebook / tiktok | 输入链接 | Measured |
| **handle / 频道名 / 真实姓名** | 用于邮件称呼 | oEmbed / 第三方站 / 搜索 | Measured |
| **频道链接** | 主页 URL | oEmbed | Measured |
| **频道定位** | 一句话品类 + 2-3 个常做主题 | 近期内容样本 | Proxy |
| **受众信号** | 订阅数 / 可见互动 / 评论区是谁 | 第三方站 + 评论样本 | Estimated |
| **近期内容** | 5-10 条，含标题/链接/日期/类型/主题 | RSS + 第三方 + 搜索 | Measured/Estimated |
| **爆款/异常值** | 1-3 条超过其自身基线的视频 | 内容样本对比 | Calculated |
| **更新节奏** | 大致频率 + 最近活跃日期 | 内容样本 | Proxy |
| **历史测评品牌** | Olight/NEBO/Fenix/Nitecore/Sofirn 等命中 | 标题/描述/搜索 | Proxy |
| **品牌安全旗标** | 争议、离题内容、合作披露信号 | 内容样本 | Proxy |
| **内容形态** | review / unboxing / field_test / tutorial | 内容样本 | Proxy |
| **最佳引用素材** | 邮件开头要用那一条 + 为什么 | 内容样本 | Measured |
| **数据缺口** | 明确列出没拿到的字段 | — | — |
| **置信度** | High / Medium / Low（整体） | 上表证据行 | Calculated |

---

## 怎么读每个字段

- **受众信号，不看虚荣数字**：订阅数本身意义有限。抽几条近期内容，看评论像不像真人在讨论，还是表情刷屏/互赞群。
- **异常值告诉你什么有效**：一条超过**该达人自己基线**的视频，说明其受众奖励什么题材/形式——这是后面写邮件卖点的依据。只跟该达人自己比，不跟别的达人比。
- **品牌安全是证据，不是判决**：只记录带日期的观察。
- **历史测评品牌 = 最强的邮件桥接点**：达人测过 Olight/NEBO，邮件就能自然地说「你测过 X，HOKOLITE 是同类可对比」。

---

## 事实降级（拿不到具体内容标题时）

1. 用**可验证的频道定位**开头（如 "Your channel has become the go-to for real-world EDC light testing…"）；
2. 仍不确定 → 用占位符 `[reference their recent Olight/NEBO video here]`，并标 `DRAFT — NEEDS CITATION`；
3. **绝不**编造视频标题、播放量、互动数据。

---

## 产出格式：写进批次 JSON 的 `records[]`

**本 skill 的唯一交付物是 JSON**（schema 见 `output-schema.md`），**不再单独产出 `.md` 画像文件**。
下面这套调研字段按 `output-schema.md` 落位：

| 调研字段 | 落到 JSON 的字段 |
|---|---|
| 平台 / handle / 频道名 / 链接 | `platform` / `handle` / `creator_name` / `profile_url` |
| 频道定位 / 受众信号 | `channel_type` / `audience_analysis`（估算须标注） |
| 近期内容 / 爆款 / 最佳引用素材 | `relevant_posts[]`（每条含 `title/url/date/type/why_relevant/source_ref/observed_at/label`） |
| 历史测评品牌 | `competitor_brands[]` + `competitor_note` |
| 更新节奏 | `activity_check` |
| 人号一致性 | `identity_check` |
| 数据缺口 | `data_gaps[]` |
| 置信度 | 体现在每条事实的 `label`（Measured / Estimated / Calculated / Proxy） |

> **术语**：下文提到的 **dossier（画像）** = 一位达人在批次 JSON 里的那条 `record`，是内部叫法，**不单独成文件**。

历史样例（**旧格式，仅供参照字段覆盖度，勿再产出 `.md`**）：
`output/creator-olight-world.md`、`output/creator-two-minute-papers.md`
