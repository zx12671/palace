#!/usr/bin/env bash
set -euo pipefail

API_KEY="${GEMINI_API_KEY:-AIzaSyAcQ8NSfY39nweNalsveisI6TZuyV8U4yk}"
MODEL="gemini-3-flash-preview"
BASE_URL="https://generativelanguage.googleapis.com/v1beta"
PROMPT="回答1+1等于几，只回答数字"

echo "=== Gemini API Connectivity Test ==="
echo "Model: $MODEL"
echo ""

echo "--- Test 1: generateContent ---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${BASE_URL}/models/${MODEL}:generateContent" \
  -H "x-goog-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{
      \"parts\": [{\"text\": \"${PROMPT}\"}]
    }]
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "Status: OK ($HTTP_CODE)"
  TEXT=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
parts = data['candidates'][0]['content']['parts']
print(''.join(p.get('text', '') for p in parts))
" 2>/dev/null || echo "$BODY")
  echo "Response: $TEXT"
  TOKENS=$(echo "$BODY" | python3 -c "
import sys, json
u = json.load(sys.stdin).get('usageMetadata', {})
print(f\"prompt={u.get('promptTokenCount',0)} completion={u.get('candidatesTokenCount',0)} total={u.get('totalTokenCount',0)}\")
" 2>/dev/null || echo "N/A")
  echo "Tokens: $TOKENS"
else
  echo "Status: FAILED ($HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""
echo "--- Test 2: generateContent (thinking model) ---"
THINK_MODEL="gemini-2.5-flash"
echo "Model: $THINK_MODEL"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${BASE_URL}/models/${THINK_MODEL}:generateContent" \
  -H "x-goog-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{
      \"parts\": [{\"text\": \"9.9和9.11谁大，只回答数字\"}]
    }],
    \"generationConfig\": {
      \"thinkingConfig\": {\"thinkingBudget\": 1024}
    }
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "Status: OK ($HTTP_CODE)"
  python3 -c "
import sys, json
data = json.load(sys.stdin)
parts = data['candidates'][0]['content']['parts']
for p in parts:
    if p.get('thought'):
        print(f\"Thinking: {p.get('text', '')[:200]}...\")
    elif p.get('text'):
        print(f\"Answer: {p['text']}\")
u = data.get('usageMetadata', {})
print(f\"Tokens: prompt={u.get('promptTokenCount',0)} thinking={u.get('thoughtsTokenCount',0)} completion={u.get('candidatesTokenCount',0)} total={u.get('totalTokenCount',0)}\")
" <<< "$BODY" 2>/dev/null || echo "$BODY"
else
  echo "Status: FAILED ($HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""
echo "--- Test 3: streamGenerateContent ---"
echo -n "Streaming: "
curl -s -X POST "${BASE_URL}/models/${MODEL}:streamGenerateContent?alt=sse" \
  -H "x-goog-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{
      \"parts\": [{\"text\": \"用一句话介绍Palace多智能体决策系统\"}]
    }]
  }" | while IFS= read -r line; do
    line="${line#data: }"
    [ -z "$line" ] && continue
    echo "$line" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
    for p in parts:
        t = p.get('text', '')
        if t: print(t, end='', flush=True, file=sys.stderr)
except: pass
" 2>&1
done

echo ""
echo ""
echo "--- Test 4: list models ---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  "${BASE_URL}/models?key=${API_KEY}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "Status: OK ($HTTP_CODE)"
  python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'].replace('models/','') for m in data.get('models', []) if 'gemini' in m.get('name','').lower()]
print(f'found {len(models)} gemini models')
for m in sorted(models)[-10:]:
    print(f'  {m}')
" <<< "$BODY" 2>/dev/null || echo "$BODY"
else
  echo "Status: FAILED ($HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""
echo "=== All tests passed ==="
