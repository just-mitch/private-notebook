---
name: deploying-marimo-to-cloudflare
description: Deploys a marimo notebook to Cloudflare Workers as an interactive WASM app with HTTP basic auth password protection. Use when the user wants to publish, deploy, or share a marimo notebook on Cloudflare, or protect a deployed notebook with a password.
---

# Deploying marimo to Cloudflare Workers

## Project layout

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

## Data files in WASM

`mo.notebook_location()` returns a URL in WASM, not a filesystem path. Files in `public/` are bundled automatically, but must be fetched over HTTP:

```python
_path = mo.notebook_location() / "public" / "data.csv"
_path_str = str(_path)

if _path_str.startswith("http"):
    from urllib.request import urlopen
    _reader = csv.DictReader(io.StringIO(urlopen(_path_str).read().decode("utf-8")))
else:
    _reader = csv.DictReader(Path(_path_str).open())
```

This is the only non-obvious pattern. Everything else follows standard marimo and Cloudflare Workers conventions.

## Deploy script

Generate `deploy.sh` using the [reference implementation](https://github.com/just-mitch/private-notebook/tree/main/example) as a guide. Key steps:

1. `uv run marimo export html-wasm notebook.py -o dist --mode run --include-cloudflare --force`
2. Write `wrangler.jsonc` pointing assets at `./dist`
3. Write `index.js` with basic auth checking `env.NOTEBOOK_PASSWORD`
4. `npx wrangler deploy`
5. `echo $NOTEBOOK_PASSWORD | npx wrangler secret put NOTEBOOK_PASSWORD`

Password is read from `.env` (sourced at top of script).

## Auth pattern

The Worker checks `Authorization: Basic ...` header against a Cloudflare secret. Username is ignored; only password is validated. The browser prompts automatically via `WWW-Authenticate: Basic realm="Notebook"`.

For per-user auth, use Cloudflare Access (Zero Trust) instead of basic auth.

## .gitignore additions

```
.env
dist/
index.js
wrangler.jsonc
```
