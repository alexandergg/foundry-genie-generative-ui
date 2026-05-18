#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"
load_local_env

require_env WAREHOUSE_ID
require_env UC3_CATALOG
export UC3_SCHEMA="${UC3_SCHEMA:-default}"
export SQL_FILE="${SQL_FILE:-$UC3_ROOT/databricks/sql/uc3_demo_setup.sql}"
ALLOW_WAREHOUSE_START="${ALLOW_WAREHOUSE_START:-no}"

state="$(warehouse_state)"
if [[ "$state" == "STOPPED" && "$ALLOW_WAREHOUSE_START" != "yes" ]]; then
  echo "Warehouse $WAREHOUSE_ID is STOPPED. Set ALLOW_WAREHOUSE_START=yes to run SQL and allow Databricks to start it." >&2
  exit 3
fi

python3 - <<'PY'
import json, os, re, sys, time, urllib.error, urllib.request
host=os.environ['DATABRICKS_HOST'].rstrip('/')
token=os.environ.get('DATABRICKS_TOKEN')
if not token:
    import subprocess
    token=subprocess.check_output([
        'az','account','get-access-token','--resource','2ff814a6-3304-4ab8-85cb-cd0e6f879c1d','--query','accessToken','-o','tsv'
    ], text=True).strip()
warehouse=os.environ['WAREHOUSE_ID']
catalog=os.environ['UC3_CATALOG']
schema=os.environ.get('UC3_SCHEMA','default')
sql_path=os.environ.get('SQL_FILE')
with open(sql_path, encoding='utf-8') as f:
    sql=f.read()
sql=sql.replace('uc3_risk_demo', catalog).replace('analytics', schema)
statements=[s.strip() for s in re.split(r';\s*(?:\n|$)', sql) if s.strip() and not s.strip().startswith('-- Useful checks')]

def request(method, path, body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(host+path, data=data, method=method, headers={
        'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        print(e.read().decode(), file=sys.stderr)
        raise

def wait_statement(statement_id):
    while True:
        result=request('GET', f'/api/2.0/sql/statements/{statement_id}')
        state=result.get('status',{}).get('state')
        if state in {'SUCCEEDED','FAILED','CANCELED','CLOSED'}:
            return result
        time.sleep(2)

for idx, stmt in enumerate(statements, 1):
    print(f'[{idx}/{len(statements)}] {stmt.splitlines()[0][:100]}')
    created=request('POST','/api/2.0/sql/statements/', {
        'warehouse_id': warehouse,
        'statement': stmt,
        'wait_timeout': '30s',
        'on_wait_timeout': 'CONTINUE'
    })
    statement_id=created.get('statement_id')
    result=created if created.get('status',{}).get('state') in {'SUCCEEDED','FAILED','CANCELED'} else wait_statement(statement_id)
    state=result.get('status',{}).get('state')
    if state != 'SUCCEEDED':
        print(json.dumps(result, indent=2), file=sys.stderr)
        raise SystemExit(f'Statement failed: {state}')
print(f'Demo SQL loaded into {catalog}.{schema}')
PY
