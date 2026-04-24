# BrickSight — Genie Code Demo Spec

## Context

**Audience:** Data engineers from Capgemini  
**Goal:** Demonstrate how Genie Code is uniquely different from generic coding agents by showcasing its ability to leverage *data semantics* — not just write code.  
**Dataset:** Public toy construction brick catalog data ([Rebrickable](https://rebrickable.com/downloads/)), rebranded as "BrickVault" — a fictional company that catalogs and tracks the toy construction brick market.  
**Tone:** Semi-serious. Enterprise-grade tooling applied to brick sets. The joke is implicit; the engineering is real.

## Timing

| Segment | Duration |
|---------|----------|
| Demo (3 prompts, pre-run results) | 10 min |
| Recap | 3 min |
| Q&A | 2 min |
| **Total** | **15 min** |

**Rule:** everything that takes more than 60 seconds to execute is **pre-run**. During the demo we type prompts and show results, we do not wait for pipelines or training jobs.

---

## Core Thesis

> A generic coding agent writes code. Genie Code understands what your data *means* — and acts on that understanding autonomously.

Every demo moment should prove this. The audience should repeatedly think: *"a standard LLM would have gotten that wrong."*

---

## Fictional Setup

**BrickVault Inc.** is a market intelligence firm covering the toy construction brick industry. Their Unity Catalog holds a certified data product covering:

- The full catalog of brick sets (historical and current)
- Theme hierarchies (licensed IP vs. original themes)
- Brick element / part catalog with supplier lineage
- Set retirement history
- Secondary market price index (community-sourced)

BrickVault's data team wants to build a **Set Retirement Risk Platform**: given the current catalog, predict which sets are most likely to be retired in the next 12–18 months, and surface insights for their analyst team.

---

## Dataset

Source: [Rebrickable bulk downloads](https://rebrickable.com/downloads/) (CC license).

| File | Table name | Description |
|------|-----------|-------------|
| `sets.csv` | `brickvault.catalog.sets` | All brick sets: set_num, name, year, theme_id, num_parts |
| `themes.csv` | `brickvault.catalog.themes` | Theme hierarchy: id, name, parent_id |
| `parts.csv` | `brickvault.catalog.parts` | Brick elements: part_num, name, part_cat_id, part_material |
| `colors.csv` | `brickvault.catalog.colors` | Color catalog: id, name, rgb, is_trans |
| `inventories.csv` | `brickvault.catalog.inventories` | Set inventory versions |
| `inventory_parts.csv` | `brickvault.catalog.inventory_parts` | Parts per inventory: quantities, spare flags |
| `minifigs.csv` | `brickvault.catalog.minifigs` | Collectible figures: fig_num, name, num_parts |
| `inventory_minifigs.csv` | `brickvault.catalog.inventory_minifigs` | Figures per inventory |

---

## Unity Catalog Semantic Layer

This is the heart of the demo. Every table and key column must carry rich metadata that Genie Code can exploit.

### Table-level descriptions (examples)

**`brickvault.catalog.sets`**
> "Master catalog of all brick sets ever produced. Each row is one set version. Use `year` + `theme_id` together to assess demand context — sets from licensed IP themes behave very differently from original themes in terms of retirement timing. Primary key: `set_num`."

**`brickvault.catalog.themes`**
> "Hierarchical theme taxonomy. Parent-child relationships model the full IP tree (e.g., 'Star-themed' → 'Galactic Saga' → 'Galactic Saga Episode IV'). Licensed themes (those with a non-null `parent_id` tracing to a licensed root) show 30% faster average retirement than original themes. Join to `sets` on `theme_id`."

**`brickvault.catalog.inventory_parts`**
> "Part-level breakdown of each set inventory. Use to compute set complexity metrics. `is_spare` = true rows should be excluded from complexity calculations. Lineage: sourced from BrickVault supplier feed, refreshed weekly."

### Column-level descriptions (examples)

| Table | Column | Description |
|-------|--------|-------------|
| `sets` | `num_parts` | Raw part count including spares. For complexity scoring use `brickvault.metrics.set_complexity_score` instead, which excludes spares and normalises by theme average. |
| `sets` | `year` | Release year. Sets older than 3 years with no inventory update are candidates for retirement scoring. |
| `themes` | `parent_id` | Null = root/original theme. Non-null and tracing to a licensed root = IP-dependent theme, higher demand volatility. |
| `colors` | `is_trans` | Transparent elements. High transparent-part ratio correlates with premium/exclusive sets — retirement risk differs from standard sets. |
| `inventory_parts` | `is_spare` | Flag for spare parts bundled in the box. Must be excluded from part-count-based complexity metrics. |
| `minifigs` | `num_parts` | Parts in the figure assembly. Proxy for figure complexity — highly detailed figures (>10 parts) correlate with licensed IP sets. |

### Certified Business Metrics (Unity Catalog Metric definitions)

| Metric name | Definition | Purpose |
|-------------|-----------|---------|
| `set_complexity_score` | `(non_spare_parts / avg_non_spare_parts_by_theme) * (1 + log(unique_colors))` | Normalised complexity indicator, theme-adjusted |
| `ip_dependency_flag` | True if theme traces to a licensed root in the themes hierarchy | Drives retirement risk uplift |
| `figure_density` | `num_minifigs / num_parts` | Proxy for collector appeal; high values = higher secondary market demand |
| `secondary_market_premium` | `(secondary_price - original_rrp) / original_rrp` | Premium paid on secondary market; negative = underperformers |

---

## Architecture

```
[Rebrickable CSVs]
        │
        ▼
[DLT Ingestion Pipeline]          ← Bronze layer (raw ingest)
        │
        ▼
[DLT Transformation Pipeline]     ← Silver layer (cleaned, typed, linked)
        │
        ▼
[Unity Catalog: brickvault.catalog.*]   ← With full semantic metadata
        │
        ├──► [Feature Engineering Notebook]   ← computes certified metrics
        │              │
        │              ▼
        │    [brickvault.features.set_retirement_features]
        │              │
        │              ▼
        │    [ML Training — MLflow]           ← retirement risk classifier
        │              │
        │              ▼
        │    [Model Serving Endpoint]         ← real-time risk scoring
        │
        └──► [Lakeview Dashboard]             ← "Set Retirement Risk Report"
                       │
                       ▼
             [Genie Code Skill]               ← "BrickVault Analyst" skill
```

---

## Demo Acts

> 3 prompts. 10 minutes total. Each prompt has one visible semantic proof point.
> The DLT pipeline and ML training are **pre-run** — we show results, not execution.

---

### Prompt 1 — "What do we have?" (3 min)
**Capability:** Semantic catalog navigation + EDA  
**Live or pre-run:** Live (fast — just catalog reads and a few queries)  
**The ask:** *"I've just joined BrickVault. What does our brick catalog look like, and which sets should we be paying attention to?"*

What Genie Code does:
- Finds `brickvault.catalog.*` from Unity Catalog — no table names given in the prompt
- Reads the theme hierarchy, identifies licensed vs. original themes from descriptions
- Produces a quick profile: sets per year, theme breakdown, complexity distribution
- Uses `set_complexity_score` instead of raw `num_parts`

**Semantic proof point:** It uses `set_complexity_score`, not `num_parts`. When asked why, it quotes the column description back verbatim. A generic agent would have used `num_parts`.

**Talking point while it runs:** *"Notice we gave it zero schema information. It found the catalog, read the metadata, and made a modeling decision we didn't ask for."*

---

### Prompt 2 — "Build the risk model" (5 min)
**Capability:** Feature engineering + ML (Data+AI bridge)  
**Live or pre-run:** Prompt is live; pipeline + training results are **pre-run**, shown as already-executed output  
**The ask:** *"Build a retirement risk prediction model for our set catalog. I want to know which sets are most at risk in the next 18 months."*

What Genie Code does:
- Writes the feature engineering logic using `ip_dependency_flag`, `figure_density`, `set_complexity_score`
- Excludes `is_spare = true` parts without being told — from the column metadata
- Trains a classifier, logs it in MLflow, shows feature importance
- `ip_dependency_flag` appears in the top 3 features

**Semantic proof point:** The `is_spare` exclusion appears in the generated code unprompted. Point at it explicitly: *"We never mentioned spare parts. It read the column description."*  
Second moment: `ip_dependency_flag` in feature importance. *"It knew licensed themes retire faster because the theme table description said so."*

**Talking point while showing results:** *"This is the Data+AI bridge. The same semantic layer that governs the data pipeline also shapes the ML model. One source of truth."*

---

### Prompt 3 — "Now make it last" (2 min)
**Capability:** Skill generation  
**Live or pre-run:** Live (fast — text output only)  
**The ask:** *"Package everything you've learned about our data model into a skill so the next analyst on the team can hit the ground running."*

What Genie Code does:
- Generates a `brickvault_analyst_skill.md` skill file
- The skill body reproduces the semantic caveats from the catalog: the `is_spare` warning, the licensed IP retirement uplift, the `set_complexity_score` definition
- The next user inherits domain knowledge without reading a single doc

**Semantic proof point:** The skill output uses the *exact language* from the table/column descriptions — it didn't invent it. The catalog metadata became institutional knowledge.

**Talking point:** *"This is the compounding effect. Every time someone runs Genie Code on your catalog, the domain knowledge gets packaged and transferred. Your documentation writes itself."*

---

## Files to Build

Priority order matches the demo flow. Items marked **[pre-run]** must be ready and executed before the demo starts.

```
genie-code-for-dataeng-demo/
├── SPECS/
│   └── SPEC.md                        ← this file
│
├── setup/                             ← run once before the demo
│   ├── 01_download_data.sh            ← downloads Rebrickable CSVs to DBFS/Volume
│   ├── 02_catalog_setup.py            ← creates catalog brickvault + schemas
│   └── 03_semantic_metadata.py        ← applies all table/column descriptions + metric definitions  ⬅ most important file
│
├── pipelines/                         ← [pre-run]
│   └── dlt_brickvault_pipeline.py     ← DLT Bronze→Silver pipeline (shown as already run in Prompt 2)
│
├── notebooks/                         ← [pre-run] except Prompt 1 which runs live
│   ├── 02_feature_engineering.py      ← builds brickvault.features.set_retirement_features [pre-run]
│   └── 03_ml_training.py              ← MLflow training + registration [pre-run]
│
└── skills/
    └── brickvault_analyst_skill.md    ← expected output of Prompt 3 (Genie Code generates this live)
```

**Dropped from scope:**
- `serving/` — model serving endpoint adds 2+ min of setup, not needed to make the point
- `monitoring/` — cut for time; mention verbally as "what comes next"
- `notebooks/01_eda.py` — Prompt 1 runs live, no starter notebook needed

---

## Key Demo Principles

1. **Never tell Genie Code the table names** in Prompts 1 and 2. It should find them from the catalog.
2. **The `is_spare` exclusion** must visibly appear in generated code — it's the clearest proof of semantic understanding.
3. **The licensed IP uplift** should appear in the model's feature importance — Genie Code picked it because the metadata said it mattered.
4. **The skill output** in Prompt 3 should quote back language from the table descriptions — proving it learned from the catalog, not from the prompt.

---

## Recap Script (3 min)

Three points, one sentence each:

1. **Semantics over syntax** — "We never told it which tables to use or which columns to trust. It read the catalog."
2. **Data+AI in one loop** — "The same metadata that governs the pipeline shaped the ML model. One source of truth for both."
3. **Knowledge compounds** — "The skill it generated will give the next analyst a head start. Your catalog becomes self-documenting."

Closing line: *"Every other coding agent writes code. Genie Code understands your data."*

---

## Out of Scope

- Real-time streaming (keeps the demo focused)
- Actual Rebrickable API calls (bulk CSV download is sufficient)
- Any brand names for specific brick set themes or figures
- Model serving endpoint (cut for time — mention verbally)
