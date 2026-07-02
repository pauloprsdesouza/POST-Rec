#!/usr/bin/env bash
# Create an Evolution API WhatsApp instance and pair it via QR code or pairing code.
#
# Usage:
#   ./scripts/evolution_pair.sh                          # instance from .env or "postrec"
#   ./scripts/evolution_pair.sh my-instance              # custom instance name
#   ./scripts/evolution_pair.sh --production postrec    # production (auto-uses internal API on VPS)
#   ./scripts/evolution_pair.sh --phone 5579999999999 postrec
#
# Options:
#   --production     Public Evolution URL (on VPS, API calls use internal Docker network)
#   --url URL        Evolution API base URL (no trailing slash)
#   --key KEY        Global API key (apikey header)
#   --phone NUMBER   Pair via WhatsApp linking code (country code, no +) instead of QR image
#   --fresh          Delete and recreate instance if not connected (default)
#   --no-fresh       Keep existing instance session (may have stale invalid QR)
#   --qr-file PATH   Where to save the QR PNG (default: /tmp/evolution-INSTANCE-qr.png)
#   --skip-create    Skip POST /instance/create (instance must already exist)
#   --no-wait        Fetch QR once and exit (do not poll for connection)
#   -h, --help       Show help

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DOMAIN="${DOMAIN:-paulorobertosouza.com.br}"
EVO_URL="${EVO_URL:-}"
EVO_KEY="${EVO_KEY:-}"
INSTANCE="${EVOLUTION_INSTANCE_NAME:-postrec}"
QR_FILE=""
PHONE=""
SKIP_CREATE=false
NO_WAIT=false
USE_PRODUCTION=false
FRESH=true
USE_INTERNAL=false
EVOLUTION_CONTAINER="${EVOLUTION_CONTAINER:-post-rec-evolution-api-1}"
DOCKER_NETWORK="${DOCKER_NETWORK:-post-rec_default}"

usage() {
  sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
}

load_dotenv() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  set -a
  # shellcheck disable=SC1090
  source <(grep -E '^(EVOLUTION_API_URL|EVOLUTION_API_KEY|EVOLUTION_INSTANCE_NAME)=' "$file" | sed 's/\r$//')
  set +a
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --production) USE_PRODUCTION=true; shift ;;
    --url) EVO_URL="${2:?--url requires a value}"; shift 2 ;;
    --key) EVO_KEY="${2:?--key requires a value}"; shift 2 ;;
    --phone) PHONE="${2:?--phone requires a value}"; shift 2 ;;
    --qr-file) QR_FILE="${2:?--qr-file requires a value}"; shift 2 ;;
    --skip-create) SKIP_CREATE=true; shift ;;
    --no-wait) NO_WAIT=true; shift ;;
    --fresh) FRESH=true; shift ;;
    --no-fresh) FRESH=false; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    *) INSTANCE="$1"; shift ;;
  esac
done

load_dotenv ".env"
load_dotenv ".env.local"

if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$EVOLUTION_CONTAINER"; then
  USE_INTERNAL=true
fi

if $USE_PRODUCTION; then
  PUBLIC_URL="https://${DOMAIN}/evolution"
  EVO_URL="${EVO_URL:-$PUBLIC_URL}"
else
  PUBLIC_URL="${EVO_URL:-}"
fi
EVO_URL="${EVO_URL:-${EVOLUTION_API_URL:-http://localhost:8080}}"
EVO_KEY="${EVO_KEY:-${EVOLUTION_API_KEY:-dev-evolution-api-key}}"
QR_FILE="${QR_FILE:-/tmp/evolution-${INSTANCE}-qr.png}"

EVO_URL="${EVO_URL%/}"
INTERNAL_URL="http://${EVOLUTION_CONTAINER}:8080"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required command not found: $1" >&2
    exit 1
  }
}

require_cmd python3

api_curl() {
  if $USE_INTERNAL; then
    require_cmd docker
    docker run --rm --network "$DOCKER_NETWORK" curlimages/curl:8.5.0 -s "$@"
  else
    require_cmd curl
    curl -fsS "$@"
  fi
}

api_url() {
  if $USE_INTERNAL; then
    echo "${INTERNAL_URL}$1"
  else
    echo "${EVO_URL}$1"
  fi
}

api_get() {
  api_curl -H "apikey: ${EVO_KEY}" "$(api_url "$1")"
}

api_post_json() {
  api_curl -X POST -H "apikey: ${EVO_KEY}" -H "Content-Type: application/json" \
    -d "$2" "$(api_url "$1")"
}

api_delete() {
  api_curl -X DELETE -H "apikey: ${EVO_KEY}" "$(api_url "$1")" || true
}

wait_for_api() {
  local deadline=$((SECONDS + 120))
  echo "Waiting for Evolution API..."
  if $USE_INTERNAL; then
    echo "  (internal: ${INTERNAL_URL})"
  else
    echo "  (url: ${EVO_URL})"
  fi
  while (( SECONDS < deadline )); do
    if api_curl -H "apikey: ${EVO_KEY}" "$(api_url /)" >/dev/null 2>&1; then
      echo "Evolution API is ready."
      return 0
    fi
    sleep 3
  done
  echo "Evolution API did not become ready within 120s." >&2
  exit 1
}

parse_instances_json() {
  local list="$1"
  INSTANCE_LIST="$list" INSTANCE_NAME="$INSTANCE" python3 - <<'PY'
import json, os, sys
raw = os.environ.get("INSTANCE_LIST", "[]")
name = os.environ.get("INSTANCE_NAME", "")
try:
    data = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(1)
if isinstance(data, list):
    items = data
elif isinstance(data, dict):
    items = data.get("instances") or data.get("data") or []
else:
    items = []
for item in items:
    if not isinstance(item, dict):
        continue
    n = str(item.get("name") or item.get("instanceName") or "")
    if n == name:
        sys.exit(0)
sys.exit(1)
PY
}

instance_exists() {
  local list
  list="$(api_get "/instance/fetchInstances" 2>/dev/null || echo "[]")"
  parse_instances_json "$list"
}

connection_state() {
  api_get "/instance/connectionState/${INSTANCE}" 2>/dev/null \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print((d.get('instance') or d).get('state',''))" \
    || echo ""
}

reset_instance() {
  echo "Resetting instance '${INSTANCE}' (logout + delete)..."
  api_delete "/instance/logout/${INSTANCE}"
  sleep 1
  api_delete "/instance/delete/${INSTANCE}"
  sleep 2
}

create_instance() {
  echo "Creating instance '${INSTANCE}'..."
  local response status
  if $USE_INTERNAL; then
    response="$(api_curl -w '\n%{http_code}' -X POST -H "apikey: ${EVO_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"instanceName\":\"${INSTANCE}\",\"integration\":\"WHATSAPP-BAILEYS\",\"qrcode\":true}" \
      "$(api_url /instance/create)")"
  else
    response="$(curl -sS -w '\n%{http_code}' -X POST -H "apikey: ${EVO_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"instanceName\":\"${INSTANCE}\",\"integration\":\"WHATSAPP-BAILEYS\",\"qrcode\":true}" \
      "${EVO_URL}/instance/create")"
  fi
  status="${response##*$'\n'}"
  response="${response%$'\n'*}"
  if [[ "$status" == "403" ]] && echo "$response" | grep -qi 'already in use'; then
    echo "Instance '${INSTANCE}' already exists."
    echo "$response"
    return 0
  fi
  if [[ "$status" -ge 200 && "$status" -lt 300 ]]; then
    echo "Instance '${INSTANCE}' created."
    echo "$response"
    return 0
  fi
  echo "Failed to create instance (HTTP ${status}):" >&2
  echo "$response" >&2
  exit 1
}

save_qr_png() {
  local connect_json="$1"
  CONNECT_JSON="$connect_json" QR_FILE="$QR_FILE" python3 - <<'PY'
import base64, json, os, re, sys

def find_base64(obj):
    if not isinstance(obj, dict):
        return None
    q = obj.get("qrcode")
    if isinstance(q, dict) and q.get("base64"):
        return q["base64"]
    if obj.get("base64"):
        return obj["base64"]
    resp = obj.get("response")
    if isinstance(resp, dict):
        hit = find_base64(resp)
        if hit:
            return hit
    return None

raw = os.environ.get("CONNECT_JSON", "")
out = os.environ["QR_FILE"]
try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"Invalid JSON: {exc}", file=sys.stderr)
    sys.exit(1)

b64 = find_base64(data)
if not b64:
    print("No QR image in response.", file=sys.stderr)
    print(json.dumps(data, indent=2)[:1200], file=sys.stderr)
    sys.exit(2)

b64 = re.sub(r"^data:image/[^;]+;base64,", "", b64)
with open(out, "wb") as fh:
    fh.write(base64.b64decode(b64))
print(out)
PY
}

show_pairing_code() {
  local connect_json="$1"
  CONNECT_JSON="$connect_json" python3 - <<'PY'
import json, os, sys

def find_code(obj):
    if not isinstance(obj, dict):
        return None
    if obj.get("pairingCode"):
        return obj["pairingCode"]
    q = obj.get("qrcode")
    if isinstance(q, dict) and q.get("pairingCode"):
        return q["pairingCode"]
    return None

data = json.loads(os.environ["CONNECT_JSON"])
code = find_code(data)
if code:
    print(code)
    sys.exit(0)
sys.exit(1)
PY
}

fetch_connect_json() {
  local path="/instance/connect/${INSTANCE}"
  if [[ -n "$PHONE" ]]; then
    path="${path}?number=${PHONE}"
  fi
  api_get "$path"
}

fetch_and_save_qr() {
  echo "Fetching QR code for '${INSTANCE}'..." >&2
  local connect_json qr_path
  connect_json="$(fetch_connect_json)"
  if pairing="$(show_pairing_code "$connect_json" 2>/dev/null)"; then
    echo ""
    echo "Pairing code (enter in WhatsApp → Linked devices → Link with phone number):"
    echo "  ${pairing}"
    echo ""
  fi
  qr_path="$(save_qr_png "$connect_json")"
  echo "$qr_path"
}

open_qr_if_possible() {
  if [[ -n "${DISPLAY:-}" ]] && command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$QR_FILE" >/dev/null 2>&1 || true
  fi
}

main() {
  echo "Evolution pair — instance: ${INSTANCE}"
  if $USE_INTERNAL; then
    echo "  API: internal Docker (${INTERNAL_URL})"
    [[ -n "${PUBLIC_URL:-}" ]] && echo "  Manager UI: ${PUBLIC_URL%/}/manager/"
  else
    echo "  API: ${EVO_URL}"
    echo "  Manager UI: ${EVO_URL}/manager/"
  fi

  wait_for_api

  local state=""
  if instance_exists; then
    state="$(connection_state)"
    echo "Instance '${INSTANCE}' exists (state: ${state:-unknown})."
    if [[ "$state" == "open" ]]; then
      echo "Already connected."
      exit 0
    fi
    if $FRESH; then
      reset_instance
      SKIP_CREATE=false
    fi
  elif $SKIP_CREATE; then
    echo "Instance '${INSTANCE}' not found and --skip-create was set." >&2
    exit 1
  fi

  if ! instance_exists; then
    if $SKIP_CREATE; then
      echo "Instance '${INSTANCE}' not found." >&2
      exit 1
    fi
    create_response="$(create_instance)"
    if [[ -z "$PHONE" ]] && echo "$create_response" | python3 -c "import json,sys; json.load(sys.stdin)" >/dev/null 2>&1; then
      if qr_path="$(save_qr_png "$create_response" 2>/dev/null)"; then
        echo ""
        echo "QR code saved from create response: ${qr_path}"
        open_qr_if_possible
        if $NO_WAIT; then
          exit 0
        fi
      fi
    fi
  elif $FRESH; then
    create_response="$(create_instance)"
    if [[ -z "$PHONE" ]] && echo "$create_response" | grep -q '"base64"'; then
      if qr_path="$(save_qr_png "$create_response" 2>/dev/null)"; then
        echo "QR code saved: ${qr_path}"
        open_qr_if_possible
      fi
    fi
  fi

  state="$(connection_state 2>/dev/null || echo "")"
  if [[ "$state" == "open" ]]; then
    echo "Instance '${INSTANCE}' is connected (state: open)."
    exit 0
  fi

  if [[ -n "$PHONE" ]]; then
    connect_json="$(fetch_connect_json)"
    if pairing="$(show_pairing_code "$connect_json")"; then
      echo ""
      echo "Enter this code in WhatsApp (Linked devices → Link with phone number):"
      echo "  ${pairing}"
      echo ""
    else
      echo "No pairing code returned. Try without --phone to use QR." >&2
      echo "$connect_json" >&2
      exit 1
    fi
  else
    qr_path="$(fetch_and_save_qr)"
    echo ""
    echo "QR code saved: ${qr_path}"
    echo "Scan within ~60 seconds (QR expires quickly)."
    echo "On your phone: WhatsApp → Settings → Linked devices → Link a device"
    if $USE_INTERNAL; then
      echo ""
      echo "Download to your PC (run on Windows):"
      echo "  scp root@${DOMAIN}:/tmp/evolution-${INSTANCE}-qr.png %USERPROFILE%\\Downloads\\"
      echo "Or use the Manager UI (recommended): https://${DOMAIN}/evolution/manager/"
    fi
    open_qr_if_possible
  fi

  if $NO_WAIT; then
    exit 0
  fi

  echo ""
  echo "Waiting for connection..."
  local poll=0
  while true; do
    state="$(connection_state 2>/dev/null || echo "")"
    case "$state" in
      open)
        echo ""
        echo "Connected! Instance '${INSTANCE}' state: open"
        echo "EVOLUTION_INSTANCE_NAME=${INSTANCE}"
        exit 0
        ;;
      close|connecting|"")
        poll=$((poll + 1))
        printf "."
        if (( poll % 12 == 0 )); then
          echo ""
          if [[ -n "$PHONE" ]]; then
            echo "Still waiting — pairing code may have expired; re-run the script."
          else
            echo "Refreshing QR (previous one expired)..."
            qr_path="$(fetch_and_save_qr || true)"
            [[ -n "${qr_path:-}" ]] && echo "New QR: ${qr_path}"
            open_qr_if_possible
          fi
        fi
        sleep 5
        ;;
      *)
        echo ""
        echo "Current state: ${state}"
        sleep 5
        ;;
    esac
  done
}

main
