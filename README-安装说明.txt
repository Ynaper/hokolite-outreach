================================================================
HOKOLITE 达人开发信 Skill · kol-personalized-outreach v1.0.0
================================================================

【这是什么】
输入一个达人主页链接（YouTube / Instagram / Facebook），自动完成：
  调研达人频道内容 → 匹配 HOKOLITE 产品 → 生成个性化英文开发邮件
  → 输出结构化 JSON（达人信息 + 匹配理由 + 英文邮件 + 中文说明）。
可选：经 SMTP 真实发送（默认只出草稿，绝不自动发）。

【包内结构】
  README-安装说明.txt                  本文件
  skills/kol-personalized-outreach/    skill 本体（整个目录即分发单元）
      ├── SKILL.md                     主文件（唯一契约 + 工作流）
      ├── references/                  9 个规范文档（邮件规格/匹配规则/平台适配/输出 schema…）
      ├── scripts/                     3 个脚本（建产品库 / 硬门校验 / SMTP 发送）
      └── products/                    产品库（随 skill 打包，装完即用）
          ├── catalog.json             HOKOLITE 产品库（67 个产品，运行时只读）
          ├── brand-facts.md           品牌事实（署名/口吻/禁用声明）★需要填写
          └── semantic-fields.json     产品语义字段（卖点/场景，供重建产品库用）

【安装】
本 skill 遵循 Agent Skills 开放标准（SKILL.md + YAML frontmatter），
可在 Codex / Claude Code 等 70+ 个宿主运行。

  · Codex / 其他宿主：
        npx skills add <本包解压后的路径> -a codex
    （会安装到 .agents/skills/）

  · WorkBuddy：
        把 skills/kol-personalized-outreach/ 整个目录复制到
        <你的项目>/.workbuddy-ai/skills/ 下

【安装后必须配置】
1. 品牌署名 —— 编辑 skill 目录内的 products/brand-facts.md，把 [YOUR NAME] / [TITLE]
   换成真实姓名与职位。这是合规要求（CAN-SPAM），也直接影响邮件观感。

2. SMTP 凭据 —— 只有要真发邮件时才需要。在包根目录建 .secrets/send-config.json
   （模板：skills/kol-personalized-outreach/references/send-config.example.json）：
       {
         "provider": "gmail",
         "smtp_user": "you@gmail.com",
         "smtp_pass": "App Password（Gmail）或授权码（QQ）",
         "from_email": "you@gmail.com",
         "from_name": "你的名字"
       }
   或改设环境变量 SMTP_PASS。切勿把该文件提交到代码库。

【怎么用】
对 AI 说：
  「给这个达人写开发信 https://www.youtube.com/@xxx」
  「把这个链接跑一下 https://www.instagram.com/xxx/」
流程结束后会产出一份 JSON，含邮件主题行与正文（英文）+ 中文撰写说明。

【重要提醒】
1. 默认只产出草稿，不会自动发送；真发需显式 --send --yes。
2. 强烈建议用独立发送域名，不要用个人 Gmail / QQ 发开发信
   —— 大概率进垃圾箱，且可能触发发信封禁。
3. 邮件中不得承诺免费样品 / 付费 / 佣金（skill 已内置禁用词校验）。
4. 不要把 .secrets/（密码）或 output/（含达人真实资料）提交到代码库。

【依赖】
Python 3（仅标准库，无第三方依赖）。

【跨平台说明】
所有路径均为相对路径：scripts/…、references/…、products/… 相对 skill 目录；
output/…、.secrets/… 相对项目根。
脚本会自动探测项目根，也可用环境变量 KOL_WORKSPACE 覆盖。换机器无需改路径。
