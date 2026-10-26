#!/usr/bin/env bash
# End-to-end check: register -> verify -> admin -> seed problem -> submit 4 programs -> poll verdicts.
# Usage (from the repo root, with `docker compose up` running):  bash scripts/e2e_submit.sh
set -euo pipefail

A=http://localhost:8001/api/v1/auth
P=http://localhost:8002/api/v1
EMAIL="e2e$RANDOM@example.com"
PASS="password123"
json() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

echo "== register + verify $EMAIL"
curl -sf -o /dev/null -X POST $A/register -H 'Content-Type: application/json' -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}"
OTP=$(docker compose logs auth-service | grep "To: $EMAIL" | grep -oE '[0-9]{6}$' | tail -1)
curl -sf -o /dev/null -X POST $A/verify-otp -H 'Content-Type: application/json' -d "{\"email\":\"$EMAIL\",\"otp\":\"$OTP\"}"
docker compose exec -T postgres psql -U postgres -d auth -qc "UPDATE users SET role='admin' WHERE email='$EMAIL';"
TOKEN=$(curl -sf -X POST $A/login -H 'Content-Type: application/json' -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | json '["access_token"]')

echo "== seed problem"
PID=$(docker compose exec -T postgres psql -U postgres -d problems -tAq < problem-service/sample_quey.sql | head -1)
echo "problem_id=$PID"

submit() {  # $1=label $2=language $3=source
  local body
  body=$(python3 -c 'import json,sys; print(json.dumps({"problem_id": int(sys.argv[1]), "language": sys.argv[2], "source_code": sys.argv[3]}))' "$PID" "$2" "$3")
  local sid
  sid=$(curl -sf -X POST $P/submissions -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d "$body" | json '["submission_id"]')
  for _ in $(seq 1 30); do
    local r
    r=$(curl -sf $P/submissions/$sid -H "Authorization: Bearer $TOKEN")
    local status
    status=$(echo "$r" | json '["status"]')
    if [[ "$status" == "completed" || "$status" == "failed" ]]; then
      echo "$1 -> $(echo "$r" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("%s  %s/%s  %sms  %sKB  %s" % (d["verdict"], d["passed_count"], d["total_count"], d["runtime_ms"], d["memory_kb"], (d["error_output"] or "")[:60]))')"
      return
    fi
    sleep 1
  done
  echo "$1 -> still $status after 30s (is ai-service running? docker compose logs ai-service)"
}

echo "== submissions (expected verdict on the left)"
submit "Accepted          (python)" python $'a,b=map(int,input().split())\nprint(a+b)'
submit "Accepted          (cpp)   " cpp $'#include <iostream>\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b;}'
submit "Wrong Answer      (python)" python $'a,b=map(int,input().split())\nprint(a-b)'
submit "Compilation Error (cpp)   " cpp 'int main( {'
submit "Time Limit Exceeded       " python 'while True: pass'
