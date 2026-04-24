# Databricks notebook source
# =============================================================================
# BrickVault — Step 3: Semantic metadata
# =============================================================================
# THIS IS THE MOST IMPORTANT SETUP FILE.
#
# Applies rich semantic metadata to every table in brickvault.catalog:
#   - Table-level descriptions (what the table is, how to join it, key caveats)
#   - Column-level comments (what each column means, what NOT to use it for)
#   - Tags (licensed IP flag on themes, data quality markers)
#   - Certified metric views in brickvault.metrics (what Genie Code should use
#     instead of raw columns)
#
# This metadata is what makes Genie Code behave differently from a generic
# coding agent. Every surprising decision it makes during the demo — using
# set_complexity_score instead of num_parts, excluding is_spare rows,
# applying the licensed-IP retirement uplift — traces back to this file.
#
# Run order: after 02_catalog_setup.py
# =============================================================================

# COMMAND ----------

# MAGIC %md
# MAGIC ## BrickVault — Step 3: Semantic Metadata
# MAGIC
# MAGIC Applies table descriptions, column comments, tags, and certified metric
# MAGIC views. Run once after catalog setup.

# COMMAND ----------

CATALOG = "brickvault"

# COMMAND ----------

# MAGIC %md ### 1 — Table descriptions

# COMMAND ----------

TABLE_COMMENTS = {
    f"{CATALOG}.catalog.sets": (
        "Master catalog of all brick sets ever produced. Each row is one set "
        "version. Use year + theme_id together to assess demand context — sets "
        "from licensed IP themes behave very differently from original themes in "
        "terms of retirement timing. Do NOT use num_parts directly for complexity "
        "analysis; use the certified metric brickvault.metrics.set_complexity_score "
        "instead, which excludes spare parts and normalises by theme average. "
        "Primary key: set_num."
    ),
    f"{CATALOG}.catalog.themes": (
        "Hierarchical theme taxonomy. Parent-child relationships model the full "
        "IP tree. A theme with parent_id IS NULL is a root/original theme owned "
        "by the manufacturer. A theme that traces (via repeated parent_id joins) "
        "to a licensed root is IP-dependent and shows 30% faster average "
        "retirement than original themes — apply this uplift in any retirement "
        "risk model. Join to sets on sets.theme_id = themes.id."
    ),
    f"{CATALOG}.catalog.parts": (
        "Master catalog of individual brick elements. part_material distinguishes "
        "standard plastic from rubber, metal, and fabric elements. Fabric and "
        "rubber parts correlate with premium sets and are disproportionately "
        "represented in licensed IP themes."
    ),
    f"{CATALOG}.catalog.colors": (
        "Color reference table. is_trans = true identifies transparent elements. "
        "A high ratio of transparent parts in a set is a proxy for premium or "
        "exclusive positioning — these sets have a different retirement risk "
        "profile from standard sets and should not be pooled with them in models."
    ),
    f"{CATALOG}.catalog.inventories": (
        "Links sets to their part inventories. A set may have multiple inventory "
        "versions (e.g., revised editions). Use the latest version per set_num "
        "when computing part-based features. Join to inventory_parts on "
        "inventories.id = inventory_parts.inventory_id."
    ),
    f"{CATALOG}.catalog.inventory_parts": (
        "Part-level breakdown of each set inventory. IMPORTANT: is_spare = true "
        "rows represent spare parts bundled in the box and MUST be excluded from "
        "all complexity and part-count calculations — including them inflates "
        "num_parts by 5-15% and biases complexity scores. "
        "Lineage: sourced from BrickVault supplier feed, refreshed weekly."
    ),
    f"{CATALOG}.catalog.minifigs": (
        "Catalog of collectible figures included in sets. num_parts reflects "
        "figure assembly complexity. Figures with more than 10 parts are "
        "considered premium and correlate strongly with licensed IP sets. "
        "Use figure_density (brickvault.metrics.figure_density) as the "
        "collector-appeal proxy in retirement risk models."
    ),
    f"{CATALOG}.catalog.inventory_minifigs": (
        "Maps figures to set inventories. Join to inventories on inventory_id "
        "to get figure counts per set. Aggregate quantity to get total figures "
        "per set before computing figure_density."
    ),
}

for full_name, comment in TABLE_COMMENTS.items():
    spark.sql(f"COMMENT ON TABLE {full_name} IS '{comment}'")
    print(f"  ✓ {full_name}")

print(f"\nTable comments applied to {len(TABLE_COMMENTS)} tables.")

# COMMAND ----------

# MAGIC %md ### 2 — Column comments

# COMMAND ----------

# Format: { "catalog.schema.table": { "column": "comment" } }
COLUMN_COMMENTS = {
    f"{CATALOG}.catalog.sets": {
        "set_num": (
            "Unique identifier for the set, e.g. '75192-1'. "
            "Primary key. The suffix (-1, -2) denotes the inventory version."
        ),
        "name": "Human-readable set name as published in the official catalog.",
        "year": (
            "Release year. Sets older than 3 years with no inventory update "
            "are candidates for retirement scoring. Do not use as a continuous "
            "feature in models without binning — retirement risk is non-linear "
            "with age."
        ),
        "theme_id": (
            "Foreign key to themes.id. Join to themes to resolve the full "
            "IP hierarchy and derive ip_dependency_flag. This is the most "
            "predictive single feature for retirement risk."
        ),
        "num_parts": (
            "RAW part count as declared in the catalog, INCLUDING spare parts. "
            "DO NOT use this column directly for complexity scoring or as an ML "
            "feature. Use the certified metric brickvault.metrics.set_complexity_score "
            "instead, which excludes spares and normalises by theme average."
        ),
    },
    f"{CATALOG}.catalog.themes": {
        "id": "Primary key. Join to sets.theme_id.",
        "name": "Display name of the theme.",
        "parent_id": (
            "Parent theme id. NULL = root theme (original, manufacturer-owned). "
            "Non-null = sub-theme. To determine if a theme is IP-dependent, "
            "walk the parent chain until parent_id IS NULL and check whether "
            "that root is a licensed IP theme. Use the derived flag "
            "brickvault.metrics.ip_dependency_flag instead of implementing "
            "this traversal yourself."
        ),
    },
    f"{CATALOG}.catalog.parts": {
        "part_num": "Unique element identifier.",
        "name": "Element display name.",
        "part_cat_id": "Part category id. Not a reliable retirement signal on its own.",
        "part_material": (
            "Material type: Plastic, Rubber, Metal, Fabric, etc. "
            "Non-plastic materials correlate with premium and licensed sets."
        ),
    },
    f"{CATALOG}.catalog.colors": {
        "id": "Color id. Join to inventory_parts.color_id.",
        "name": "Color display name.",
        "rgb": "Hex RGB value for display purposes. Not an analytical feature.",
        "is_trans": (
            "True if the element is transparent. A set with high transparent-part "
            "ratio signals premium or exclusive positioning. Compute at set level "
            "as: COUNT(is_trans=true) / COUNT(*) from inventory_parts joined to "
            "this table. Do NOT pool transparent-heavy sets with standard sets in "
            "retirement risk models — they have a distinct survival curve."
        ),
    },
    f"{CATALOG}.catalog.inventories": {
        "id": "Inventory id. Primary key. Join to inventory_parts.inventory_id.",
        "version": (
            "Inventory revision number. When a set has multiple inventories, "
            "use MAX(version) per set_num to get the most current part list."
        ),
        "set_num": "Foreign key to sets.set_num.",
    },
    f"{CATALOG}.catalog.inventory_parts": {
        "inventory_id": "Foreign key to inventories.id.",
        "part_num": "Foreign key to parts.part_num.",
        "color_id": "Foreign key to colors.id.",
        "quantity": "Number of this element in the set. Sum across rows for total part count.",
        "is_spare": (
            "TRUE if this is a spare part included as a bonus in the box. "
            "ALWAYS filter is_spare = false before computing part counts, "
            "complexity scores, or any feature derived from inventory composition. "
            "Failing to exclude spares inflates complexity metrics by 5–15%."
        ),
    },
    f"{CATALOG}.catalog.minifigs": {
        "fig_num": "Unique figure identifier.",
        "name": "Figure display name.",
        "num_parts": (
            "Number of parts in the figure assembly. Figures with >10 parts "
            "are considered premium/complex and correlate with licensed IP sets. "
            "Use figure_density at the set level (brickvault.metrics.figure_density) "
            "rather than aggregating this column directly."
        ),
    },
    f"{CATALOG}.catalog.inventory_minifigs": {
        "inventory_id": "Foreign key to inventories.id.",
        "fig_num": "Foreign key to minifigs.fig_num.",
        "quantity": "Number of this figure included in the set.",
    },
}

for full_table, columns in COLUMN_COMMENTS.items():
    for col_name, comment in columns.items():
        # Escape single quotes in comments
        safe_comment = comment.replace("'", "\\'")
        spark.sql(
            f"ALTER TABLE {full_table} "
            f"ALTER COLUMN {col_name} COMMENT '{safe_comment}'"
        )
    print(f"  ✓ {full_table} ({len(columns)} columns)")

print(f"\nColumn comments applied.")

# COMMAND ----------

# MAGIC %md ### 3 — Tags

# COMMAND ----------

# Mark licensed root themes so Genie Code can filter on this without
# needing to know the exact theme names.
#
# The licensed roots in the Rebrickable dataset are well-known by id.
# We tag them here; the ip_dependency_flag metric view uses these tags.

LICENSED_ROOT_THEME_IDS = [
    18,   # Star-themed space adventure
    65,   # Superhero franchises
    67,   # Superhero franchises (second publisher)
    494,  # Brick-film franchise
    504,  # Galactic saga
    579,  # Dinosaur park franchise
    591,  # Wizards and magic school
    598,  # Toy cowboy franchise
    605,  # Racing franchise
    688,  # Martial arts franchise
    700,  # City spy franchise
]

id_list = ", ".join(str(i) for i in LICENSED_ROOT_THEME_IDS)

spark.sql(f"""
    ALTER TABLE {CATALOG}.catalog.themes
    SET TAGS ('licensed_ip_root' = 'true')
    WHERE id IN ({id_list})
""") if False else None  # Unity Catalog row-level tags not yet GA — use a flag column instead

# Materialise as a flag column for reliable use in metric views
spark.sql(f"""
    ALTER TABLE {CATALOG}.catalog.themes
    ADD COLUMN IF NOT EXISTS is_licensed_root BOOLEAN
""")

spark.sql(f"""
    UPDATE {CATALOG}.catalog.themes
    SET is_licensed_root = CASE WHEN id IN ({id_list}) THEN true ELSE false END
""")

print("Licensed IP root flag applied to themes table.")

# COMMAND ----------

# MAGIC %md ### 4 — Certified metric views
# MAGIC
# MAGIC These views are the **single source of truth** for BrickVault's business
# MAGIC metrics. Genie Code should use these rather than recomputing raw columns.
# MAGIC The view comments explain exactly what each metric means.

# COMMAND ----------

# ── ip_dependency_flag ────────────────────────────────────────────────────────
# Recursively walks the theme hierarchy to determine whether a set's theme
# is IP-dependent (licensed from a third party).

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.metrics.ip_dependency_flag
COMMENT 'For each set, resolves whether its theme is licensed IP by walking
the theme parent hierarchy. ip_dependent = true means the set is based on
a licensed third-party franchise and shows ~30% faster historical retirement
than original themes. Use this as a binary feature in retirement risk models
and as a stratification variable in EDA — never pool licensed and original
themes without this flag.'
AS
WITH RECURSIVE theme_tree AS (
    -- base: all themes
    SELECT id, name, parent_id, is_licensed_root,
           id AS root_id, is_licensed_root AS traces_to_licensed_root
    FROM {CATALOG}.catalog.themes

    UNION ALL

    -- walk up the parent chain
    SELECT c.id, c.name, c.parent_id, c.is_licensed_root,
           p.root_id,
           p.traces_to_licensed_root OR c.is_licensed_root
    FROM {CATALOG}.catalog.themes c
    JOIN theme_tree p ON c.parent_id = p.id
    WHERE p.root_id != c.id  -- cycle guard
)
SELECT
    s.set_num,
    s.theme_id,
    BOOL_OR(tt.traces_to_licensed_root) AS ip_dependent
FROM {CATALOG}.catalog.sets s
JOIN theme_tree tt ON s.theme_id = tt.id
GROUP BY s.set_num, s.theme_id
""")
print("  ✓ metrics.ip_dependency_flag")

# COMMAND ----------

# ── set_complexity_score ──────────────────────────────────────────────────────

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.metrics.set_complexity_score
COMMENT 'Normalised complexity score for each set. Computed as:
  (non_spare_parts / avg_non_spare_parts_for_theme) * (1 + LN(1 + unique_colors))
Spare parts (is_spare = true) are excluded. The score is theme-normalised so
that a small City set and a large Technic set can be compared meaningfully.
A score > 1.5 indicates an unusually complex set for its theme.
Use this instead of raw num_parts for any complexity-related feature or filter.'
AS
WITH non_spare_counts AS (
    SELECT
        i.set_num,
        COUNT(*)                                        AS non_spare_parts,
        COUNT(DISTINCT ip.color_id)                     AS unique_colors
    FROM {CATALOG}.catalog.inventories i
    JOIN (
        SELECT inventory_id, part_num, color_id, quantity,
               ROW_NUMBER() OVER (
                   PARTITION BY (
                       SELECT set_num FROM {CATALOG}.catalog.inventories
                       WHERE id = inventory_id
                   )
                   ORDER BY version DESC
               ) AS rn
        FROM {CATALOG}.catalog.inventory_parts
        WHERE is_spare = false
    ) ip ON i.id = ip.inventory_id AND ip.rn = 1
    GROUP BY i.set_num
),
theme_avg AS (
    SELECT
        s.theme_id,
        AVG(nsc.non_spare_parts) AS avg_non_spare_parts_by_theme
    FROM non_spare_counts nsc
    JOIN {CATALOG}.catalog.sets s ON nsc.set_num = s.set_num
    GROUP BY s.theme_id
)
SELECT
    nsc.set_num,
    s.theme_id,
    nsc.non_spare_parts,
    nsc.unique_colors,
    ta.avg_non_spare_parts_by_theme,
    ROUND(
        (nsc.non_spare_parts / NULLIF(ta.avg_non_spare_parts_by_theme, 0))
        * (1 + LN(1 + nsc.unique_colors)),
        4
    ) AS set_complexity_score
FROM non_spare_counts nsc
JOIN {CATALOG}.catalog.sets s ON nsc.set_num = s.set_num
JOIN theme_avg ta ON s.theme_id = ta.theme_id
""")
print("  ✓ metrics.set_complexity_score")

# COMMAND ----------

# ── figure_density ────────────────────────────────────────────────────────────

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.metrics.figure_density
COMMENT 'Collector appeal proxy: total figures per non-spare part count for each set.
A higher ratio signals a figure-heavy set which correlates with licensed IP themes
and stronger secondary market demand. Sets with figure_density > 0.05 should be
treated as collector items in retirement risk models — they have a distinct
survival curve driven by character popularity, not set complexity.'
AS
WITH latest_inventory AS (
    SELECT set_num, MAX(id) AS inventory_id
    FROM {CATALOG}.catalog.inventories
    GROUP BY set_num
),
fig_counts AS (
    SELECT li.set_num, COALESCE(SUM(im.quantity), 0) AS total_figures
    FROM latest_inventory li
    LEFT JOIN {CATALOG}.catalog.inventory_minifigs im
        ON li.inventory_id = im.inventory_id
    GROUP BY li.set_num
),
part_counts AS (
    SELECT i.set_num, COUNT(*) AS non_spare_parts
    FROM {CATALOG}.catalog.inventories i
    JOIN {CATALOG}.catalog.inventory_parts ip
        ON i.id = ip.inventory_id AND ip.is_spare = false
    GROUP BY i.set_num
)
SELECT
    f.set_num,
    f.total_figures,
    p.non_spare_parts,
    ROUND(
        f.total_figures / NULLIF(p.non_spare_parts, 0),
        6
    ) AS figure_density
FROM fig_counts f
JOIN part_counts p ON f.set_num = p.set_num
""")
print("  ✓ metrics.figure_density")

# COMMAND ----------

# MAGIC %md ### 5 — Verify

# COMMAND ----------

print("Views in brickvault.metrics:")
for row in spark.sql(f"SHOW VIEWS IN {CATALOG}.metrics").collect():
    print(f"  {row.viewName}")

print("\nSample — set_complexity_score (top 10):")
display(
    spark.table(f"{CATALOG}.metrics.set_complexity_score")
    .join(spark.table(f"{CATALOG}.catalog.sets").select("set_num", "name"), "set_num")
    .orderBy("set_complexity_score", ascending=False)
    .limit(10)
)

# COMMAND ----------

# MAGIC %md
# MAGIC **Setup complete.**
# MAGIC The BrickVault catalog is now fully annotated with semantic metadata.
# MAGIC Genie Code can now navigate this catalog intelligently without being
# MAGIC given explicit schema guidance.
# MAGIC
# MAGIC Proceed to record the demo session as described in `SPECS/SPEC.md`.
