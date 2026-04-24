# BrickSight — Genie Code Demo Spec

## Context

**Audience:** Data engineers from Capgemini  
**Goal:** Demonstrate how Genie Code is uniquely different from generic coding agents by showcasing its ability to leverage *data semantics* — not just write code.  
**Dataset:** Public toy construction brick catalog data ([Rebrickable](https://rebrickable.com/downloads/)), rebranded as "BrickVault" — a fictional company that catalogs and tracks the toy construction brick market.  
**Tone:** Semi-serious. Enterprise-grade tooling applied to brick sets. The joke is implicit; the engineering is real.

## Timing

| Segment | Duration |
|---------|----------|
| Demo (rrweb recording) | 10 min |
| Recap | 3 min |
| Q&A | 2 min |
| **Total** | **15 min** |

**Delivery:** the demo is a prerecorded rrweb session replayed in the browser. No live typing, no risk of failure on stage. You talk over the replay.

**Recording approach:**
- Record the full real session in Genie Code (may take 30–45 min including actual execution)
- Edit the rrweb recording to cut or 10× speed through waiting periods (pipeline runs, model training, token generation)
- Target playback duration: exactly 10 min at 1× speed
- Pause points for commentary are built into the recording as deliberate slow moments

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
| `sets.csv` | `lucasbruand_catalog.brickvault.sets` | All brick sets: set_num, name, year, theme_id, num_parts |
| `themes.csv` | `lucasbruand_catalog.brickvault.themes` | Theme hierarchy: id, name, parent_id |
| `parts.csv` | `lucasbruand_catalog.brickvault.parts` | Brick elements: part_num, name, part_cat_id, part_material |
| `colors.csv` | `lucasbruand_catalog.brickvault.colors` | Color catalog: id, name, rgb, is_trans |
| `inventories.csv` | `lucasbruand_catalog.brickvault.inventories` | Set inventory versions |
| `inventory_parts.csv` | `lucasbruand_catalog.brickvault.inventory_parts` | Parts per inventory: quantities, spare flags |
| `minifigs.csv` | `lucasbruand_catalog.brickvault.minifigs` | Collectible figures: fig_num, name, num_parts |
| `inventory_minifigs.csv` | `lucasbruand_catalog.brickvault.inventory_minifigs` | Figures per inventory |

---

## Unity Catalog Semantic Layer

This is the heart of the demo. Every table and key column must carry rich metadata that Genie Code can exploit.

### Table-level descriptions (examples)

**`lucasbruand_catalog.brickvault.sets`**
> "Master catalog of all brick sets ever produced. Each row is one set version. Use `year` + `theme_id` together to assess demand context — sets from licensed IP themes behave very differently from original themes in terms of retirement timing. Primary key: `set_num`."

**`lucasbruand_catalog.brickvault.themes`**
> "Hierarchical theme taxonomy. Parent-child relationships model the full IP tree (e.g., 'Star-themed' → 'Galactic Saga' → 'Galactic Saga Episode IV'). Licensed themes (those with a non-null `parent_id` tracing to a licensed root) show 30% faster average retirement than original themes. Join to `sets` on `theme_id`."

**`lucasbruand_catalog.brickvault.inventory_parts`**
> "Part-level breakdown of each set inventory. Use to compute set complexity metrics. `is_spare` = true rows should be excluded from complexity calculations. Lineage: sourced from BrickVault supplier feed, refreshed weekly."

### Column-level descriptions (examples)

| Table | Column | Description |
|-------|--------|-------------|
| `sets` | `num_parts` | Raw part count including spares. For complexity scoring use `lucasbruand_catalog.brickvault.set_complexity_score` instead, which excludes spares and normalises by theme average. |
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
[Unity Catalog: lucasbruand_catalog.brickvault.*]   ← With full semantic metadata
        │
        ├──► [Feature Engineering Notebook]   ← computes certified metrics
        │              │
        │              ▼
        │    [lucasbruand_catalog.brickvault.set_retirement_features]
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

## Recording Script

3 prompts, 10 minutes of edited playback. Each segment has a target duration, the exact prompt text to type, what the recording must show, and the **proof point** to pause on.

---

### Segment 1 — "What do we have?" — target: 3 min 00 s

**What to show before typing:**
- Open a fresh Genie Code conversation in the `brickvault` catalog context
- Scroll slowly past the Unity Catalog browser so the audience sees `lucasbruand_catalog.brickvault.*` tables listed — 5 seconds, no clicking

**Prompt to type (slowly, readable):**
```
I've just joined BrickVault. What does our brick catalog look like,
and which sets should we be paying attention to?
```

**What the recording must show Genie Code doing:**
1. Reading `lucasbruand_catalog.brickvault.sets`, `lucasbruand_catalog.brickvault.themes` — tool calls visible in the sidebar
2. Navigating the theme hierarchy to identify licensed vs. original themes
3. Generating a notebook with: sets per year bar chart, theme breakdown, complexity distribution using `set_complexity_score`

**Proof point — pause 5 seconds here:**
The generated code contains `set_complexity_score` not `num_parts`.  
Genie Code's explanation should quote back the column description: *"num_parts includes spare parts and is not theme-normalised — set_complexity_score is the certified metric for this."*

**Cut / speed targets:**
- Token generation: 3× speed
- Notebook execution: cut entirely, show only the rendered output charts

---

### Segment 2 — "Build the risk model" — target: 5 min 00 s

**What to show before typing:**
- Stay in the same conversation (continuity matters — it remembers the catalog it just explored)

**Prompt to type:**
```
Build a retirement risk prediction model for our set catalog.
I want to know which sets are most at risk of being retired
in the next 18 months.
```

**What the recording must show Genie Code doing:**
1. Writing a DLT pipeline (Bronze → Silver) — scroll through the generated code at readable speed
2. Writing feature engineering that:
   - Computes `ip_dependency_flag` by walking the theme hierarchy
   - Excludes `is_spare = true` rows from part counts — **this line must be clearly visible**
   - Uses `figure_density` and `set_complexity_score` as features
3. Training a classifier with MLflow logging — show the MLflow UI with the completed run
4. Displaying feature importance: `ip_dependency_flag` in top 3

**Two proof points — pause 5 seconds on each:**

**Proof point A** — the `is_spare` filter in the feature code:
```python
# Exclude spare parts — they inflate part counts and skew complexity metrics
# (per lucasbruand_catalog.brickvault.inventory_parts column description)
.filter(col("is_spare") == False)
```
Say: *"We never mentioned spare parts in the prompt."*

**Proof point B** — `ip_dependency_flag` in MLflow feature importance chart, ranked #2.  
Say: *"It knew this mattered because the themes table description said licensed IP sets retire 30% faster."*

**Cut / speed targets:**
- DLT pipeline code generation: 3× speed, pause on the `is_spare` filter line
- MLflow training run: cut to the completed run UI (no waiting for epochs)
- Feature importance chart: hold for 8 seconds

---

### Segment 3 — "Make it last" — target: 2 min 00 s

**Prompt to type:**
```
Package what you've learned about the BrickVault data model
into a skill file, so the next analyst on the team
doesn't have to rediscover this.
```

**What the recording must show Genie Code doing:**
- Generating `brickvault_analyst_skill.md`
- The skill body must visibly reproduce:
  - The `is_spare` warning
  - The licensed IP retirement uplift note
  - The `set_complexity_score` definition
  - The theme hierarchy join pattern

**Proof point — slow scroll through the skill file:**
The language in the skill is verbatim from the Unity Catalog table descriptions.  
Say: *"It didn't invent this. It read your catalog and turned it into onboarding documentation."*

**Cut / speed targets:**
- Skill file generation: 2× speed, slow down to 1× when the `is_spare` and IP lines appear

---

## Files to Build

These files set up the workspace so that when Genie Code is recorded it has real data and real metadata to work with. The recording captures Genie Code generating its own code — these files are not shown in the demo.

```
genie-code-for-dataeng-demo/
├── SPECS/
│   └── SPEC.md                        ← this file
│
├── setup/                             ← run once to prepare the workspace
│   ├── 01_download_data.sh            ← downloads Rebrickable CSVs into a DBFS Volume
│   ├── 02_catalog_setup.py            ← creates catalog brickvault + schemas, loads tables
│   └── 03_semantic_metadata.py        ← applies all table/column descriptions + metric definitions  ⬅ most important file
│
└── skills/
    └── brickvault_analyst_skill.md    ← reference copy of the skill Genie Code should produce in Segment 3
```

**Dropped from scope:** DLT pipeline, feature engineering, and ML training notebooks. These are generated by Genie Code *during the recording* — we do not write them ahead of time. The recording captures the generation, then cuts to the already-executed results.

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
