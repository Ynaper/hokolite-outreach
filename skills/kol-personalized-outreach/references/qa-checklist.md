# 质量自检门 · QA Checklist

邮件生成后**必须**过这道门。`check_email.py` 是硬门（机器判定），下面是 agent 的复核清单。

---

## A. 脚本硬门（`check_email.py`，不通过即回炉）

| 检查 | 规则 |
|---|---|
| 字数 | 正文（剥离主题行/署名）词数 ∈ **[100, 160]** |
| 禁用词 | 扫描 §3 全部清单，命中即 fail（输出命中词 + 位置） |
| 首词 | 正文第一个词 ∉ {I, We, Our} |
| 链接 | 首触正文 URL 数 = **0** |
| 必备 token | 正文含达人名；含选定产品名；含主题行 |

```bash
python scripts/check_email.py \
  --email output/outreach\<creator-slug>\email.md \
  --creator-name "<达人名或频道名>" --product-name "<产品名>"
```

---

## B. agent 复核清单（逐条打勾）

```
【用户 6 条要求】
□ R1 称呼：用达人真实姓名或频道名（不是 generic "Hi there"）
□ R2 开头：引用一条真实内容 + 说明为什么关注
□ R3 产品：自然引出 HOKOLITE 对应产品 + 1–2 个核心卖点（不堆参数）
□ R4 价值：从达人和粉丝角度说明合作价值（场景 + 观众能获得什么）
□ R5 邀请：软 CTA（是否愿意了解/接收资料/讨论测评）
□ R6 语言：地道、美式、自然、友好；无 AI 模板感、无过度推销

【红线】
□ G1 未承诺免费样品 / 付费 / 佣金
□ G2 正文 100–160 英文单词
□ G3 首触无任何链接
□ G4 首词非 I/We/Our
□ G5 引用内容可回指 dossier 证据

【事实性核查（最重要）】
□ 每个引用点（视频标题/内容/品牌）都能回指 dossier 的 source_ref + observed_at
□ 无法回溯的引用 → 已删除或已泛化（不是"大概是这样"）
□ 未出现任何编造的播放量 / 互动数据 / 合作历史
□ 邮件里的产品参数/卖点与 catalog.json 完全一致（无 catalog 里没有的数字）

【Tone 复核】
□ 通读一遍，像「懂行的人写的便条」吗？像营销文案就重写
□ 主题行与正文不重复、不矛盾
□ 无 emoji、无感叹号堆叠、无全大写标题
```

---

## C. 产出 `qa-report.md`

```markdown
# QA Report — <频道名>

## 脚本硬门（check_email.py）
- 字数：<n> 词 → PASS / FAIL
- 禁用词：<无 / 命中清单>
- 首词：<word> → PASS / FAIL
- 链接数：0 → PASS / FAIL
- 必备 token：达人名 ✅ 产品名 ✅ → PASS / FAIL

## agent 复核
<R1–R6 / G1–G5 打勾表>

## 事实性核查
| 引用点 | dossier 来源 (source_ref + observed_at) | 结论 |
|---|---|---|
| ... | ... | 可回溯 ✅ / 已泛化 |

## 结论
**PASS** / **回炉重写**（列出问题）
```

**不过门 → 回炉重写，绝不带病交付。**
