# deploying-marimo-to-cloudflare

An agent skill for deploying [marimo](https://marimo.io) notebooks to Cloudflare Workers as interactive WASM apps, protected with HTTP basic auth.

## Install the skill

```bash
npx skills add just-mitch/private-notebook
```

## What it does

When triggered, the skill instructs your coding agent to:

1. Export a marimo notebook to WASM via `marimo export html-wasm --include-cloudflare`
2. Inject a Cloudflare Worker with basic HTTP password auth
3. Deploy with `wrangler deploy` and set the password as a Cloudflare secret

It also covers the non-obvious gotcha: `mo.notebook_location()` returns a URL (not a file path) in WASM, so data files in `public/` must be fetched over HTTP.

## Example

The [`example/`](example/) directory contains a working project you can deploy as-is:

```bash
cd example
uv sync
echo 'NOTEBOOK_PASSWORD=changeme' > .env

# edit locally
uv run marimo edit notebook.py

# deploy
./deploy.sh
```

## Repo structure

```
skills/
  deploying-marimo-to-cloudflare/
    SKILL.md                       # the skill
example/
  notebook.py                      # sample marimo notebook
  deploy.sh                        # reference deploy script
  public/sample.csv                # sample data
  pyproject.toml
```
