# BrickSight — Genie Code Demo Spec

## Context

**Audience:** Data engineers from Capgemini  
**Goal:** Demonstrate how Genie Code is uniquely different from generic coding agents by showcasing its ability to leverage *data semantics* — not just write code.  
**Dataset:** Public toy construction brick catalog data ([Rebrickable](https://rebrickable.com/downloads/)), rebranded as "BrickVault" — a fictional company that catalogs and tracks the toy construction brick market.  
**Tone:** Semi-serious. Enterprise-grade tooling applied to brick sets. The joke is implicit; the engineering is real.

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

### Act 1 — Discovery (5 min)
**Capability:** EDA + semantic catalog navigation  
**The ask to Genie Code:** *"I've just joined BrickVault. What does our brick catalog look like, and which sets should we be watching?"*

What Genie Code does autonomously:
- Navigates Unity Catalog, finds `brickvault.catalog.*` tables
- Reads table descriptions to understand relationships without being told schema
- Identifies the `themes` hierarchy and the licensed IP flag
- Produces a summary EDA notebook with charts: sets per year, theme distribution, part count distribution
- Calls out that `num_parts` should not be used raw — it spots the column description warning and uses `set_complexity_score` instead

**Key semantic moment:** Genie Code uses `set_complexity_score` (the certified metric) rather than raw `num_parts`, *because the column description explicitly says so*. A generic agent would have used `num_parts`.

---

### Act 2 — Build (10 min)
**Capability:** DLT pipeline + ML model (end-to-end Data+AI)  
**The ask to Genie Code:** *"Build a retirement risk prediction pipeline for our set catalog."*

What Genie Code does autonomously:
- Creates a DLT pipeline (Bronze → Silver) for the Rebrickable source tables
- Engineers features using the catalog metric definitions (`ip_dependency_flag`, `figure_density`, `secondary_market_premium`)
- Excludes `is_spare = true` parts from all calculations because the column metadata says so
- Trains a binary classifier (retired in next 18 months) in MLflow
- Registers and serves the model via a Model Serving endpoint
- Logs the feature importance back to the catalog as a column tag

**Key semantic moment:** Genie Code excludes `is_spare` parts and applies the licensed-IP retirement uplift — both decisions driven solely by the catalog metadata, not by explicit user instructions.

---

### Act 3 — Scale (5 min)
**Capability:** Skills + monitoring + background agent  
**The ask to Genie Code:** *"Make sure this platform stays up to date when new sets are released, and package your knowledge for the next analyst."*

What Genie Code does autonomously:
- Creates a monitoring notebook that re-triggers the retirement scoring pipeline when `catalog.sets` is updated
- Writes and registers a **BrickVault Analyst Skill** so any future user can ask questions in the context of BrickVault's domain model
- The skill includes: table relationship guidance, metric definitions, known data quality caveats (the `is_spare` flag, the licensed IP hierarchy logic)

**Key semantic moment:** The skill it generates *includes the same semantic caveats* it learned from the catalog metadata. The next analyst inherits the knowledge without reading any documentation.

---

## Files to Build

```
genie-code-for-dataeng-demo/
├── SPECS/
│   └── SPEC.md                        ← this file
├── setup/
│   ├── 01_download_data.sh            ← downloads Rebrickable CSVs
│   ├── 02_catalog_setup.py            ← creates catalog, schemas, uploads to volumes
│   └── 03_semantic_metadata.py        ← applies all table/column descriptions + metric definitions
├── pipelines/
│   └── dlt_brickvault_pipeline.py     ← DLT Bronze→Silver pipeline
├── notebooks/
│   ├── 01_eda.py                      ← EDA notebook (Act 1 starting point)
│   ├── 02_feature_engineering.py      ← builds the feature table (Act 2)
│   └── 03_ml_training.py              ← MLflow training + registration (Act 2)
├── serving/
│   └── 04_model_serving.py            ← endpoint creation + test query
├── monitoring/
│   └── 05_pipeline_monitor.py         ← re-trigger logic (Act 3)
└── skills/
    └── brickvault_analyst_skill.md    ← Genie Code skill definition (Act 3)
```

---

## Key Demo Principles

1. **Never tell Genie Code the table names** in Acts 1 and 2. It should find them from the catalog.
2. **The `is_spare` exclusion** must visibly appear in generated code — it's the clearest proof of semantic understanding.
3. **The licensed IP uplift** should appear in the model's feature importance — Genie Code picked it because the metadata said it mattered.
4. **The skill output** in Act 3 should quote back language from the table descriptions — proving it learned from the catalog, not from the prompt.

---

## Out of Scope

- Real-time streaming (keeps the demo focused)
- Actual Rebrickable API calls (bulk CSV download is sufficient)
- Any brand names for specific brick set themes or figures
