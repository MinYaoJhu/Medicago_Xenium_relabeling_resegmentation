#!/usr/bin/env bash
set -euo pipefail

# === Config ===
XENIUM_ROOT="${XENIUM_ROOT:-/path/to/Xenium}"  # set to your Xenium data folder
ROOT="$XENIUM_ROOT"

# Relabeled Xenium outputs used as input bundles
RELABEL_ROOT="${RELABEL_ROOT:-$ROOT/relabeled/rhizobia_50+50/relabel_20260302}"
RELABEL_SUFFIX="_relabel_20260302"
BUNDLE_SUBDIR="outs"

# External segmentation inputs
MASK_ROOT="${MASK_ROOT:-$ROOT/inputs/cell_mask/selected_HE_mask}"
MATRIX_ROOT="${MATRIX_ROOT:-$ROOT/inputs/transformation_matrix/HE}"

# Outputs
OUT_ROOT="${OUT_ROOT:-$ROOT/segmentation_output/resegmentation_20260312/rhizobia_50+50}"
LOG_DIR="${LOG_DIR:-$OUT_ROOT/logs}"

CORES="${CORES:-12}"
MEM="${MEM:-24}"
RUN_SUFFIX="HE_import_rhizobia_50plus50_20260312"

# If FORCE=1, rerun and overwrite existing outputs
FORCE="${FORCE:-0}"

mkdir -p "$OUT_ROOT" "$LOG_DIR"

timestamp() { date +"%Y-%m-%d %H:%M:%S"; }

find_mask_for_sample() {
  local sample="$1"
  # Expected example:
  # H&E_XEN-158A.ome_mask.tif
  find "$MASK_ROOT" -type f -name "H&E_${sample}.ome_mask.tif" | head -n 1
}

find_matrix_for_sample() {
  local sample="$1"
  local dir="$MATRIX_ROOT/H&E_${sample}_alignment_files"
  [[ -f "$dir/matrix.csv" ]] && printf "%s\n" "$dir/matrix.csv"
}

bundle_dir_for_sample() {
  local sample="$1"
  local d="$RELABEL_ROOT/${sample}${RELABEL_SUFFIX}/${BUNDLE_SUBDIR}"
  [[ -d "$d" ]] && printf "%s\n" "$d"
}

process_one() {
  local sample="$1"

  local run_id="${sample}_${RUN_SUFFIX}"
  local out_dir="$OUT_ROOT/$run_id"
  local log_file="$LOG_DIR/${run_id}.log"

  local bundle_dir; bundle_dir="$(bundle_dir_for_sample "$sample" || true)"
  if [[ -z "${bundle_dir:-}" || ! -d "$bundle_dir" ]]; then
    printf "[$(timestamp)] [SKIP] %s — relabeled bundle not found under %s\n" "$sample" "$RELABEL_ROOT"
    return 0
  fi

  local nuclei_file="$bundle_dir/cells.zarr.zip"
  if [[ ! -f "$nuclei_file" ]]; then
    printf "[$(timestamp)] [SKIP] %s — missing nuclei file: %s\n" "$sample" "$nuclei_file"
    return 0
  fi

  local mask; mask="$(find_mask_for_sample "$sample" || true)"
  if [[ -z "${mask:-}" || ! -f "$mask" ]]; then
    printf "[$(timestamp)] [SKIP] %s — mask not found under %s\n" "$sample" "$MASK_ROOT"
    return 0
  fi

  local matrix; matrix="$(find_matrix_for_sample "$sample" || true)"
  if [[ -z "${matrix:-}" || ! -f "$matrix" ]]; then
    printf "[$(timestamp)] [SKIP] %s — alignment matrix not found under %s\n" "$sample" "$MATRIX_ROOT"
    return 0
  fi

  if [[ -d "$out_dir/outs" && "$FORCE" != "1" ]]; then
    printf "[$(timestamp)] [SKIP] %s — output exists: %s\n" "$sample" "$out_dir/outs"
    return 0
  fi

  printf "[$(timestamp)] [BEGIN] %s\n" "$sample"
  printf "  bundle: %s\n" "$bundle_dir"
  printf "  nuclei: %s\n" "$nuclei_file"
  printf "  mask  : %s\n" "$mask"
  printf "  matrix: %s\n" "$matrix"
  printf "  out   : %s\n" "$out_dir"
  printf "  log   : %s\n" "$log_file"

  rm -rf "$out_dir"

  (
    cd "$OUT_ROOT"
    xeniumranger import-segmentation \
      --id="$run_id" \
      --xenium-bundle="$bundle_dir" \
      --cells="$mask" \
      --nuclei="$nuclei_file" \
      --coordinate-transform="$matrix" \
      --units=pixels \
      --expansion-distance=0 \
      --localcores="$CORES" \
      --localmem="$MEM" \
      2>&1 | tee "$log_file"
  )

  if [[ ! -d "$out_dir/outs" ]]; then
    printf "[$(timestamp)] [ERROR] %s — missing outs: %s\n\n" "$sample" "$out_dir/outs"
    return 0
  fi

  printf "[$(timestamp)] [DONE] %s → %s\n\n" "$sample" "$out_dir/outs"
}

main() {
  printf "[$(timestamp)] === Starting H&E import-segmentation (rhizobia_50+50) ===\n"
  printf "RELABEL_ROOT: %s\n" "$RELABEL_ROOT"
  printf "MASK_ROOT   : %s\n" "$MASK_ROOT"
  printf "MATRIX_ROOT : %s\n" "$MATRIX_ROOT"
  printf "OUT_ROOT    : %s\n" "$OUT_ROOT"
  printf "LOG_DIR     : %s\n\n" "$LOG_DIR"

  command -v xeniumranger >/dev/null || { echo "[ERROR] xeniumranger not found in PATH"; exit 1; }
  command -v find >/dev/null || { echo "[ERROR] find not found"; exit 1; }

  # Auto-discover available relabeled bundles
  mapfile -t samples < <(
    find "$RELABEL_ROOT" -maxdepth 1 -type d -name "XEN-*${RELABEL_SUFFIX}" \
    | sed -E "s#.*/(XEN-[^/]+)${RELABEL_SUFFIX}#\1#" \
    | sort
  )

  if [[ ${#samples[@]} -eq 0 ]]; then
    echo "[ERROR] No relabeled sample directories found under: $RELABEL_ROOT"
    exit 1
  fi

  printf "[$(timestamp)] Found %d relabeled samples. Will run only those with mask + matrix + nuclei.\n\n" "${#samples[@]}"

  local n_run=0 n_skip=0
  for s in "${samples[@]}"; do
    local before_exists=0
    [[ -d "$OUT_ROOT/${s}_${RUN_SUFFIX}/outs" ]] && before_exists=1

    process_one "$s" || true

    if [[ $before_exists -eq 0 && -d "$OUT_ROOT/${s}_${RUN_SUFFIX}/outs" ]]; then
      n_run=$((n_run+1))
    else
      n_skip=$((n_skip+1))
    fi
  done

  printf "[$(timestamp)] ✅ import-segmentation complete. New outputs created: %d; skipped/unchanged: %d\n" "$n_run" "$n_skip"
}

main "$@"
