#!/usr/bin/env bash
set -euo pipefail

API_KEY="${DASHSCOPE_API_KEY:-}"
if [ -z "$API_KEY" ]; then
  echo "Error: DASHSCOPE_API_KEY is required"
  exit 1
fi
GEMINI_KEY="${GEMINI_API_KEY:-}"
MODEL="qwen3-max"
BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_BASE_URL="https://generativelanguage.googleapis.com/v1beta"
PROMPT="回答1+1等于几，只回答数字"

echo "=== DashScope API Connectivity Test ==="
echo "Model: $MODEL"
echo ""

echo "--- Test 1: chat/completions ---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  --location --request POST "${BASE_URL}/chat/completions" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --data-raw "{
    \"model\": \"${MODEL}\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"${PROMPT}\"
    }],
    \"stream\": false
  }")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "Status: OK ($HTTP_CODE)"
  TEXT=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
msg = data['choices'][0]['message']
print(msg.get('content', ''))
" 2>/dev/null || echo "$BODY")
  echo "Response: $TEXT"
  TOKENS=$(echo "$BODY" | python3 -c "
import sys, json
u = json.load(sys.stdin).get('usage', {})
print(f\"prompt={u.get('prompt_tokens',0)} completion={u.get('completion_tokens',0)} total={u.get('total_tokens',0)}\")
" 2>/dev/null || echo "N/A")
  echo "Tokens: $TOKENS"
else
  echo "Status: FAILED ($HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""
echo "--- Test 2: chat/completions (stream + thinking) ---"
echo -n "Thinking: "
ANSWER=""
curl -s --location --request POST "${BASE_URL}/chat/completions" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --data-raw "{
    \"model\": \"${MODEL}\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"9.9和9.11谁大，只回答数字\"
    }],
    \"enable_thinking\": true,
    \"stream\": true,
    \"stream_options\": {\"include_usage\": true}
  }" | while IFS= read -r line; do
    line="${line#data: }"
    [ -z "$line" ] && continue
    [ "$line" = "[DONE]" ] && break
    echo "$line" | python3 -c "
import sys, json
try:
    c = json.load(sys.stdin)['choices']
    if not c: sys.exit(0)
    d = c[0].get('delta', {})
    r = d.get('reasoning_content') or ''
    t = d.get('content') or ''
    if r: print(f'R:{r}', end='', flush=True, file=sys.stderr)
    if t: print(f'A:{t}', end='', flush=True, file=sys.stderr)
except: pass
" 2>&1
done

echo ""
echo ""
echo "--- Test 3: list models ---"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  --location "${BASE_URL}/models" \
  --header "Authorization: Bearer ${API_KEY}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  COUNT=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['id'] for m in data.get('data', []) if 'qwen' in m.get('id','').lower()]
print(f'found {len(models)} qwen models')
for m in sorted(models)[-10:]:
    print(f'  {m}')
" 2>/dev/null || echo "?")
  echo "Status: OK ($HTTP_CODE)"
  echo "$COUNT"
else
  echo "Status: FAILED ($HTTP_CODE)"
  echo "$BODY"
  exit 1
fi

echo ""

# ========== Google Gemini API Tests ==========
if [ -z "$GEMINI_KEY" ]; then
  echo "=== Skipping Gemini tests (GEMINI_API_KEY not set) ==="
else
  echo "=== Google Gemini API Connectivity Test ==="
  echo "Model: $GEMINI_MODEL"
  echo ""

  echo "--- Test 4: Gemini generateContent ---"
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    --location --request POST "${GEMINI_BASE_URL}/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_KEY}" \
    --header "Content-Type: application/json" \
    --data-raw "{
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
print(''.join(p.get('text','') for p in parts))
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
  echo "--- Test 5: Gemini list models ---"
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    --location "${GEMINI_BASE_URL}/models?key=${GEMINI_KEY}")

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | sed '$d')

  if [ "$HTTP_CODE" -eq 200 ]; then
    COUNT=$(echo "$BODY" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', []) if 'gemini' in m.get('name','').lower()]
print(f'found {len(models)} gemini models')
for m in sorted(models)[-10:]:
    print(f'  {m}')
" 2>/dev/null || echo "?")
    echo "Status: OK ($HTTP_CODE)"
    echo "$COUNT"
  else
    echo "Status: FAILED ($HTTP_CODE)"
    echo "$BODY"
    exit 1
  fi
fi

echo ""
echo "=== All tests passed ==="
