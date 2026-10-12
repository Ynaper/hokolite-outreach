# 产品匹配规则 · Product Matching

**输入**：`creator-signal`（来自 dossier）
**输出**：主推产品 1 个（必要时备选 1 个），或判定「不匹配」

---

## 打分规则（0–100）

对 `catalog.json` 里每个 **in_stock** 产品计算：

| 维度 | 规则 | 分值 |
|---|---|---|
| **品类匹配** | creator 品类 == product.category → +40；相邻品类 → +20 | ≤40 |
| **场景重叠** | `|creator.scenarios ∩ product.use_scenarios|` × 8 | ≤24 |
| **受众重叠** | `|creator.audience ∩ product.audience|` × 8 | ≤16 |
| **竞品桥接** | `creator.brand_hits ∩ product.competitor_analogs ≠ ∅` → +15 | +15 |
| **内容形态** | `content_format ∈ {review, unboxing, field_test}` → +5 | +5 |
| **缺货** | `in_stock == false` → -30（通常直接排除） | -30 |
| **合规风险** | `claims_to_avoid` 非空且邮件可能触发 → -20 | -20 |

**排序取 top1。并列时优先「有竞品桥接」的那个**（那是邮件里最有说服力的理由）。

### 阈值
- `max(score) ≥ 30` → 出邮件。
- `max(score) < 30` → **判「不匹配」，不出邮件**。产出「不建议合作」结论及原因。
  （例：`output/creator-two-minute-papers.md` 的 AI 论文频道，6 个品牌命中全 0 → 正确筛掉。）

### 建联资格门槛（匹配分 ≠ 值得建联）⚠️

**内容匹配分只衡量「相关性」，不代表「值得投入」。** 出邮件前还须过下面两道门：

| 门槛 | 判据 | 不通过时 |
|---|---|---|
| **活跃度** | 近期（≤3 个月）有更新 | 标 `不活跃`，`recommended=false` |
| **量级** | 粉丝数 ≥ 2K（可调） | 标 `量级不足`，`recommended=false` |

- 任一不通过 → **不出邮件**，但**保留匹配分与理由**，在记录里说明「内容相关但不建议建联」。
- 反例（实测）：`@tonych_edc` 内容匹配 **76 分**（EDC + Olight 竞品桥接），但仅 **1K 粉丝、最新帖为一年前** → 判 `recommended=false`。若只看匹配分就会误推。
- 粉丝数拿不到时（imginn/pixnoy 常不返回）：用第三方估算标 `Estimated`，并在 `data_gaps` 记明，**不要用估算值硬过门槛**。

### 品类相邻关系（用于 +20）
```
work_light  ↔ auto_repair / garage / inspection 场景的户外/EDC 频道
headlamp    ↔ hiking / camping / running / outdoor
edc_flashlight ↔ edc / self_defense / everyday_carry
camping_lantern ↔ camping / van_life / power_outage
spotlight   ↔ hunting / home_security / outdoor
bike_light  ↔ cycling / bike_commute
```

---

## 只选 1 个主推产品

**不要在一封邮件里堆多个产品。** 只推最匹配的 1 个，让达人和读者聚焦。确实难分伯仲时，可在 `product-match.md` 里记 1 个备选，但邮件正文只提主推款。

---

## 产出格式：`product-match.md`

```markdown
# 产品匹配 — <频道名>

## 信号摘要
- 品类：<niche>
- 场景：<scenarios>
- 受众：<audience>
- 历史测评品牌：<brand_hits>
- 内容形态：<content_format>

## 候选打分表
| 产品 | 品类 | 场景 | 受众 | 桥接 | 形态 | 合计 | 理由 |
|---|---|---|---|---|---|---|---|
| CLAKAP W7 | 40 | 16 | 8 | 15 | 5 | 84 | 竞品桥接(Olight) + 场景重叠(garage/blackout) |
| ... | | | | | | | |

## 结论
- **主推**：CLAKAP W7（score 84）
- **理由**：<一句话>
- **邮件将采用的卖点**：#1 magnetic base、#3 dual-beam（各含场景）
- （可选）备选：<产品>（score xx）
```
