#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Single-machine development only. Bind all services to loopback.
export PATH="/opt/homebrew/opt/postgresql@15/bin:/opt/homebrew/bin:$PATH"
for tool in node npm initdb pg_ctl createdb ffmpeg tesseract; do
  command -v "$tool" >/dev/null || { echo "Missing prerequisite: $tool. See README.md."; exit 1; }
done
if command -v python3.12 >/dev/null; then PYTHON_BIN=python3.12
elif [[ -x /opt/anaconda3/bin/python ]]; then PYTHON_BIN=/opt/anaconda3/bin/python
else PYTHON_BIN=python3; fi
"$PYTHON_BIN" -c 'import sys; assert (3,10) <= sys.version_info[:2] <= (3,12), "Use Python 3.10–3.12 for the pinned inference dependencies"'
mkdir -p .data
if [[ ! -f .env.local ]]; then
node --input-type=module <<'JS'
import fs from 'node:fs';import crypto from 'node:crypto';
const secret=()=>crypto.randomBytes(32).toString('hex');
fs.writeFileSync('.env.local',`DATABASE_URL=postgres://homeatlas:homeatlas@127.0.0.1:54329/homeatlas\nBETTER_AUTH_URL=http://localhost:3000\nBETTER_AUTH_SECRET=${secret()}\nWORKER_KEY=${secret()}\nWORKER_URL=http://127.0.0.1:8001\nSTORAGE_ROOT=.data/storage\nGENERATION_MODEL=qwen3-vl:4b-instruct\nALLOW_LOCAL_MAIL=true\n`,{mode:0o600});
JS
fi
if [[ ! -f .data/postgres/PG_VERSION ]]; then initdb -D .data/postgres -U homeatlas -A trust --encoding=UTF8 --locale=C; fi
if ! pg_ctl -D .data/postgres status >/dev/null 2>&1; then
 pg_ctl -D .data/postgres -l .data/postgres.log -o '-p 54329 -h 127.0.0.1 -k /tmp' start
fi
if ! psql -h 127.0.0.1 -p 54329 -U homeatlas -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='homeatlas'" | grep -q 1; then
 createdb -h 127.0.0.1 -p 54329 -U homeatlas homeatlas
fi
npm ci
if [[ ! -x worker/.venv/bin/python ]]; then "$PYTHON_BIN" -m venv worker/.venv; fi
worker/.venv/bin/python -m pip install -r worker/requirements.lock.txt
node --env-file=.env.local --import tsx scripts/backend-migrate.ts
# Download weights explicitly with scripts/models.sh for neural inference.
WORKER_PID=""
if ! node -e "fetch('http://127.0.0.1:8001/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"; then
 worker/.venv/bin/python -m uvicorn worker.app:app --host 127.0.0.1 --port 8001 >.data/worker.log 2>&1 &
 WORKER_PID=$!
fi
trap 'if [[ -n "$WORKER_PID" ]]; then kill "$WORKER_PID" 2>/dev/null || true; fi' EXIT INT TERM
if node -e "fetch('http://localhost:3000/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"; then
 printf 'HomeAtlas is already healthy at http://localhost:3000\n'
else
 npm run dev
fi
