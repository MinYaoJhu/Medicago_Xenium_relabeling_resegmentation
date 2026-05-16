#!/usr/bin/env bash
set -euo pipefail

# =========================
# CONFIG (UPDATE FOR THIS RUN)
# =========================
PANEL="/home/myj23/myj23/Xenium/subset_panel/corrected_panel_json/Sm_50_add-on_rhizobia_50g_gene_panel_Mt_50_standalone_base_corrected.json"
RAW_DIR="/home/myj23/myj23/Xenium/raw_outputs/rhizobia_50+50"

# A dedicated run folder under your relabeled directory (keeps runs clean & reproducible)
RUN_TAG="relabel_20260302"
OUT_ROOT="/home/myj23/myj23/Xenium/relabeled/rhizobia_50+50/${RUN_TAG}"
LOG_DIR="${OUT_ROOT}/logs"

CORES=12
MEM=24

# Samples must match the __XEN-???__ substring in the raw bundle folder name
SAMPLES=("XEN-158A" "XEN-158B" "XEN-158C" "XEN-158D")

timestamp(){ date +"%Y-%m-%d %H:%M:%S"; }

# =========================
# PRECHECKS
# =========================
command -v xeniumranger >/dev/null || { echo "[ERROR] xeniumranger not found in PATH"; exit 1; }
command -v jq >/dev/null || { echo "[ERROR] jq not found"; exit 1; }
command -v sha256sum >/dev/null || { echo "[ERROR] sha256sum not found"; exit 1; }

[[ -f "$PANEL" ]] || { echo "[ERROR] Panel JSON not found: $PANEL"; exit 1; }
[[ -d "$RAW_DIR" ]] || { echo "[ERROR] Raw dir not found: $RAW_DIR"; exit 1; }

mkdir -p "$OUT_ROOT" "$LOG_DIR"

# Verify checksum is correct (abort if not)
NEWCHK=$(jq -j -c '.payload' "$PANEL" | sha256sum | awk '{print $1}')
INFILE=$(jq -r '.metadata.sha256_checksum // empty' "$PANEL")
if [[ -z "${INFILE:-}" ]]; then
  echo "[ERROR] Panel JSON missing .metadata.sha256_checksum. Do NOT run relabel."
  echo "  PANEL:    $PANEL"
  exit 1
fi
if [[ "$NEWCHK" != "$INFILE" ]]; then
  echo "[ERROR] Panel checksum mismatch. Do NOT run relabel."
  echo "  PANEL:    $PANEL"
  echo "  computed: $NEWCHK"
  echo "  in-file : $INFILE"
  exit 1
fi

echo "[$(timestamp)] ✅ Panel checksum OK"
echo "[$(timestamp)] PANEL:    $PANEL"
echo "[$(timestamp)] RAW_DIR:  $RAW_DIR"
echo "[$(timestamp)] OUT_ROOT: $OUT_ROOT"
echo

# =========================
# RUN RELABEL PER SAMPLE
# =========================
for SAMPLE in "${SAMPLES[@]}"; do
  RAW="$(ls -d "$RAW_DIR"/*"__${SAMPLE}__"* 2>/dev/null | head -n 1 || true)"

  if [[ -z "${RAW:-}" || ! -d "$RAW" ]]; then
    echo "[$(timestamp)] [ERROR] Could not find raw bundle for $SAMPLE under $RAW_DIR"
    echo
    continue
  fi

  # Minimal expected file check (same as previous run)
  if [[ ! -f "$RAW/experiment.xenium" ]]; then
    echo "[$(timestamp)] [SKIP] $SAMPLE — missing $RAW/experiment.xenium (not a Xenium bundle?)"
    echo
    continue
  fi

  OUT_ID="${SAMPLE}_${RUN_TAG}"
  DEST_DIR="$OUT_ROOT/$OUT_ID"
  LOGFILE="$LOG_DIR/${OUT_ID}.log"

  # Skip if already completed
  if [[ -d "$DEST_DIR/outs" ]]; then
    echo "[$(timestamp)] [SKIP] $SAMPLE — already exists: $DEST_DIR/outs"
    echo
    continue
  fi

  echo "[$(timestamp)] [BEGIN] $SAMPLE"
  echo "  RAW:  $RAW"
  echo "  OUT:  $DEST_DIR"
  echo "  LOG:  $LOGFILE"

  (
    cd "$OUT_ROOT"
    xeniumranger relabel \
      --id="$OUT_ID" \
      --xenium-bundle="$RAW" \
      --panel="$PANEL" \
      --localcores="$CORES" \
      --localmem="$MEM" \
      2>&1 | tee "$LOGFILE"
  )

  # Provenance: save the exact panel used
  if [[ -d "$DEST_DIR" ]]; then
    mkdir -p "$DEST_DIR/_panel_used"
    cp "$PANEL" "$DEST_DIR/_panel_used/gene_panel.json"
  fi

  echo "[$(timestamp)] [DONE] $SAMPLE → $DEST_DIR/outs"
  echo
done

echo "[$(timestamp)] ✅ rhizobia_50+50 relabel batch complete."
