# 邮件规格 · Email Spec【核心】

冷启动开发邮件（first-touch）的可执行规格。**主题行和正文都按每位达人独立生成，不是替换姓名的模板。**

> **重要冲突说明**：aaron 库 `cold-copy-rules.md` 规定「首触最多 3 句」。
> 本规格**以用户要求为准：正文 100–160 英文单词**（约 6–8 句），**放弃 3 句硬上限**。
> 只吸收 cold-copy 的**精神**：禁 I/We 开头、首触无链接、软 CTA、不编造经历、证据支撑个性化。

---

## 1. 结构模板（5 个 move，总 100–160 词）

| Move | 作用 | 词数预算 | 硬规则 |
|---|---|---|---|
| **M1 Hook** | 引用达人**一条真实内容** + 为什么关注 | 20–35 | 以「姓名/频道名 + 具体内容」开头；**首词禁止 I / We / Our** |
| **M2 Bridge** | 把该内容接到产品品类；测过竞品则点名桥接 | 15–25 | 不得编造「我看了你很久」这类经历 |
| **M3 Product** | 引出 HOKOLITE 对应产品 + **1–2 个卖点**（场景化，不堆参数） | 25–40 | 卖点必须来自 `catalog.selling_points` |
| **M4 Value** | 从**达人 + 粉丝**角度讲合作价值（场景 + 观众能得到什么好内容） | 20–35 | 不得承诺任何回报 |
| **M5 CTA** | 软邀请 | 8–15 | 只用软 CTA；首触不放链接 |

**主题行**：1 主用 + 2 备选（A/B）。≤ ~50 字符；必含达人真实内容或姓名钩子；无全大写、无 `!!!`、无假 `RE:/FWD:`。

---

## 2. 对应用户 6 条要求（必须逐条满足）

| 编号 | 要求 | 落在哪个 move |
|---|---|---|
| **R1** | 用达人真实姓名或频道名称呼 | M1 开头 |
| **R2** | 开头结合真实内容，提及某条具体视频/测评/帖子（如曾测 Olight、NEBO），说明为什么关注 | M1 |
| **R3** | 自然引出 HOKOLITE 对应产品，介绍 1–2 个核心卖点，**不堆参数** | M2→M3 |
| **R4** | 从达人和粉丝角度解释合作价值（使用场景 + 观众能获得什么有价值的测评内容） | M4 |
| **R5** | 自然提出合作邀请（是否愿意了解产品/接收资料/讨论测评合作） | M5 |
| **R6** | 地道、美式、自然、友好的商务英语；无 AI 模板感、无过度推销 | 全篇 |

**红线（G 系列）**
- **G1** 不得擅自承诺免费样品、付费合作、佣金。
- **G2** 正文 100–160 英文单词。
- **G3** 首触无任何链接。
- **G4** 正文首词非 I / We / Our。
- **G5** 引用内容可回指 dossier 证据（不得编造）。

---

## 3. 禁用词清单

### 开头禁用（正文第一个词/首句）
`I` · `We` · `Our team` · `Our brand` · `I wanted to` · `I'm reaching out` · `Hope this finds you well` · `My name is`

### AI 模板味
`I came across your profile` · `impressed by your content` · `perfect fit` · `authentic style` · `this will resonate` · `your inbox must be busy` · `as a passionate` · `leverage` · `synergy` · `game-changer` · `revolutionary` · `cutting-edge` · `elevate` · `unleash` · `seamless` · `dive into` · `in today's landscape` · `we're excited to`

### 过度推销 / 承诺（绝对禁止）
`free sample` · `we'll pay` · `commission` · `sponsorship fee` · `guaranteed` · `100%` · `risk-free` · `limited time` · `act now` · `don't miss`

### 硬 CTA（首触禁用）
`book a call` · `are you free` · `let's hop on a call` · `schedule a meeting`

### 参数堆砌
禁止连续出现 ≥3 个数字/单位（如 "1000lm, 4000mAh, 8 hours"）。

---

## 4. CTA 规范

**只用软 CTA**（低承诺，问意愿，不要时间）：
- `Open to taking a look?`
- `Want the details?`
- `Is this the kind of product you'd test?`
- `Happy to send more if it's useful.`

**禁止**：预约电话、要具体时间、任何形式的承诺。

---

## 5. Tone 规范

- **peer-to-peer**（同行口吻），不是 brand-to-creator。
- curious, not desperate；specific, not generic；short, not comprehensive。
- 美式拼写；允许缩写（you've / it's）；**不用 emoji**；不堆感叹号。
- 读起来像「懂行的人写的一张便条」，不像营销文案。
- 第一人称可用，但**不能是首词**，且要克制（一封里 I/We 出现 ≤2 次为佳）。

---

## 6. 署名

从 `products/brand-facts.md` 取姓名/职位。**未提供时用占位符**：

```
Best,
[YOUR NAME]
[TITLE], HOKOLITE
```

---

## 7. 事实降级规则（防编造）

拿不到具体视频/帖子标题时（IG 常见），opener **不得虚构**：
1. 用**可验证的频道定位**开头（"Your channel has become the go-to for real-world EDC light testing…"）；
2. 仍不确定 → 用占位符 `[reference their recent Olight/NEBO video here]`，并标 `DRAFT — NEEDS CITATION`；
3. **绝不**编造视频标题、播放量、互动数据、合作历史。

---

## 8. 交付格式：`email.md`

```markdown
# Outreach Email — <频道名>

> **DRAFT — NOT SENT**
> 达人：<姓名 / 频道名>
> 主推产品：<产品名>
> 生成时间：<YYYY-MM-DD>

## Subject (primary)
<主题行>

## Subject (alternatives)
1. <备选 1>
2. <备选 2>

## Body
<正文，100–160 词>

## Signature
Best,
[YOUR NAME]
[TITLE], HOKOLITE

---

## 引用依据（自检用，不发送）
- R2 引用来源：<dossier 里的 source_ref + observed_at>
- 采用的产品卖点：<catalog selling_points 编号>
```

完整示例见 `email-examples.md`。
