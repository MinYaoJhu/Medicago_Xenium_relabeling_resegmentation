# Medicago_Xenium_relabeling_resegmentation

## Overview

This repository provides the analysis pipelines for transcript relabeling and cell segmentation used in:

**“4D Medicago spatial transcriptomics reveals primary root-associated identity upon nodule identity collapse”**  
Min-Yao Jhu *et al.*

The workflows here specifically support:
- Relabeling of Xenium transcripts across panels
- Reassignment of transcripts using **custom segmentation masks**

---

## Pipeline Overview

### 1. Transcript Relabeling Across Panels

To ensure consistency between the **50-gene pilot panel** and the **405-gene atlas panel**:

- Panel JSON files were edited to synchronize gene identifiers  

---

### 2. Cell Segmentation Strategies

We implemented three segmentation modes:

(A) Xenium nucleus-based segmentation (--expansion-distance 15) for 50 gene panel
(B) Xenium nucleus-based segmentation (--expansion-distance 5) for 405 gene panel 
(C) Cell wall–based segmentation (Cellpose)

---

### 3. Image Alignment

- Convert H&E or confocal image to pyramidal OME-TIFF 
- Align using Xenium Explorer  
- ≥25 anatomical keypoints  

---

### 4. Re-segmentation

bash 04_resegmentation.sh

Core command:

xeniumranger import-segmentation

---

## Segmentation Selection Criteria

Quantitative:
- Transcript-in-cell ratio

Qualitative:
- Visual inspection  
- Anatomical consistency  

---

## Dependencies

- Xenium Ranger  

---

## Citation

Jhu, M.-Y. *et al.* (2026)  
4D Medicago spatial transcriptomics reveals primary root-associated identity upon nodule identity collapse

---

## Contact

Min-Yao Jhu  
Email: myj23@cam.ac.uk
