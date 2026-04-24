#!/usr/bin/env bash
# =============================================================================
# BrickVault — Step 1: Download source data
# =============================================================================
# Downloads Rebrickable bulk CSV files, decompresses them, and uploads to a
# Unity Catalog Volume at /Volumes/brickvault/landing/raw/
#
# Prerequisites:
#   - Databricks CLI v0.200+ installed and configured (databricks auth login)
#   - curl, gunzip available on PATH
#   - The brickvault catalog must already exist (created by 02_catalog_setup.py)
#     OR run with --create-volume to let this script create it via CLI
#
# Usage:
#   ./01_download_data.sh
#   ./01_download_data.sh --profile my-profile
# =============================================================================

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
CATALOG="brickvault"
SCHEMA="landing"
VOLUME="raw"
VOLUME_PATH="/Volumes/${CATALOG}/${SCHEMA}/${VOLUME}"
REBRICKABLE_BASE="https://cdn.rebrickable.com/media/downloads"
DATABRICKS_PROFILE="${DATABRICKS_PROFILE:-DEFAULT}"

FILES=(
  sets
  themes
  parts
  colors
  inventories
  inventory_parts
  minifigs
  inventory_minifigs
)

# ── Parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --profile=*) DATABRICKS_PROFILE="${arg#*=}" ;;
    --profile)   shift; DATABRICKS_PROFILE="$1" ;;
  esac
done

# ── Download & upload ─────────────────────────────────────────────────────────
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading Rebrickable bulk files..."
echo "Note: if downloads fail (403), register a free account at rebrickable.com"
echo "      and export REBRICKABLE_API_KEY=<your_key>, then re-run."
echo ""

for name in "${FILES[@]}"; do
  gz_file="${name}.csv.gz"
  csv_file="${name}.csv"
  local_path="${TMP_DIR}/${csv_file}"

  echo "  ↓ ${gz_file}"

  if [[ -n "${REBRICKABLE_API_KEY:-}" ]]; then
    curl -sSfL \
      -H "Authorization: key ${REBRICKABLE_API_KEY}" \
      "${REBRICKABLE_BASE}/${gz_file}" \
      | gunzip > "${local_path}"
  else
    curl -sSfL "${REBRICKABLE_BASE}/${gz_file}" | gunzip > "${local_path}"
  fi

  echo "  ↑ uploading to ${VOLUME_PATH}/${csv_file}"
  databricks --profile "${DATABRICKS_PROFILE}" \
    fs cp "${local_path}" "dbfs:${VOLUME_PATH}/${csv_file}" \
    --overwrite 2>/dev/null \
  || databricks --profile "${DATABRICKS_PROFILE}" \
    volumes upload "${local_path}" "${VOLUME_PATH}/${csv_file}" \
    --overwrite
done

echo ""
echo "Done. All files available at ${VOLUME_PATH}"
echo "Next: run setup/02_catalog_setup.py in your Databricks workspace."
