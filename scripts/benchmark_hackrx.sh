#!/bin/bash
# Benchmark script for /hackrx/run endpoint
# Usage: ./benchmark_hackrx.sh [BASE_URL]

BASE_URL="${1:-http://127.0.0.1:5000}"
TOKEN="fd4d7c6b3d2f4441c504368af8eafd59025b77053a8123fd9946501c5ae23612"

JSON_BODY='{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
    "questions": [
        "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
        "What is the waiting period for pre-existing diseases (PED) to be covered?",
        "Does this policy cover maternity expenses, and what are the conditions?",
        "What is the waiting period for cataract surgery?",
        "Are the medical expenses for an organ donor covered under this policy?",
        "What is the No Claim Discount (NCD) offered in this policy?",
        "Is there a benefit for preventive health check-ups?",
        "How does the policy define a 'Hospital'?",
        "What is the extent of coverage for AYUSH treatments?",
        "Are there any sub-limits on room rent and ICU charges for Plan A?"
    ]
}'

echo "Benchmarking $BASE_URL/hackrx/run ..."

time curl -s -w '\nHTTP_STATUS:%{http_code}\n' -X POST "$BASE_URL/hackrx/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "$JSON_BODY" | tee response.json

echo "\n--- Response saved to response.json ---"
