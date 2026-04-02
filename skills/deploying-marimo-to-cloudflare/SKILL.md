---
name: deploying-marimo-to-cloudflare
description: Deploys a marimo notebook to Cloudflare Workers as an interactive WASM app with HTTP basic auth password protection. Use when the user wants to publish, deploy, or share a marimo notebook on Cloudflare, or protect a deployed notebook with a password.
---

# Deploying marimo to Cloudflare Workers

## Project layout (single notebook)

```
project/
├── notebook.py       # marimo notebook
├── public/           # static files (bundled into WASM export)
├── deploy.sh         # one-command deploy script
├── .env              # NOTEBOOK_PASSWORD=... (gitignored)
├── dist/             # generated output (gitignored)
├── index.js          # generated Worker (gitignored)
└── wrangler.jsonc    # generated config (gitignored)
```

For multi-notebook repos, use per-notebook naming:

```
project/
├── notebook-a.py
├── notebook-b.py
├── deploy.sh                   # accepts worker name as argument
├── .env
├── dist-{worker-name}/         # per-notebook output (gitignored)
├── index-{worker-name}.js      # per-notebook Worker (gitignored)
└── wrangler-{worker-name}.jsonc # per-notebook config (gitignored)
```

## PEP 723 inline metadata (REQUIRED for WASM)

The WASM export runs in pyodide, which needs to know which packages to install. Without inline metadata, you get `ModuleNotFoundError` for any non-stdlib package. Add a PEP 723 block at the **top** of each notebook, before `import marimo`:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas",
#     "plotly",
# ]
# ///

import marimo
```

List every non-stdlib package the notebook imports.

## Data files in WASM

`mo.notebook_location()` returns a URL in WASM, not a filesystem path. Files in `public/` are bundled automatically, but must be fetched over HTTP. **The cell must depend on `mo`** (include it in the function signature), not just the library used for reading:

```python
@app.cell
def _(mo, pd):
    import io
    from urllib.request import urlopen

    _path = str(mo.notebook_location() / "public" / "data.csv")
    if _path.startswith("http"):
        df = pd.read_csv(io.StringIO(urlopen(_path).read().decode("utf-8")))
    else:
        df = pd.read_csv(_path)
```

## wrangler.jsonc — `run_worker_first` is CRITICAL

By default, Cloudflare serves static assets directly without routing through the Worker. This means the auth check is bypassed entirely — users can cancel the browser prompt and still see the page.

The fix requires **both** `"binding": "ASSETS"` and `"run_worker_first": true`:

```jsonc
{
  "name": "my-notebook",
  "main": "index.js",
  "compatibility_date": "2025-01-01",
  "assets": {
    "directory": "./dist",
    "binding": "ASSETS",
    "run_worker_first": true
  }
}
```

- `"binding": "ASSETS"` — exposes assets via `env.ASSETS.fetch(request)` in the Worker
- `"run_worker_first": true` — forces **all** requests through the Worker's `fetch` handler before any static file is served

Without both of these, the auth Worker is decorative. See: https://developers.cloudflare.com/workers/static-assets/binding/

## Deploy script

Generate `deploy.sh` using the [reference implementation](https://github.com/just-mitch/private-notebook/tree/main/example) as a guide. Key steps:

1. `uv run marimo export html-wasm notebook.py -o dist --mode run --include-cloudflare --force --no-sandbox`
2. Write `wrangler.jsonc` with `run_worker_first: true` and `binding: "ASSETS"`
3. Write `index.js` with basic auth checking `env.NOTEBOOK_PASSWORD`
4. `npx wrangler deploy`
5. `echo $NOTEBOOK_PASSWORD | npx wrangler secret put NOTEBOOK_PASSWORD`

Password is read from `.env` (sourced at top of script).

### Important flags

- **`--no-sandbox`** — suppresses the interactive prompt "Run in a sandboxed venv?" that blocks scripted deploys. The flag is `--no-sandbox`, not `--sandbox false`.
- **`--force`** — overwrites existing dist directory.
- **`--include-cloudflare`** — generates the dist structure for Cloudflare. Note: this also generates root-level `index.js` and `wrangler.jsonc` that do NOT include auth or `run_worker_first` — the deploy script must overwrite them.

### TLS issues behind corporate proxies

If `npx wrangler` fails with `UNABLE_TO_GET_ISSUER_CERT_LOCALLY`:

```bash
# Quick workaround
export NODE_TLS_REJECT_UNAUTHORIZED=0

# Better fix if you have the CA cert
export NODE_EXTRA_CA_CERTS=/path/to/corporate-ca.pem
```

## Auth pattern

The Worker checks `Authorization: Basic ...` header against a Cloudflare secret. Username is ignored; only password is validated. The browser prompts automatically via `WWW-Authenticate: Basic realm="Notebook"`.

For per-user auth, use Cloudflare Access (Zero Trust) instead of basic auth.

## .gitignore additions

Single notebook:
```
.env
dist/
index.js
wrangler.jsonc
```

Multi-notebook:
```
.env
dist-*/
index-*.js
wrangler-*.jsonc
```

Also gitignore the root-level `index.js` and `wrangler.jsonc` that `--include-cloudflare` generates, since they lack auth config.
