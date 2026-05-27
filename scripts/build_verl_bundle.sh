#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

SCAN_ROOT="${1:-${REPO_ROOT}/results/used_molclaw_accepted_hit_0518}"
SFT_DIR="${2:-${SCAN_ROOT}/sft_outputs}"
OUT_DIR="${3:-${REPO_ROOT}/exports/mol_pipeline_to_verl_bundle_v0.1}"

python pipeline/postprocess/export_verl_training_bundle.py \
  --scan-output-root "${SCAN_ROOT}" \
  --sft-output-dir "${SFT_DIR}" \
  --results-root "${REPO_ROOT}/results" \
  --output-dir "${OUT_DIR}" \
  --include-kg-if-present \
  --include-raw-samples 20

python pipeline/postprocess/validate_verl_training_bundle.py \
  --bundle-dir "${OUT_DIR}"

tar -czf "${OUT_DIR}.tar.gz" -C "$(dirname "${OUT_DIR}")" "$(basename "${OUT_DIR}")"
echo "Wrote ${OUT_DIR}.tar.gz"
