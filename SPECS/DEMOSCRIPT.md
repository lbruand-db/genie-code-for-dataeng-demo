# BrickSight — Demo Script

**Format:** prerecorded rrweb session, replayed in browser  
**Total runtime:** 10 min 00 s  
**Voiceover:** live, over the replay  
**Audience:** data engineers, Capgemini

Legend:
- `[SCREEN]` — what to do / show on screen during recording
- `[SAY]` — what to say live over the replay (not recorded)
- `[PAUSE N]` — hold the replay here for N seconds while speaking
- `[CUT]` — edit point: cut or speed up to next state

---

## Pre-recording checklist

Before hitting record:
- [ ] Workspace: `https://e2-demo-field-eng.cloud.databricks.com`
- [ ] Catalog context set to `lucasbruand_catalog`
- [ ] Genie Code open, fresh empty conversation
- [ ] Browser zoom: 100%, full screen, no bookmarks bar
- [ ] Font size readable at presentation resolution
- [ ] Unity Catalog Explorer open in a side tab (for the catalog browse moment)

---

## Recording: Opening (0:00 – 0:30)

`[SCREEN]` Show the Unity Catalog Explorer tab. Slowly expand `lucasbruand_catalog` → `brickvault`. Let the table list appear: `sets`, `themes`, `parts`, `colors`, `inventories`, `inventory_parts`, `minifigs`, `inventory_minifigs`, and the three views.

`[SCREEN]` Click on `sets`. Let the schema panel appear showing columns and — crucially — the table description text.

`[SCREEN]` Scroll down slowly so the table description is readable for 3 seconds. Then switch to the Genie Code tab.

`[SAY]`
> "This is BrickVault — a fictional market intelligence company for the toy construction brick industry. Their data lives in Databricks Unity Catalog. Notice the catalog already has table descriptions, column comments, and certified metric views. That's the semantic layer. That's what we're going to let Genie Code read."

---

## Segment 1 — "What do we have?" (0:30 – 3:30)

**Target:** 3 min 00 s

### Prompt

`[SCREEN]` In the Genie Code conversation, click the input box. Type slowly (readable pace):

```
I've just joined BrickVault. What does our brick catalog look like,
and which sets should we be paying attention to?
```

`[SCREEN]` Hit enter. The tool-call sidebar appears showing Genie Code reading the catalog.

`[CUT]` Speed tool-call expansion to 3×. Slow back to 1× when the sidebar shows it has opened `lucasbruand_catalog.brickvault.sets` and `lucasbruand_catalog.brickvault.themes`.

`[SAY]`
> "We gave it nothing. No table names, no schema hints. Watch the sidebar — it's navigating Unity Catalog on its own, reading the descriptions."

`[SCREEN]` Genie Code generates a notebook. Let the code stream at 2× speed.

`[PAUSE 3]` When the code contains `set_complexity_score`, slow to 1× and hold.

### ★ Proof point 1 (hold 5 seconds)

`[SCREEN]` The generated code references `lucasbruand_catalog.brickvault.set_complexity_score`, not `num_parts`. Scroll so this line is centred on screen.

`[SAY]`
> "Stop here. It used `set_complexity_score` — not `num_parts`. We never mentioned that metric. It read the column description on `num_parts`, which says: *'RAW count including spare parts — do not use directly. Use set_complexity_score instead.'* A generic coding agent would have used `num_parts`. Genie Code read the catalog and made the right call."

`[SCREEN]` Continue streaming. Genie Code produces the EDA notebook. Then send a follow-up prompt to get the charts explicitly:

```
Now show me three charts:
1. Number of sets released per year
2. Distribution of sets by theme type (licensed IP vs original)
3. Distribution of set_complexity_score across the catalog
```

`[SCREEN]` Genie Code runs the notebook cells. Let the three charts render in sequence.

`[CUT]` Skip notebook execution waiting. Cut directly to the rendered chart output — all three charts visible.

`[SAY]`
> "One business question. No schema guidance. It found the data, chose the right metric, and produced a coherent analysis."

---

## Segment 2 — "Build the risk model" (3:30 – 8:30)

**Target:** 5 min 00 s

### Prompt

`[SCREEN]` Still in the same conversation (continuity is visible). Type:

```
Build a retirement risk prediction model for our set catalog.
I want to know which sets are most at risk of being retired
in the next 18 months.
```

`[SCREEN]` Hit enter.

`[SAY]`
> "Same conversation — it remembers everything it just learned about the catalog. Now we're asking it to go from analysis to a full Data-plus-AI pipeline."

### Feature engineering code

`[SCREEN]` Genie Code begins writing feature engineering code. Stream at 2×.

`[PAUSE 3]` Slow to 1× when the feature code appears. Scroll to find the `is_spare` filter line.

### ★ Proof point 2a (hold 6 seconds)

`[SCREEN]` Centre this line on screen:

```python
# Exclude spare parts — they inflate part counts and skew complexity metrics
# (per lucasbruand_catalog.brickvault.inventory_parts column description)
.filter(col("is_spare") == False)
```

`[SAY]`
> "We never mentioned spare parts. Not once. It filtered them out because the `is_spare` column description says: *'ALWAYS filter is_spare = false before computing part counts — failing to exclude spares inflates metrics by 5 to 15 percent.'* The catalog told it. We didn't."

`[SCREEN]` Continue streaming feature code. Let `ip_dependency_flag` appear as a feature.

### ★ Proof point 2b (hold 5 seconds)

`[SCREEN]` Scroll to where `ip_dependency_flag` is used as a feature. Hold.

`[SAY]`
> "It's using `ip_dependency_flag` — the view that walks the theme hierarchy to detect licensed IP sets. It included this because the `themes` table description says licensed themes retire 30% faster. That's domain knowledge embedded in the catalog, not in the prompt."

### MLflow + feature importance

`[SCREEN]` Genie Code continues: writes training code, logs to MLflow. Stream at 3×.

`[CUT]` Cut the actual training wait. Jump directly to the MLflow run UI showing a completed run.

`[SCREEN]` Show the MLflow experiment: run completed, metrics visible. Then show the feature importance chart. `ip_dependency_flag` is in the top 3 features.

`[PAUSE 4]` Hold on the feature importance chart.

`[SAY]`
> "Feature importance confirms it. `ip_dependency_flag` is one of the top predictors. Not because we told the model to use it — because the semantic layer told Genie Code it mattered, and Genie Code included it."

`[SCREEN]` Scroll back up to show the full Genie Code response: pipeline code, training, results — in one thread.

`[SAY]`
> "This is the Data-plus-AI bridge. The same semantic layer that governs your data pipelines shapes your ML model. One source of truth for both."

---

## Segment 3 — "Make it last" (8:30 – 10:00)

**Target:** 1 min 30 s

### Prompt

`[SCREEN]` Still the same conversation. Type:

```
Package what you've learned about the BrickVault data model
into a skill file, so the next analyst on the team doesn't
have to rediscover all of this.
```

`[SCREEN]` Hit enter. Genie Code streams the skill markdown file. Speed at 1.5×.

### ★ Proof point 3 (slow scroll, 8 seconds)

`[SCREEN]` When the skill output is complete, scroll slowly through it. The skill contains:
- The `is_spare` warning (verbatim from the column description)
- The licensed IP retirement uplift note
- The `set_complexity_score` definition and usage guidance

`[SAY]`
> "The language in this skill file is the language from your Unity Catalog descriptions. Genie Code didn't invent it — it read your catalog and turned it into onboarding documentation. The next analyst who joins BrickVault gets all of this automatically."

`[SCREEN]` Scroll to the bottom of the skill file. Hold on the final line:

```
*This skill was generated by Genie Code from the BrickVault Unity Catalog
semantic metadata.*
```

`[SAY]`
> "Your catalog becomes self-documenting. Every time Genie Code works on your data, domain knowledge gets packaged and transferred. That's the compounding effect."

`[SCREEN]` Fade out on the skill file.

---

## Recap — spoken, no recording (3 min)

Three points. One sentence each. Pause after each one.

**Point 1 — Semantics over syntax**
> "We never told Genie Code which tables to use or which columns to trust. It read the catalog."

**Point 2 — Data and AI in one loop**
> "The same metadata that governs the pipeline shaped the ML model. One source of truth for both."

**Point 3 — Knowledge compounds**
> "The skill it generated gives the next analyst a head start. Your catalog becomes self-documenting."

**Closing line** — say this slowly:
> "Every other coding agent writes code. Genie Code understands your data."

---

## Q&A prep (2 min)

Likely questions and short answers:

**"Can it work with our existing data catalog, or do we need to start from scratch?"**
> It reads whatever metadata you have in Unity Catalog today. The richer the descriptions, the smarter the decisions. You can add metadata incrementally — even one well-described table is better than none.

**"How does it know which catalog to look at?"**
> You set the catalog context when you open the Genie Code session. It then explores within that context. You can also point it at specific schemas explicitly in the prompt.

**"What if the model makes a wrong decision based on bad metadata?"**
> Same as any code review — you review what it generated before you run it in production. The difference is that the decisions are traceable: you can see exactly which column description or metric definition drove a choice.

**"Is the skill file it generated actually usable, or is it just a summary?"**
> It's a real Databricks workspace skill file. You upload it to the workspace and it becomes available to any Genie Code user in that workspace. What you saw is the actual output format.

**"What about data governance — does it respect access controls?"**
> Yes. Genie Code operates under the identity of the logged-in user. If a table is masked or a column is access-controlled in Unity Catalog, Genie Code sees what that user sees — no more.
