#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
NOTEBOOK="$PROJECT_DIR/notebook.py"
WORKER_NAME="private-notebook"

# ── Check prerequisites ──────────────────────────────────────────────
if ! command -v npx &>/dev/null; then
  echo "Error: npx not found. Install Node.js first." >&2
  exit 1
fi

if ! command -v uv &>/dev/null; then
  echo "Error: uv not found. Install uv first." >&2
  exit 1
fi

# ── Read or prompt for password ───────────────────────────────────────
if [[ -f "$PROJECT_DIR/.env" ]]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.env"
fi

if [[ -z "${NOTEBOOK_PASSWORD:-}" ]]; then
  echo "Set NOTEBOOK_PASSWORD in .env or as an env var."
  echo "Example: echo 'NOTEBOOK_PASSWORD=mysecret' > .env"
  exit 1
fi

echo "==> Exporting notebook to WASM..."
uv run marimo export html-wasm "$NOTEBOOK" \
  -o "$DIST_DIR" \
  --mode run \
  --include-cloudflare \
  --force \
  --no-sandbox

# ── Patch wrangler.jsonc with correct worker name and asset path ──────
cat > "$DIST_DIR/../wrangler.jsonc" <<JSONC
{
  "name": "$WORKER_NAME",
  "main": "index.js",
  "compatibility_date": "2025-01-01",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS",
    "run_worker_first": true
  }
}
JSONC

# ── Write index.js with basic auth ────────────────────────────────────
cat > "$DIST_DIR/../index.js" <<'WORKER'
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/health")) {
      return new Response(JSON.stringify({ made: "with marimo" }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // ── Basic auth check ──
    const auth = request.headers.get("Authorization");
    if (!auth || !auth.startsWith("Basic ")) {
      return new Response("Unauthorized", {
        status: 401,
        headers: { "WWW-Authenticate": 'Basic realm="Notebook"' },
      });
    }

    const decoded = atob(auth.slice(6));
    const password = decoded.includes(":") ? decoded.split(":").slice(1).join(":") : decoded;

    if (password !== env.NOTEBOOK_PASSWORD) {
      return new Response("Forbidden", { status: 403 });
    }

    return env.ASSETS.fetch(request);
  },
};
WORKER

echo "==> Deploying to Cloudflare Workers..."
npx wrangler deploy --cwd "$PROJECT_DIR"

echo "==> Setting password secret..."
echo "$NOTEBOOK_PASSWORD" | npx wrangler secret put NOTEBOOK_PASSWORD --cwd "$PROJECT_DIR"

echo ""
echo "Done! Your notebook is live at:"
echo "  https://$WORKER_NAME.<your-subdomain>.workers.dev"
echo ""
echo "Log in with any username and the password from .env."
