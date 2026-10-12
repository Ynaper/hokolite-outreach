# 平台适配器 · Platform Adapters

每个平台一个 adapter，**统一输出同一个规范化对象 `creator-signal`**，供匹配层与邮件层消费。
新增平台只需在此补一节；匹配层与邮件层零改动。

> 前提：本机 Bash 出网是白名单制（只有 hokolite.com / github.com 放行）。
> 抓达人内容**必须走 agent 的联网工具**（WebFetch / WebSearch），不要用 Bash 里的 curl。

---

## 通用抓取顺序

1. **oEmbed**（如该平台支持）→ 拿标题、作者名、页面链接（最省、最稳）
2. **第三方统计站** → 拿订阅/播放/视频数/简介/近期视频（标注为 `Estimated`）
3. **搜索引擎** → 补新闻、背景、bio、帖子标题快照
4. 交叉验证：同一字段多源不一致时，并列记录各自证据，不平均、不按新旧强选

---

## YouTube（v1 已实现）

### 可用端点

| 通道 | 用法 | 产出 | 证据标签 |
|---|---|---|---|
| oEmbed | `https://www.youtube.com/oembed?url=<视频URL>&format=json` | 视频标题、作者名(author_name)、作者链接(author_url) | Measured |
| 频道 RSS | `https://www.youtube.com/feeds/videos.xml?channel_id=UC...`（需先拿到 UC id） | 最新 ~15 条视频标题/发布时间 | Measured |
| 第三方统计站 | AskNaveen / ViewStats / ThoughtLeaders / SocialBlade 等公开页 | 订阅数、总播放、视频数、创建日期、简介、部分近期视频 | Estimated |
| 搜索引擎 | `<频道名> review Olight` / `<频道名> flashlight` 等 | 历史测评品牌、新闻、背景 | Proxy |

### 已知限制（实测）
- 视频页 `/watch` 返回空（JS 渲染）。
- **频道页 `/@handle` 经 WebFetch 实测可抓**（2026-10-12 成功，未被 cookie 墙拦截）→ 能拿到：频道简介原文、订阅数、视频数、**部分视频列表（标题/播放/时间）**。这是 v1 最有价值的通道，优先试它。
- **同意墙（consent wall）**：`www.youtube.com/@handle` 与 `m.youtube.com/@handle` 会**间歇性**返回 "Before you continue to YouTube" 同意墙。**最可靠的绕过通道是阅读代理**：
  `https://r.jina.ai/https://www.youtube.com/@handle/videos`
  → 返回完整视频列表（标题 + 播放量 + 发布时间），偶带 `Warning: 401`（可忽略）。抓取优先级：**r.jina.ai 阅读代理 > m.youtube.com > www.youtube.com**。
- 官方 RSS `feeds/videos.xml?channel_id=` 在 Bash/curl 与 WebFetch 均返回 404（2026-10-12 实测），**不要依赖**。
- **拿不到**：完整近期视频列表（长频道通常只见约 30 条）、精确平均播放量、受众画像、邮箱。

### 输出映射
- `display_name` ← oEmbed `author_name`
- `profile_url` ← oEmbed `author_url`
- `recent_items[]` ← RSS + 第三方站 + 搜索（每条带 url + date + source_ref）
- `brand_hits[]` ← 标题/描述里扫竞品词（Olight/NEBO/Fenix/Nitecore/Sofirn/…）
- `engagement_signal` ← 第三方站，标 `Estimated`

---

## Instagram（v1 已实测，可用）

### 可用端点（2026-10-12 实测）

| 通道 | 用法 | 产出 | 证据标签 |
|---|---|---|---|
| **imginn** | `https://imginn.com/<handle>/` | 帖子**永久链接**（`imginn.com/p/<shortcode>/`，可换算 `instagram.com/p/<shortcode>/`）、**相对日期**（"4 months ago"）、**点赞/评论数**、部分账号的粉丝数+bio | Measured |
| **pixnoy**（原 pixwox，已改名） | `https://pixnoy.com/profile/<handle>/` | **帖子 caption 全文** + hashtags（imginn 不给正文，必须靠它） | Measured |
| 第三方统计站 | SocialBlade / HypeAuditor 公开页 | 粉丝数/互动率估算 | Estimated |

**两个源互补**：imginn 给「链接+日期+互动数」，pixnoy 给「caption 全文」。要拼出可引用的一条帖子，两个都要抓。

### 不可用（实测，别浪费时间）
- **直连 `instagram.com/<handle>/`** → 登录墙（只返回 "Sign up / Log in"）。
- **`r.jina.ai` + instagram.com** → 同样返回登录页（r.jina.ai 对 IG 无效，别套用 YouTube 那招）。
- **`dumpor.com/v/<handle>`** → 反爬 "Verifying…"。
- **`instanavigation.com`** → fetch failed。
- `picuki.com` → 已重定向到 TikTok 站（tikvib），无用。
- **Bash/脚本直连**（`scripts/` 里用 urllib/requests 抓）→ **不可行**。实测：`imginn.com` 返回 403（Cloudflare 挡非浏览器 TLS 指纹，加全套浏览器头也无效）；`pixnoy.com` / `instagram.com` 返回 502（本机代理白名单不放行）。
  → **结论：IG 调研只能走 agent 的 WebFetch 通道**（它走独立网络通道，能过反爬与白名单）。脚本只负责下游拼装与校验，**不要试图写 IG 抓取脚本**。

### 覆盖率不是 100%（实测）
- `pixnoy` 有账号未收录：`@lukepearsallphoto`、`@instafr4nk` 只返回页首、无帖子正文。
- `imginn` 有账号未收录：`@vanlifesagas` 返回 "Page Not Found"。
→ **单个数据源失败不等于达人不活跃**，换另一个源或换通道再试；两个源都空才判「无公开数据」。

### 能力边界（实测）
- ✅ bio、粉丝数（**仅部分账号** imginn 返回；kristiroams/vanlifesagas 均未返回 → 需 `data_gap` 标注）
- ✅ 帖子 caption 全文、hashtags、帖子短码、相对日期、点赞/评论数
- ❌ **绝对日期**（imginn 只给 "N months ago" 相对时间，需自行换算并标 `Calculated`）
- ❌ 受众画像、邮箱
- ⚠️ **缓存滞后**：imginn/pixnoy 的"最新帖"可能是数周~数月前（实测 kristiroams IG 最新帖约 4 个月前）。**IG 活跃度低的达人，其 IG 不能代表当前状态**，务必标注。

### ⚠️ 头号陷阱：YouTube handle ≠ IG handle
**同名不等于同人。** 实测 `@bunnyandbeyond` 在 YouTube 是 vanlife 频道，在 IG 是 296 粉丝的插画师，完全无关。
→ **每个 handle 必须先做人号一致性校验**：比对 bio（是否互相导流，如 IG bio 写 "Endurance Room on YouTube"）、内容主题、粉丝量级。**对不上就不认，宁缺勿错。**

### 输出映射
- `display_name` ← pixnoy/imginn 页首
- `recent_items[]` ← imginn（url/date/互动）+ pixnoy（caption 正文）按顺序对齐
- `brand_hits[]` ← caption 里扫竞品词
- `data_gaps` 里**必须**列出「绝对日期 / 粉丝数（若未返回）/ 完整帖子列表 / 受众画像 / 邮箱 未获取」

---

## Facebook（v1 已实测，可用）

### 可用端点（2026-10-12 实测）

| 通道 | 用法 | 产出 | 证据标签 |
|---|---|---|---|
| **直连 WebFetch** | `https://www.facebook.com/<page>` | 页面名、粉丝数/关注数、分类、**简介 Intro**、**公开邮箱**、外链、**最新 1 条帖**（文案+相对时间+互动数）、有时可见评论 | Measured |

**唯一可用通道就是直连 WebFetch**。实测成功率约 4/6（@homemadewanderlust / @darwinonthetrail / @danbeckeroutdoors / 品牌页 olightworld 成功；@justinoutdoors 内容未渲染；@kraigadams 撞登录墙）。

### 不可用（实测）
- **`r.jina.ai` + facebook** → 只返回登录页（与 IG 一样无效）。
- **`facebook.com/<page>/posts`** → 仍只放行 1 条帖（登录墙截断）。
- 无第三方 FB 镜像站可用（IG 有 imginn/pixnoy，FB 没有对等物）。

### 能力边界（实测）
- ✅ 页面名、粉丝数、分类（`Page · Public figure` / `Digital creator` / `Interest`）、简介、外链
- ✅ **公开联系邮箱**（比例明显高于 IG —— 常直接挂在 Intro/About 区）
- ✅ **最新 1 条帖**的文案 + 相对时间 + 互动数；**有时能看到评论**
- ❌ **第 2 条及以后的帖子**（登录墙硬截断）
- ❌ 绝对日期（只有 "N hours ago"）、完整正文（常被 "See more" 折叠）、About 详细页

### ⚠️ 定位结论：FB 是「联系方式渠道」，不是「内容调研渠道」
- **强项**：公开邮箱。实测 3 个达人页里 1 个直接给了邮箱（`danbeckeroutdoors@gmail.com`），品牌页也有（`cs.us@olight.com`）。
- **弱项**：内容素材只有最新 1 条帖，**且经常与产品无关**（实测：Homemade Wanderlust 的最新帖是 PCT 徒步者失踪纪念、Dan Becker 是幸存者访谈）。
- **建议**：FB 用于「补充联系方式 + 人号交叉验证」；内容调研仍以 YouTube / Instagram 为主。

### ⚠️ 内容合规判断：最新帖可能「有内容但不能用」
FB 只给 1 条帖，而这条帖可能**题材敏感**（如失踪纪念、事故报道）。**此时必须主动放弃引用，降级到简介/频道定位**，绝不为了「有 hook」而消费悲伤事件。这是判断，不是能力问题。

### 输出映射
- `display_name` ← 页首
- `bio` ← Intro 区原文
- `recent_items[]` ← **仅 1 条**（最新帖）
- `data_gaps` 里**必须**列出「第 2 条起的帖子 / 绝对日期 / 完整正文 未获取」

---

## TikTok（v4，占位）

Research API 仅限学术非商业（项目 memory 2026-10-11 已核实），商业用途不可用。
计划：搜索引擎快照 + 第三方估算；待定。

---

## 统一输出：`creator-signal`

**最终交付物是 JSON**（唯一契约），schema 见 `output-schema.md`。下方 YAML 是调研层的**中间信号结构**（agent 在写邮件前先在脑内组织成这个形状），最终按 `output-schema.md` 落成 `records[]`：

```yaml
platform: youtube            # youtube | instagram | facebook | tiktok
handle: "@example"
display_name: "Example Channel"
profile_url: "https://..."
niche: [edc, outdoor]                 # agent 判断，2-4 个
audience: [edc_enthusiast, camper]    # agent 判断
bio_excerpt: "..."
recent_items:                         # 最多 5-10 条，按可引用性排序
  - title: "..."
    url: "https://..."
    date: "2026-08-12"
    type: review|unboxing|field_test|tutorial|other
    topic: "..."
    why_relevant: "..."
    source_ref: "oembed:..."
    observed_at: "2026-10-12"
brand_hits: [Olight, NEBO]
engagement_signal:
  subs: 125000
  avg_views: 18000
  note: "subs/views from SocialBlade, Estimated"
  label: Estimated
content_format: review
best_citation:
  item: "Baton 4 Pro teardown"
  reason: "唯一实测 pocket-clip 磨损的测评，细节罕见"
data_gaps:
  - "完整近期视频列表未获取"
  - "邮箱未获取（由第三方 ERP 提供）"
evidence:
  - {field: display_name, provider: youtube-oembed, source_ref: "...", observed_at: "2026-10-12", label: Measured}
```

**证据标签**：`Measured`（实测）/ `Estimated`（第三方估算）/ `Calculated`（推导）/ `User-provided` / `Proxy`（间接）。
