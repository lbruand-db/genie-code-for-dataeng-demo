---
version: 1
title: BrickSight — Genie Code Reads the Semantic Layer
---

## Section: Opening {#opening}

### Annotation: BrickVault Catalog {#brickvault-catalog}
---
timestamp: 0
color: #4CAF50
autopause: true
---

BrickVault — a fictional toy-brick market intelligence company. Their data lives in Unity Catalog under `lucasbruand_catalog.brickvault`, with table descriptions, column comments, and certified metric views. That semantic layer is what Genie Code is about to read.

```driverjs
driverObj.highlight({
  popover: {
    title: 'Meet BrickVault',
    description: 'Fictional toy-brick market intelligence company. Their Unity Catalog already has table descriptions, column comments, and certified metric views — that semantic layer is what Genie Code will read.',
    align: 'center'
  }
});
```

### Annotation: Switch to Genie Code {#switch-to-genie}
---
timestamp: 30000
---

We switch from the Catalog Explorer to a fresh Genie Code conversation. No schema hints, no table names — just a business question.

## Section: Segment 1 — What do we have? {#segment-1}

### Annotation: First Prompt {#segment-1-prompt}
---
timestamp: 40508
color: #2196F3
autopause: true
---

> "I've just joined BrickVault. What does our brick catalog look like, and which sets should we be paying attention to?"

Watch the sidebar — Genie Code navigates Unity Catalog on its own, reading descriptions on `sets` and `themes`.

```driverjs
driverObj.highlight({
  popover: {
    title: 'No schema hints',
    description: 'We gave it nothing. No table names, no columns. Watch the tool-call sidebar — it explores Unity Catalog on its own and reads the descriptions on sets and themes.',
    align: 'center'
  }
});
```

### Annotation: ★ Proof Point — set_complexity_score {#proof-set-complexity}
---
timestamp: 49896
color: #FFD600
autopause: true
---

**It picked `set_complexity_score`, not `num_parts`.**

The column comment on `num_parts` says: *"RAW count including spare parts — do not use directly. Use set_complexity_score instead."* A generic coding agent would have used `num_parts`. Genie Code read the catalog and made the right call.

```driverjs
driverObj.highlight({
  popover: {
    title: '★ Proof Point: set_complexity_score',
    description: 'It used set_complexity_score — not num_parts. The column comment on num_parts says "RAW count including spare parts — do not use directly." A generic coding agent would have used num_parts. Genie Code read the catalog.',
    align: 'center'
  }
});
```

### Annotation: EDA Charts Prompt {#eda-charts-prompt}
---
timestamp: 120090
color: #2196F3
---

> "Now show me three charts: sets per year, licensed-IP vs original, and the distribution of `set_complexity_score`."

### Annotation: EDA Charts Rendered {#eda-charts}
---
timestamp: 165000
---

Three charts render in sequence. One business question — no schema guidance — coherent analysis.

```driverjs
driverObj.highlight({
  popover: {
    title: 'One question, coherent analysis',
    description: 'One business question. No schema guidance. It found the data, chose the right metric, and produced three coherent charts.',
    align: 'center'
  }
});
```

## Section: Segment 2 — Build the risk model {#segment-2}

### Annotation: Risk Model Prompt {#segment-2-prompt}
---
timestamp: 195324
color: #2196F3
autopause: true
---

> "Build a retirement risk prediction model for our set catalog. I want to know which sets are most at risk of being retired in the next 18 months."

Same conversation — Genie Code remembers everything it just learned about the catalog.

```driverjs
driverObj.highlight({
  popover: {
    title: 'From analysis to ML pipeline',
    description: 'Same conversation — Genie Code remembers what it just learned. Now we ask it to go from EDA to a full Data + AI pipeline.',
    align: 'center'
  }
});
```

### Annotation: ★ Proof Point — ip_dependency_flag {#proof-ip-dependency}
---
timestamp: 246948
color: #FFD600
autopause: true
---

**`ip_dependency_flag` selected as a feature.**

The certified view walks the theme hierarchy to detect licensed-IP sets. The `themes` table description notes licensed themes retire 30% faster — domain knowledge embedded in the catalog, not in the prompt.

```driverjs
driverObj.highlight({
  popover: {
    title: '★ Proof Point: ip_dependency_flag',
    description: 'It used ip_dependency_flag — the certified view that walks the theme hierarchy. The themes description says licensed IP retires 30% faster. Domain knowledge embedded in the catalog, not in the prompt.',
    align: 'center'
  }
});
```

### Annotation: MLflow Run & Feature Importance {#mlflow}
---
timestamp: 328730
color: #9C27B0
autopause: true
---

MLflow run completes. Feature importance confirms `ip_dependency_flag` in the top predictors — promoted by the semantic layer, validated by the model.

```driverjs
driverObj.highlight({
  popover: {
    title: 'Feature importance confirms it',
    description: 'ip_dependency_flag is one of the top predictors. Not because we told the model — because the semantic layer told Genie Code it mattered, and the model validated it.',
    align: 'center'
  }
});
```

### Annotation: ★ Proof Point — is_spare filter {#proof-is-spare}
---
timestamp: 393226
color: #FFD600
autopause: true
---

**It filtered out spare parts without being told.**

```python
.filter(col("is_spare") == False)
```

The `is_spare` column description says: *"ALWAYS filter is_spare = false before computing part counts — failing to exclude spares inflates metrics by 5 to 15 percent."* The catalog told it. We didn't.

```driverjs
driverObj.highlight({
  popover: {
    title: '★ Proof Point: is_spare filter',
    description: 'We never mentioned spare parts. It filtered them out because the is_spare column description says "ALWAYS filter is_spare = false — failing to exclude spares inflates metrics by 5–15%." The catalog told it. We didn\'t.',
    align: 'center'
  }
});
```

### Annotation: Data + AI in One Loop {#data-ai-loop}
---
timestamp: 425000
---

Pipeline code, training, and results — all in one thread. The same semantic layer that governs your pipelines shapes your ML model.

```driverjs
driverObj.highlight({
  popover: {
    title: 'The Data + AI bridge',
    description: 'Pipeline code, training, results — one thread. The same semantic layer that governs your data pipelines shapes your ML model. One source of truth for both.',
    align: 'center'
  }
});
```

## Section: Segment 3 — Make it last {#segment-3}

### Annotation: Skill Generation Prompt {#segment-3-prompt}
---
timestamp: 447690
color: #2196F3
autopause: true
---

> "Package what you've learned about the BrickVault data model into a skill file, so the next analyst doesn't have to rediscover all of this."

### Annotation: ★ Proof Point — Self-documenting catalog {#proof-self-documenting}
---
timestamp: 475000
color: #FFD600
autopause: true
---

The skill file echoes the language from your Unity Catalog descriptions verbatim:
- The `is_spare` warning
- The licensed-IP retirement uplift note
- The `set_complexity_score` definition

Your catalog becomes self-documenting. Every Genie Code session compounds the team's knowledge.

```driverjs
driverObj.highlight({
  popover: {
    title: '★ Proof Point: Knowledge compounds',
    description: 'The skill file uses the language from your Unity Catalog descriptions verbatim. Genie Code didn\'t invent it — it read your catalog and turned it into onboarding documentation. The next analyst gets all of this automatically.',
    align: 'center'
  }
});
```

### Annotation: Closing {#closing}
---
timestamp: 495000
color: #E91E63
autopause: true
---

> "Every other coding agent writes code. Genie Code understands your data."

```driverjs
driverObj.highlight({
  popover: {
    title: 'Closing',
    description: 'Every other coding agent writes code. Genie Code understands your data.',
    align: 'center'
  }
});
```
