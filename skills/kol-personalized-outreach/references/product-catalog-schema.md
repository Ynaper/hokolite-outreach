# 产品库规格 · Product Catalog Schema

产品库是「产品匹配」和「邮件卖点提取」的数据源。文件：`products/catalog.json`（**位于 skill 目录内**，随 skill 一起分发，装完即用）。

字段分两组：**客观字段**（`build_catalog.py` 抓取/归一化）+ **语义字段**（agent 补，需理解语义）。

---

## schema

```jsonc
{
  "version": "2026-10-12",
  "sources": ["shopify:products.json", "user:raw/xxx.xlsx"],
  "products": [
    {
      // ---------- 客观字段（脚本） ----------
      "id": "hokolite-clakap-w7-work-light",   // = handle，稳定主键
      "sku": "7741",
      "name": "CLAKAP W7 1000LM Rechargeable Magnetic Work Light",
      "brand": "HOKOLITE",
      "category": "work_light",                // 见下方枚举
      "product_type_raw": "LED WORK LIGHT",    // 保留 Shopify 原值
      "price_usd": 34.99,
      "url": "https://hokolite.com/products/...",
      "image_url": "https://cdn.shopify.com/...",
      "in_stock": true,                        // 来自 variants[].available
      "tags": ["work light", "magnetic", "rechargeable"],
      "body_text": "……",                        // body_html 去标签后的纯文本（供 agent 抽卖点）
      "source_ref": "shopify:products.json#9212906733810",
      "observed_at": "2026-10-12",

      // ---------- 语义字段（agent 补） ----------
      "one_liner": "Spotlight + COB work light + magnetic base in one folding light.",
      "key_specs": {
        "lumens": 1000, "battery_mah": 4000, "recharge": "USB-C",
        "runtime_h": null, "weight_g": null, "waterproof": null
      },
      "selling_points": [                       // ≤4 条，供邮件提取
        {
          "point": "Magnetic hands-free base",
          "benefit": "sticks to metal while you work on a car or bench",
          "scenarios": ["auto_repair", "garage", "maintenance"]
        },
        {
          "point": "180° rotating + 90° folding",
          "benefit": "aim light exactly where needed, then fold flat to store",
          "scenarios": ["inspection", "camping"]
        }
      ],
      "use_scenarios": ["garage", "auto_repair", "camping", "power_outage", "inspection", "emergency"],
      "audience": ["diy", "mechanic", "camper", "prepper", "edc"],
      "competitor_analogs": ["Olight", "NEBO"],  // 桥接用：「你测过 Olight → 这是同类」
      "claims_to_avoid": []                      // 未认证/未证实、邮件不得声称的点
    }
  ]
}
```

### `category` 枚举
`work_light` | `headlamp` | `edc_flashlight` | `camping_lantern` | `spotlight` | `bike_light` | `other`

### `use_scenarios` / `audience` 词表（尽量复用，便于匹配层做交集）
- **scenarios**：`garage` `auto_repair` `camping` `hiking` `night_hiking` `power_outage` `emergency` `inspection` `fishing` `hunting` `dog_walking` `home_security` `van_life` `backpacking` `workshop` `bike_commute`
- **audience**：`diy` `mechanic` `camper` `hiker` `prepper` `edc` `outdoor` `tradesman` `cyclist` `hunter` `angler` `homeowner` `first_responder`

### `selling_points` 写法
每条 = **卖点(point) + 收益(benefit) + 场景(scenarios)**。benefit 要写成「对使用者意味着什么」，不是参数复读。
反例：`{"point": "1000 lumens"}`（参数，邮件里就成了堆砌）
正例：`{"point": "Dual beam: spotlight + wide COB", "benefit": "flip between a long throw and a flood light without a second tool", "scenarios": ["camping", "inspection"]}`

---

## 入库流程

```bash
python scripts/build_catalog.py \
  --shopify https://hokolite.com/products.json \
  --collections work-lights,headlamps,edc-flashlights,camping-lanterns,best-sellers,new-arrivals \
  --inbox products/raw \
  --out products/catalog.json
```

- **脚本**：抓 Shopify JSON → 归一化客观字段 → 输出 catalog.json（语义字段留空/默认）。
- **agent**：读每个产品的 `body_text`，补 `one_liner / selling_points / use_scenarios / audience / competitor_analogs / claims_to_avoid`。
  Shopify 的 `body_html` 里 `<h3>` + `<li>` 通常就是现成卖点素材。
- **优先级**：用户文件（`raw/`）> Shopify 自动值。同名产品以用户文件字段覆盖。

### 用户文件解析分流（`raw/` 目录）

| 格式 | 解析方式 |
|---|---|
| xlsx / csv | `tencent-docs-sheetagent`（`mcp__sheetagent__read_table`） |
| docx | `tencent-docx` skill / python-docx |
| pdf | `pdf` / `pdfkit-py` skill |

用户文件至少应能映射到：`name / sku / category / price / 卖点 / 场景 / 受众`。缺的字段由 agent 结合 `body_text` 补。

---

## 质量要求（catalog 可用性自检）

- 每个产品**必须有**：`id / name / category / url / in_stock`。
- 进邮件候选的产品**必须有**：至少 2 条 `selling_points`、非空 `use_scenarios`、非空 `audience`。
- `key_specs` 拿不到的字段写 `null`，**不要瞎填**——邮件里出现的参数必须来自这里。
