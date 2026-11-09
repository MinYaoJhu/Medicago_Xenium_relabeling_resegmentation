# Medicago Xenium Relabeling and Resegmentation

<p align="center">
  <img src="assets/workflow.svg" width="100%" alt="Workflow: raw Xenium bundles are relabeled with a corrected gene panel using xeniumranger relabel, then H&amp;E-derived cell masks, nuclei and an H&amp;E-to-Xenium transform are imported with xeniumranger import-segmentation to produce resegmented outputs"/>
</p>

## Overview

This repository provides the analysis pipelines for transcript relabeling and cell segmentation used in:

**“4D spatial transcriptomics reveals nodule identity emerges through stacked parallel developmental programs”**  


This repository documents batch scripts used to process Medicago Xenium datasets through two main stages:

1. **Relabeling** Xenium raw output bundles with corrected or reduced gene-panel JSON files by using `xeniumranger relabel`.
2. **Resegmentation / H&E cell-mask import** by using `xeniumranger import-segmentation` with H&E-derived cell masks, nuclei from the relabeled Xenium bundle, and an H&E-to-Xenium coordinate transform matrix.

The scripts are intentionally organized by analysis type and gene-panel/sample group so each batch can be rerun independently.

## Repository folder structure

```text
.
├── README.md
├── LICENSE
├── assets/
│   ├── workflow.svg
│   └── make_workflow.py      # reproducible figure generator
├── relabeling/
│   ├── Mt_50_gene_panel/
│   │   └── run_relabel_50g.sh
│   ├── Mt_350+55_gene_panel/
│   │   └── run_relabel_405.sh
│   ├── Mt_50+rhizobia_50_gene_panel/
│   │   └── run_relabel_rhizobia_50+50.sh
│   └── Mt_350+rhizobia_50_gene_panel/
│       └── run_relabel_rhizobia_50+380_focused_panel.sh
└── resegmentation/
    ├── HnE_Mt_350+55_gene_panel/
    │   └── run_import_HE_405.sh
    ├── HnE_Mt_50+rhizobia_50_gene_panel/
    │   └── run_import_HE_rhizobia_50plus50_20260312.sh
    └── HnE_Mt_350+rhizobia_50_gene_panel/
        └── run_import_HE_rhizobia_50plus380_400gene_20260312.sh
```

## Analysis workflow overview

```text
Raw Xenium bundle(s)
        │
        ▼
Relabeling scripts
xeniumranger relabel
        │
        ├── Uses corrected / subset gene-panel JSON
        ├── Writes relabeled Xenium output folders
        └── Saves per-sample logs
        │
        ▼
Resegmentation scripts
xeniumranger import-segmentation
        │
        ├── Uses relabeled bundle outs/ as --xenium-bundle
        ├── Uses cells.zarr.zip from the relabeled bundle as nuclei
        ├── Uses H&E-derived cell mask TIFF as cells
        ├── Uses matrix.csv as coordinate transform
        └── Writes resegmented Xenium output folders and logs
```

## General requirements

These scripts are Bash scripts and assume they are run on the processing system where the referenced Xenium data directories exist.

Required command-line tools:

- `bash`
- `xeniumranger`
- `jq`
- `sha256sum` for most relabeling scripts
- standard Unix tools such as `find`, `sed`, `awk`, `sort`, `tee`, and `mkdir`

Resource settings used across the scripts:

- `CORES=12`
- `MEM=24`

Before running, point the scripts to your data. Every path is built from one setting, `XENIUM_ROOT` (default placeholder: `/path/to/Xenium`), and each individual path, `CORES` and `MEM` can also be overridden from the environment without editing the script:

```bash
XENIUM_ROOT=/data/my_xenium_project bash relabeling/Mt_50_gene_panel/run_relabel_50g.sh
CORES=24 MEM=64 XENIUM_ROOT=/data/my_xenium_project bash relabeling/Mt_50_gene_panel/run_relabel_50g.sh
```

The folder layout expected under `XENIUM_ROOT` (`raw_outputs/`, `subset_panel/`, `relabeled/`, `inputs/`, `segmentation_output/`) is shown in each script's configuration block.

## Relabeling scripts

Relabeling scripts use `xeniumranger relabel` to replace or subset the panel metadata of raw Xenium bundles. In general, each script:

1. Defines a panel JSON, raw bundle directory, output root, logs directory, compute resources, and sample list or bundle-discovery rule.
2. Verifies required tools and input paths.
3. Optionally verifies the panel JSON checksum by comparing `.metadata.sha256_checksum` against a checksum computed from `.payload`.
4. Locates each raw Xenium bundle by sample ID.
5. Skips samples whose output already contains an `outs/` directory.
6. Runs `xeniumranger relabel` and writes a per-sample log.
7. Copies the exact panel JSON used into `_panel_used/gene_panel.json` for provenance in most relabeling batches.


## Resegmentation / H&E import scripts

Resegmentation scripts use `xeniumranger import-segmentation` to import externally generated H&E cell masks into relabeled Xenium bundles. In general, each script:

1. Defines the relabeled Xenium output root, expected output suffix, H&E mask root, H&E transformation matrix root, output root, log directory, and compute settings.
2. Auto-discovers samples from relabeled output folders.
3. For each sample, locates:
   - relabeled bundle `outs/` directory,
   - nuclei file: `cells.zarr.zip` from the relabeled bundle,
   - H&E cell mask: `H&E_<sample>.ome_mask.tif`,
   - coordinate transform matrix: `H&E_<sample>_alignment_files/matrix.csv`.
4. Skips samples with missing required inputs.
5. Skips existing outputs unless `FORCE=1` is set in the environment.
6. Runs `xeniumranger import-segmentation` with `--units=pixels` and `--expansion-distance=0`.
7. Writes per-sample logs and reports run/skip counts.

## How to run

Run scripts from the repository root or from any location by passing the script path to Bash:

```bash
bash relabeling/Mt_50_gene_panel/run_relabel_50g.sh
bash relabeling/Mt_350+55_gene_panel/run_relabel_405.sh
bash relabeling/Mt_50+rhizobia_50_gene_panel/run_relabel_rhizobia_50+50.sh
bash relabeling/Mt_350+rhizobia_50_gene_panel/run_relabel_rhizobia_50+380_focused_panel.sh

bash resegmentation/HnE_Mt_350+55_gene_panel/run_import_HE_405.sh
bash resegmentation/HnE_Mt_50+rhizobia_50_gene_panel/run_import_HE_rhizobia_50plus50_20260312.sh
bash resegmentation/HnE_Mt_350+rhizobia_50_gene_panel/run_import_HE_rhizobia_50plus380_400gene_20260312.sh
```

To force a resegmentation rerun and overwrite an existing output folder, set `FORCE=1` for the relevant import script:

```bash
FORCE=1 bash resegmentation/HnE_Mt_50+rhizobia_50_gene_panel/run_import_HE_rhizobia_50plus50_20260312.sh
```

---

## Dependencies

- Xenium Ranger

---

## Contact

Min-Yao Jhu  
Donald Danforth Plant Science Center  
Email: [MJhu@danforthcenter.org](mailto:MJhu@danforthcenter.org)