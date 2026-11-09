#!/usr/bin/env bash
set -euo pipefail

# ====== CONFIG ======
XENIUM_ROOT="${XENIUM_ROOT:-/path/to/Xenium}"  # set to your Xenium data folder
RAW_DIR="${RAW_DIR:-${XENIUM_ROOT}/raw_outputs/480_gene}"

PANEL_DIR="${PANEL_DIR:-${XENIUM_ROOT}/subset_panel/corrected_panel_json}"
PANEL_JSON="${PANEL_JSON:-${PANEL_DIR}/Mt_380_standalone_480_Mt_100_add-on_100_genes_panel_subset_405_minyao_corrected.json}"

OUT_ROOT="${OUT_ROOT:-${XENIUM_ROOT}/relabeled/480_gene_panel/405_gene_relabel_20260208}"
LOG_DIR="${LOG_DIR:-${OUT_ROOT}/logs}"

CORES="${CORES:-12}"
MEM="${MEM:-24}"

# Label used in output run IDs
RUN_TAG="relabel405_20260208"

# ====================

timestamp(){ date +"%Y-%m-%d %H:%M:%S"; }

mkdir -p "$OUT_ROOT" "$LOG_DIR"

# Preflight
command -v xeniumranger >/dev/null || { echo "[ERROR] xeniumranger not found in PATH"; exit 1; }
command -v jq >/dev/null || { echo "[ERROR] jq not found"; exit 1; }

[[ -f "$PANEL_JSON" ]] || { echo "[ERROR] Panel JSON not found: $PANEL_JSON"; exit 1; }

echo "[$(timestamp)] Xenium relabel (405-gene subset)"
echo "  RAW_DIR  : $RAW_DIR"
echo "  PANEL    : $PANEL_JSON"
echo "  OUT_ROOT : $OUT_ROOT"
echo "  LOG_DIR  : $LOG_DIR"
echo "  CORES/MEM: $CORES cores / $MEM GB"
echo

# Discover all raw Xenium bundles in the folder
mapfile -t BUNDLES < <(ls -d "$RAW_DIR"/output-* 2>/dev/null | sort)
if [[ ${#BUNDLES[@]} -eq 0 ]]; then
  echo "[ERROR] No bundles found under $RAW_DIR"
  exit 1
fi

echo "[$(timestamp)] Found ${#BUNDLES[@]} bundles."
echo

# Run relabel for each bundle
for RAW in "${BUNDLES[@]}"; do
  # Extract sample ID like XEN-44A from folder name (expects __XEN-44A__ pattern)
  SAMPLE="$(basename "$RAW" | sed -n 's/.*__\(XEN-[A-Za-z0-9]\+\)__.*$/\1/p')"
  if [[ -z "${SAMPLE:-}" ]]; then
    echo "[$(timestamp)] [SKIP] Could not parse sample name from: $RAW"
    continue
  fi

  OUT_ID="${SAMPLE}_${RUN_TAG}"
  DEST="${OUT_ROOT}/${OUT_ID}"
  LOGFILE="${LOG_DIR}/${OUT_ID}.log"

  echo "[$(timestamp)] [BEGIN] $SAMPLE"
  echo "  RAW: $RAW"
  echo "  OUT: $DEST"
  echo "  LOG: $LOGFILE"

  # Skip if already finished (outs exists + gene_panel.json exists)
  if [[ -d "${DEST}/outs" && -f "${DEST}/outs/gene_panel.json" ]]; then
    echo "[$(timestamp)] [SKIP] Already exists: ${DEST}/outs"
    echo
    continue
  fi

  # Clean partial output if exists
  rm -rf "$DEST"

  # Run relabel from OUT_ROOT (keeps outputs organized)
  (
    cd "$OUT_ROOT"
    xeniumranger relabel \
      --id="$OUT_ID" \
      --xenium-bundle="$RAW" \
      --panel="$PANEL_JSON" \
      --localcores="$CORES" \
      --localmem="$MEM" \
      2>&1 | tee "$LOGFILE"
  )

  # Quick post-checks
  if [[ ! -d "${DEST}/outs" ]]; then
    echo "[$(timestamp)] [ERROR] Missing outs for $SAMPLE: ${DEST}/outs" | tee -a "$LOGFILE"
    echo
    continue
  fi

  # Verify the panel metadata in the output gene_panel.json
  OUT_PANEL="${DEST}/outs/gene_panel.json"
  echo "[$(timestamp)] [CHECK] Panel metadata for $SAMPLE" | tee -a "$LOGFILE"
  jq -r '
    "panel.identity.name: \(.payload.panel.identity.name // "NA")",
    "panel.species      : \(.payload.panel.species // "NA")",
    "panel.tissue       : \(.payload.panel.tissue // "NA")"
  ' "$OUT_PANEL" | tee -a "$LOGFILE"

  # Count gene targets in the output panel (should be 405)
  NGENE="$(jq '[.payload.targets[] | select(.type.descriptor=="gene")] | length' "$OUT_PANEL")"
  echo "[$(timestamp)] [CHECK] gene targets in outs/gene_panel.json: $NGENE" | tee -a "$LOGFILE"

  if [[ "$NGENE" -ne 405 ]]; then
    echo "[$(timestamp)] [WARN] Expected 405 gene targets but saw $NGENE for $SAMPLE" | tee -a "$LOGFILE"
  fi

  echo "[$(timestamp)] [DONE] $SAMPLE"
  echo
done

echo "[$(timestamp)] ✅ Batch relabel complete (405 subset)."
echo "Outputs: $OUT_ROOT"
echo "Logs:    $LOG_DIR"
