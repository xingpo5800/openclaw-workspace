#!/bin/bash
# Tavily search via curl (bypasses Python SSL issues)
source ~/.openclaw/.env 2>/dev/null
QUERY="$1"
MAX="${2:-5}"

curl -s -X POST "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"$QUERY\",\"max_results\":$MAX}" | \
  python3 -c "
import json,sys
d = json.load(sys.stdin)
print(f'查询: {d[\"query\"]}')
print(f'耗时: {d[\"response_time\"]}s')
print('---')
for r in d.get('results', []):
    print(f'[{r[\"score\"]:.2f}] {r[\"title\"]}')
    print(f'URL: {r[\"url\"]}')
    print(f'摘要: {r[\"content\"][:100]}...')
    print()
if d.get('answer'):
    print(f'答案: {d[\"answer\"]}')
"
