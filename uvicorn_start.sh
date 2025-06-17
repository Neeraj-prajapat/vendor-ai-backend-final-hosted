#!/usr/bin/env bash
export DATABASE_URL="postgresql://postgres:postgresql@localhost/your_dbname"
export PERPLEXITY_API_KEY="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"
# Optionally set NVD_API_KEY if you have one:
# export NVD_API_KEY="your_nvd_api_key"

uvicorn app.main:app --host 0.0.0.0 --port 8000
