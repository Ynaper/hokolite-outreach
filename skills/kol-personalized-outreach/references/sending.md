# 发送环节 · Sending

> 本文件回答一个问题：**JSON 里的邮件草稿，怎么真的发出去。**
> 结论先给：**用 SMTP（脚本），不要用 API，更不要让我去操控你的电脑点鼠标。**

---

## 三条路对比

| 方案 | 怎么做 | 优点 | 缺点 | 建议 |
|---|---|---|---|---|
| **A. SMTP 脚本** | `send_emails.py` 读 JSON，用 Gmail/QQ 的 SMTP 发 | 简单、可批量、可限速、有日志、可 dry-run | 需开 App Password/授权码 | ✅ **推荐** |
| **B. Gmail API（OAuth2）** | 建 GCP 项目 + OAuth 授权，调 `messages.send` | 官方、无需密码 | 配置更重；送达率与 A **完全一样** | 没必要，除非要用 Workspace 审计 |
| **C. 操控电脑（GUI/浏览器）** | 我开浏览器登录网页邮箱，逐封点「发送」 | 无需配 SMTP | 脆、慢、无法审计、易点错、撞验证码/二次验证 | ❌ **不要** |

**为什么不选 C**：网页邮箱是给人点着玩的，不是给程序发信的口子。批量发时它会弹验证码、二次验证、异常登录拦截；我一「点错」就是发给错的人，且没有可靠日志可查。SMTP 是设计给程序用的正规通道，同一个 Gmail 账户，A 比 C 稳得多、快得多、也安全得多。

**为什么不选 B**：Gmail API 唯一的优势是「不用存密码」，但代价是建 GCP 项目 + OAuth 同意屏 + token 刷新。对「一批几十封、跑脚本发」这个场景，SMTP 的投入产出比更高。**两者送达率没有任何区别** —— 垃圾箱还是垃圾箱。

---

## 怎么开（一次性配置）

### Gmail

1. 开启**两步验证**（Google 账户 → 安全性）。
2. 生成 **App Password**：Google 账户 → 安全性 → 应用专用密码 → 选「邮件 / Windows 计算机」→ 得到 16 位密码。
3. 用这 16 位当密码（**不是你的 Gmail 登录密码**）。
   - host `smtp.gmail.com`，port `465`（SSL）。
   - 发信上限：个人 Gmail 约 **500 封/天**，Workspace 2000。

### QQ 邮箱

1. 网页版 → 设置 → 账户 → 开启 **SMTP 服务**。
2. 按提示生成 **授权码**（16 位）。
3. 用授权码当密码（**不是 QQ 密码**）。
   - host `smtp.qq.com`，port `465`（SSL）。

### 凭据放哪

**绝不写进代码，也绝不进 git。**

- 首选环境变量：`set SMTP_PASS=xxxx`（每次开新终端设一次）。
- 或本地配置文件 `.secrets/send-config.json`（项目根下的 `.secrets/`）；**模板见 `references/send-config.example.json`（与本文件同目录）**，复制过去填入真实值即可。
- `.secrets/` 目录应加入 `.gitignore`。

---

## ⚠️ 最重要的一件事：别用个人 Gmail / QQ 发开发信

这一节比上面所有配置都重要。

**个人 Gmail 和 QQ 邮箱，都不是给「陌生开发信」用的。** 用它们群发 cold outreach，会同时踩两个坑：

1. **送达率**：陌生域名/陌生地址 + 批量 + 无退订历史 → 大概率进**垃圾箱**，甚至直接被拒收。
2. **账户安全**：短时间内向大量陌生地址发相似内容，是垃圾邮件发送者的典型特征 → Gmail 可能**临时封禁发信**，QQ 更严。**这是你的主力邮箱，别拿它冒险。**

**QQ 邮箱尤其不适合**：向欧美 B2B 收件人发信时，「QQ 域名 + 中国 IP」在国际反垃圾体系里天然吃亏，进垃圾箱概率更高。

### 建议的正规做法（如果这是要长期跑的生意）

1. **用独立发送域名**（如 `outreach@hokolite.com` 或单独注册一个域名），不要用个人邮箱。
2. 配好 **SPF + DKIM + DMARC** 三条 DNS 记录 —— 这是进收件箱的前提。
3. **域名预热**：新域名从每天 5–10 封起步，逐步加量，别一上来就群发。
4. **小批量 + 高个性化**：本 skill 的邮件本来就是一人一稿，这正是优势；每天控制在几十封，别一天几百。
5. **纯文本、无追踪像素、带退订说明**。
6. 真要上量，用专业服务（Resend / Amazon SES / SendGrid），它们帮你做域名信誉。

**如果只是想拿个人 Gmail 试发几封验证效果**：可以，但务必 `--limit` 压到 3–5 封，`--delay` 拉到 60 秒以上，且内容保持一人一稿。

---

## 合规（别跳过）

- **CAN-SPAM（美国）/ GDPR（欧盟）**：商业邮件必须有**真实发件人身份**和**可用的退订方式**。
- 所以：`brand-facts.md` 的署名要填真名真职位（现在是 `[YOUR NAME]` 占位）；发送时建议加 `--unsubscribe` 一行退订说明。
- 收到退订/拒绝，立即加入黑名单，不再联系。

---

## 发送流程（本 skill 的第 7 步）

```bash
# 0) 先确保邮件已过硬门（第 5 步）
python check_email.py --json output/outreach\<批次>.json

# 1) 预览：不连服务器，只看「谁收、什么主题」
python send_emails.py --json output/outreach\<批次>.json \
    --provider gmail --from-name "你的名字" --from-email you@gmail.com

# 2) 真发（小批量试水）
set SMTP_PASS=<App Password 或授权码>
python send_emails.py --json output/outreach\<批次>.json \
    --provider gmail --from-name "你的名字" --from-email you@gmail.com \
    --unsubscribe "Not interested? Just reply STOP and I won't follow up." \
    --limit 5 --delay 60 --send --yes
```

**发送器自动做的事**：
- 跳过 `recommended=false` 的记录（未达建联门槛）。
- 跳过没有邮箱的记录（邮箱由第三方 ERP 提供）。
- 发送前重跑硬门，不过门的不发。
- 每条之间限速；单条失败不中断整批。
- 写 `output/outreach/send-log.jsonl`（谁、何时、成功/失败，**不含密码**）。

---

## 现状（2026-10-12 更新）

- `send_emails.py` 已就绪并**已实测跑通**：2026-10-12 经 Gmail SMTP 成功投递自测信，日志见 `output/outreach/send-log.jsonl`（⚠️ 日志含收件地址，**分享前请清理**）。
- 凭据已配：`.secrets/send-config.json`（provider=gmail）。该文件已被 `.gitignore` 忽略，**绝不进 git**。
- `brand-facts.md` 署名仍是 `[YOUR NAME]` 占位，发件显示名现为占位 `Jiang` → **正式发给达人前必须替换**。
- **默认仍是 dry-run**，需 `--send --yes` 才真发。

## 实测记录与排障

| 症状 | 原因 | 处理 |
|---|---|---|
| 登录失败 | 用了登录密码而非 App Password / 授权码 | Gmail 用 16 位 App Password；QQ 用授权码 |
| 登录失败 | App Password 带空格直接传 | 发送器已自动去空格；手写脚本需 `password.replace(" ","")` |
| 认证失败 | App Password 与 `smtp_user` 不属于同一账号 | 二者必须同属一个 Google 账号 |
| `535 BadCredentials` | App Password 已撤销 / 复制不全 | 到 Google 账号重新生成 |
| 发出去但进垃圾箱 | 个人邮箱直发陌生地址（非技术故障） | 见上「别用个人 Gmail / QQ 发开发信」，转独立域名 |

**可复用的成功命令**：

```bash
python scripts/send_emails.py \
    --json output/outreach\<批次>.json \
    --config .secrets/send-config.json \
    --send --yes --limit 5 --delay 60
```

## 安全提醒

- App Password / 授权码**不要在聊天、工单、截图里传递**。若已泄露，立刻到对应邮箱后台**撤销并重新生成**。
- 凭据只放两处：环境变量 `SMTP_PASS`，或 `.secrets/send-config.json`（gitignored）。**任何情况下都不写进脚本、文档、JSON 交付物。**
