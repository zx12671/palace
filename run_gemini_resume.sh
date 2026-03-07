#!/usr/bin/env bash
set -euo pipefail

export GEMINI_API_KEY="${GEMINI_API_KEY:-AIzaSyAcQ8NSfY39nweNalsveisI6TZuyV8U4yk}"

python3 interactive.py \
  --issue tests/fixtures/issue_resume.json \
  --model gemini \
  --outdir outputs
