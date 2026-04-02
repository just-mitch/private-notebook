# private-notebook

Example repo: publish a [marimo](https://marimo.io) notebook to a Cloudflare Worker with basic HTTP password protection.

## Setup

```bash
uv sync
echo 'NOTEBOOK_PASSWORD=changeme' > .env
```

## Local dev

```bash
# edit code
uv run marimo edit notebook.py

# view
uv run marimo run notebook.py
```

## Deploy

```bash
./deploy.sh
```

Exports the notebook as WASM, injects basic auth into the Cloudflare Worker, deploys, and sets the password as a secret. Rerun to update.

## How it works

- `public/` — static files (e.g. `sample.csv`) bundled into the WASM export
- `notebook.py` — uses `mo.notebook_location()` so data paths resolve both locally and in WASM
- `deploy.sh` — handles export, auth injection, and `wrangler deploy` in one step
