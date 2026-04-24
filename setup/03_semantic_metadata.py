# Databricks notebook source
# =============================================================================
# BrickVault — Step 3: Semantic metadata
# =============================================================================
# THIS IS THE MOST IMPORTANT SETUP FILE.
#
# Applies rich semantic metadata to every table in lucasbruand_catalog.brickvault:
#   - Table-level descriptions (what the table is, how to join it, key caveats)
#   - Column-level comments (what each column means, what NOT to use it for)
#   - Licensed IP flag column on the themes table
#   - Certified metric views (what Genie Code should use instead of raw columns)
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
# MAGIC Applies table descriptions, column comments, and certified metric views
# MAGIC to `lucasbruand_catalog.brickvault`. Run once after catalog setup.

# COMMAND ----------

CATALOG = "lucasbruand_catalog"
SCHEMA  = "brickvault"

def tbl(name: str) -> str:
    return f"{CATALOG}.{SCHEMA}.{name}"

# COMMAND ----------

# MAGIC %md ### 1 — Table descriptions

# COMMAND ----------

TABLE_COMMENTS = {
    tbl("sets"): (
        "Master catalog of all brick sets ever produced. Each row is one set "
        "version. Use year + theme_id together to assess demand context — sets "
        "from licensed IP themes behave very differently from original themes in "
        "terms of retirement timing. Do NOT use num_parts directly for complexity "
        f"analysis; use the certified metric {CATALOG}.{SCHEMA}.set_complexity_score "
        "instead, which excludes spare parts and normalises by theme average. "
        "Primary key: set_num."
    ),
    tbl("themes"): (
        "Hierarchical theme taxonomy. Parent-child relationships model the full "
        "IP tree. A theme with parent_id IS NULL is a root/original theme owned "
        "by the manufacturer. A theme that traces (via repeated parent_id joins) "
        "to a licensed root is IP-dependent and shows 30% faster average "
        "retirement than original themes — apply this uplift in any retirement "
        "risk model. Use the derived view ip_dependency_flag rather than "
        f"traversing this hierarchy manually. Join to sets on sets.theme_id = themes.id."
    ),
    tbl("parts"): (
        "Master catalog of individual brick elements. part_material distinguishes "
        "standard plastic from rubber, metal, and fabric elements. Fabric and "
        "rubber parts correlate with premium sets and are disproportionately "
        "represented in licensed IP themes."
    ),
    tbl("colors"): (
        "Color reference table. is_trans = true identifies transparent elements. "
        "A high ratio of transparent parts in a set is a proxy for premium or "
        "exclusive positioning — these sets have a different retirement risk "
        "profile from standard sets and should not be pooled with them in models."
    ),
    tbl("inventories"): (
        "Links sets to their part inventories. A set may have multiple inventory "
        "versions (e.g., revised editions). Use the latest version per set_num "
        "when computing part-based features. Join to inventory_parts on "
        "inventories.id = inventory_parts.inventory_id."
    ),
    tbl("inventory_parts"): (
        "Part-level breakdown of each set inventory. IMPORTANT: is_spare = true "
        "rows represent spare parts bundled in the box and MUST be excluded from "
        "all complexity and part-count calculations — including them inflates "
        "num_parts by 5-15% and biases complexity scores. "
        "Lineage: sourced from BrickVault supplier feed, refreshed weekly."
    ),
    tbl("minifigs"): (
        "Catalog of collectible figures included in sets. num_parts reflects "
        "figure assembly complexity. Figures with more than 10 parts are "
        "considered premium and correlate strongly with licensed IP sets. "
        "Use figure_density (view in this schema) as the collector-appeal "
        "proxy in retirement risk models."
    ),
    tbl("inventory_minifigs"): (
        "Maps figures to set inventories. Join to inventories on inventory_id "
        "to get figure counts per set. Aggregate quantity to get total figures "
        "per set before computing figure_density."
    ),
}

for full_name, comment in TABLE_COMMENTS.items():
    safe = comment.replace("'", "\\'")
    spark.sql(f"COMMENT ON TABLE {full_name} IS '{safe}'")
    print(f"  ✓ {full_name}")

print(f"\nTable comments applied to {len(TABLE_COMMENTS)} tables.")

# COMMAND ----------

# MAGIC %md ### 2 — Column comments

# COMMAND ----------

COLUMN_COMMENTS = {
    tbl("sets"): {
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
            f"feature. Use the certified view {CATALOG}.{SCHEMA}.set_complexity_score "
            "instead, which excludes spares and normalises by theme average."
        ),
    },
    tbl("themes"): {
        "id": "Primary key. Join to sets.theme_id.",
        "name": "Display name of the theme.",
        "parent_id": (
            "Parent theme id. NULL = root theme (original, manufacturer-owned). "
            "Non-null = sub-theme. To determine if a theme is IP-dependent, "
            "walk the parent chain until parent_id IS NULL and check whether "
            "that root is a licensed IP theme. Use the view ip_dependency_flag "
            "instead of implementing this traversal yourself."
        ),
        "is_licensed_root": (
            "True if this theme is a licensed IP root (e.g. a major franchise). "
            "Applied by the setup script. Used by ip_dependency_flag to resolve "
            "licensing for all child themes."
        ),
    },
    tbl("parts"): {
        "part_num": "Unique element identifier.",
        "name": "Element display name.",
        "part_cat_id": "Part category id. Not a reliable retirement signal on its own.",
        "part_material": (
            "Material type: Plastic, Rubber, Metal, Fabric, etc. "
            "Non-plastic materials correlate with premium and licensed sets."
        ),
    },
    tbl("colors"): {
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
    tbl("inventories"): {
        "id": "Inventory id. Primary key. Join to inventory_parts.inventory_id.",
        "version": (
            "Inventory revision number. When a set has multiple inventories, "
            "use MAX(version) per set_num to get the most current part list."
        ),
        "set_num": "Foreign key to sets.set_num.",
    },
    tbl("inventory_parts"): {
        "inventory_id": "Foreign key to inventories.id.",
        "part_num": "Foreign key to parts.part_num.",
        "color_id": "Foreign key to colors.id.",
        "quantity": "Number of this element in the set. Sum across rows for total part count.",
        "is_spare": (
            "TRUE if this is a spare part included as a bonus in the box. "
            "ALWAYS filter is_spare = false before computing part counts, "
            "complexity scores, or any feature derived from inventory composition. "
            "Failing to exclude spares inflates complexity metrics by 5-15%."
        ),
    },
    tbl("minifigs"): {
        "fig_num": "Unique figure identifier.",
        "name": "Figure display name.",
        "num_parts": (
            "Number of parts in the figure assembly. Figures with >10 parts "
            "are considered premium/complex and correlate with licensed IP sets. "
            "Use figure_density view at the set level rather than aggregating "
            "this column directly."
        ),
    },
    tbl("inventory_minifigs"): {
        "inventory_id": "Foreign key to inventories.id.",
        "fig_num": "Foreign key to minifigs.fig_num.",
        "quantity": "Number of this figure included in the set.",
    },
}

for full_table, columns in COLUMN_COMMENTS.items():
    for col_name, comment in columns.items():
        safe = comment.replace("'", "\\'")
        spark.sql(
            f"ALTER TABLE {full_table} "
            f"ALTER COLUMN {col_name} COMMENT '{safe}'"
        )
    print(f"  ✓ {full_table} ({len(columns)} columns)")

print("\nColumn comments applied.")

# COMMAND ----------

# MAGIC %md ### 3 — Licensed IP root flag on themes

# COMMAND ----------

# These are the licensed IP root theme ids in the Rebrickable dataset.
# Child themes that trace back to any of these roots are IP-dependent
# and show ~30% faster historical retirement.

LICENSED_ROOT_THEME_IDS = [
    18,   # Star-themed space adventure
    65,   # Superhero franchises (first publisher)
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
    ALTER TABLE {CATALOG}.{SCHEMA}.themes
    ADD COLUMN IF NOT EXISTS is_licensed_root BOOLEAN
""")

spark.sql(f"""
    UPDATE {CATALOG}.{SCHEMA}.themes
    SET is_licensed_root = CASE WHEN id IN ({id_list}) THEN true ELSE false END
""")

print("Licensed IP root flag applied to themes.")

# COMMAND ----------

# MAGIC %md ### 4 — Certified metric views
# MAGIC
# MAGIC These views are the **single source of truth** for BrickVault's business
# MAGIC metrics. Genie Code should use these rather than recomputing raw columns.

# COMMAND ----------

# ── ip_dependency_flag ────────────────────────────────────────────────────────

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.ip_dependency_flag
COMMENT 'For each set, resolves whether its theme is licensed IP by walking
the theme parent hierarchy. ip_dependent = true means the set is based on
a licensed third-party franchise and shows ~30% faster historical retirement
than original themes. Use this as a binary feature in retirement risk models
and as a stratification variable in EDA — never pool licensed and original
themes without this flag.'
AS
WITH RECURSIVE theme_tree AS (
    SELECT id, parent_id,
           is_licensed_root AS traces_to_licensed_root
    FROM {CATALOG}.{SCHEMA}.themes

    UNION ALL

    SELECT c.id, c.parent_id,
           p.traces_to_licensed_root OR c.is_licensed_root
    FROM {CATALOG}.{SCHEMA}.themes c
    JOIN theme_tree p ON c.parent_id = p.id
    WHERE c.id != p.id
)
SELECT
    s.set_num,
    s.theme_id,
    BOOL_OR(tt.traces_to_licensed_root) AS ip_dependent
FROM {CATALOG}.{SCHEMA}.sets s
JOIN theme_tree tt ON s.theme_id = tt.id
GROUP BY s.set_num, s.theme_id
""")
print(f"  ✓ {CATALOG}.{SCHEMA}.ip_dependency_flag")

# COMMAND ----------

# ── set_complexity_score ──────────────────────────────────────────────────────

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.set_complexity_score
COMMENT 'Normalised complexity score for each set. Formula:
  (non_spare_parts / avg_non_spare_parts_for_theme) * (1 + LN(1 + unique_colors))
Spare parts (is_spare = true) are excluded — always. The score is
theme-normalised so a small City set and a large Technic set can be compared
meaningfully. Score > 1.5 = unusually complex for its theme.
Use this instead of raw num_parts for any complexity-related feature or filter.'
AS
WITH latest_inv AS (
    SELECT set_num, MAX(version) AS max_ver
    FROM {CATALOG}.{SCHEMA}.inventories
    GROUP BY set_num
),
latest_inv_id AS (
    SELECT i.set_num, i.id AS inventory_id
    FROM {CATALOG}.{SCHEMA}.inventories i
    JOIN latest_inv l ON i.set_num = l.set_num AND i.version = l.max_ver
),
non_spare_counts AS (
    SELECT
        li.set_num,
        COUNT(*)                        AS non_spare_parts,
        COUNT(DISTINCT ip.color_id)     AS unique_colors
    FROM latest_inv_id li
    JOIN {CATALOG}.{SCHEMA}.inventory_parts ip
        ON li.inventory_id = ip.inventory_id
       AND ip.is_spare = false
    GROUP BY li.set_num
),
theme_avg AS (
    SELECT
        s.theme_id,
        AVG(nsc.non_spare_parts) AS avg_non_spare_parts_by_theme
    FROM non_spare_counts nsc
    JOIN {CATALOG}.{SCHEMA}.sets s ON nsc.set_num = s.set_num
    GROUP BY s.theme_id
)
SELECT
    nsc.set_num,
    s.theme_id,
    nsc.non_spare_parts,
    nsc.unique_colors,
    ROUND(ta.avg_non_spare_parts_by_theme, 2) AS avg_non_spare_parts_by_theme,
    ROUND(
        (nsc.non_spare_parts / NULLIF(ta.avg_non_spare_parts_by_theme, 0))
        * (1 + LN(1 + nsc.unique_colors)),
        4
    ) AS set_complexity_score
FROM non_spare_counts nsc
JOIN {CATALOG}.{SCHEMA}.sets s ON nsc.set_num = s.set_num
JOIN theme_avg ta ON s.theme_id = ta.theme_id
""")
print(f"  ✓ {CATALOG}.{SCHEMA}.set_complexity_score")

# COMMAND ----------

# ── figure_density ────────────────────────────────────────────────────────────

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.figure_density
COMMENT 'Collector appeal proxy: total figures per non-spare part count for each set.
Higher ratio = figure-heavy set, correlates with licensed IP themes and stronger
secondary market demand. Sets with figure_density > 0.05 should be treated as
collector items in retirement risk models — distinct survival curve driven by
character popularity, not set complexity.'
AS
WITH latest_inv AS (
    SELECT set_num, MAX(version) AS max_ver
    FROM {CATALOG}.{SCHEMA}.inventories
    GROUP BY set_num
),
latest_inv_id AS (
    SELECT i.set_num, i.id AS inventory_id
    FROM {CATALOG}.{SCHEMA}.inventories i
    JOIN latest_inv l ON i.set_num = l.set_num AND i.version = l.max_ver
),
fig_counts AS (
    SELECT li.set_num, COALESCE(SUM(im.quantity), 0) AS total_figures
    FROM latest_inv_id li
    LEFT JOIN {CATALOG}.{SCHEMA}.inventory_minifigs im
        ON li.inventory_id = im.inventory_id
    GROUP BY li.set_num
),
part_counts AS (
    SELECT li.set_num, COUNT(*) AS non_spare_parts
    FROM latest_inv_id li
    JOIN {CATALOG}.{SCHEMA}.inventory_parts ip
        ON li.inventory_id = ip.inventory_id
       AND ip.is_spare = false
    GROUP BY li.set_num
)
SELECT
    f.set_num,
    f.total_figures,
    p.non_spare_parts,
    ROUND(f.total_figures / NULLIF(p.non_spare_parts, 0), 6) AS figure_density
FROM fig_counts f
JOIN part_counts p ON f.set_num = p.set_num
""")
print(f"  ✓ {CATALOG}.{SCHEMA}.figure_density")

# COMMAND ----------

# MAGIC %md ### 5 — Verify

# COMMAND ----------

print(f"Objects in {CATALOG}.{SCHEMA}:")
for row in spark.sql(f"SHOW TABLES IN {CATALOG}.{SCHEMA}").collect():
    kind = "VIEW" if row.isTemporary else "TABLE"
    print(f"  {row.tableName:35s}  {kind}")

print("\nSample — set_complexity_score (top 10 by score):")
display(
    spark.table(f"{CATALOG}.{SCHEMA}.set_complexity_score")
    .join(
        spark.table(f"{CATALOG}.{SCHEMA}.sets").select("set_num", "name"),
        "set_num"
    )
    .orderBy("set_complexity_score", ascending=False)
    .limit(10)
)

# COMMAND ----------

# MAGIC %md
# MAGIC **Setup complete.**
# MAGIC
# MAGIC `lucasbruand_catalog.brickvault` is now fully annotated with semantic metadata.
# MAGIC Genie Code can navigate this catalog intelligently without being given
# MAGIC explicit schema guidance.
# MAGIC
# MAGIC Proceed to record the demo session as described in `SPECS/SPEC.md`.
