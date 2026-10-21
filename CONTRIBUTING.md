# Contributing

[简体中文](CONTRIBUTING.zh-CN.md) · [日本語](CONTRIBUTING.ja.md)

Suggest one useful, real resource at a time. Prefer finance and investing, research,
content and social publishing, video, and the skills or guides that support them.
Use the issue forms or send a pull request with the source and a concise reason.

1. Edit `data/bots.yaml` for public `https://x.ai/bot/<id>` shares, `data/skills.yaml`
   for skills/plugins/MCP, or `data/guides.yaml` for guides and use cases.
2. Copy the exact URL and author from your source. Use a known repository account
   for repository resources; do not infer a person's identity. `author.handle`
   may be null if genuinely unavailable. Set `language: [und]` when the source
   does not establish the content language; UI translations do not establish it.
3. Follow [the schema](schema/entry.schema.json). IDs and URLs must be unique across
   active and retired entries. Use one primary category and 1–6 short tags.
   Add one-line English, zh-CN, and Japanese reviews (220 characters each).
   New UI languages fall back to English reviews until translations are provided.
4. Preserve the metadata source repository and row license. CC-BY-4.0 rows also need
   `source.attribution` and `source.changes`. A linked project's code license is
   separate. See [LICENSE-DATA](LICENSE-DATA) and [CREDITS](CREDITS.md).
5. Open the link and run an HTTP GET with redirects and a browser User-Agent.
   New entries must return <400. Add quoted ISO dates for `added` and `last_checked`,
   `status: active`, and `tier: listed`. Do not count HTTP checks as workflow tests.
6. Run the commands below, inspect the generated diff, and include generated files.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/validate.py
python scripts/build.py
python scripts/build.py --check
python scripts/check_links.py --dry-run
python -m unittest discover -s tests
python -m http.server 8000 --directory site
```

`listed` means a reachable resource with attributable metadata. `tested` requires a
maintainer's recorded task, setup, date, observed result, and limitations in a PR or
`docs/reviews/<id>.md`. `featured` additionally requires a maintainer's reason for
recommending it. No seed entries are tested or featured. The badge is awarded only
with a featured review; copying the badge does not create that status.

Weekly selections live in `data/picks.yaml` as `{week: "YYYY-MM-DD", entries: [id]}`.
Use a Monday date and 1–6 unique active IDs; do not duplicate entry metadata.
Picks do not automatically change tiers. Retiring a selected entry removes its
reference and removes a week if no selections remain. Seeds have no picks.

The link checker is read-only by default. `--write` updates successful check dates
and moves only HTTP 404/410 rows to `data/retired.yaml`. 401/403/429, server errors,
and request errors never retire a row. More than 25% blocked/errors aborts the whole
sweep before any write, including reports. Exit codes: 0 clean or applied, 1 dead
links found in a dry run, 2 circuit breaker. A dry run writes no files even with
`--report`. Below the breaker, blocked/error rows keep their previous check date.

Edit `web/` for the site; `site/`, `dist/`, `README*.md`, and `llms.txt` are generated.
Add one `i18n/<locale>.yaml` with the same keys as English to add a UI language and
README; no Python or JS change is needed. Locale-specific contributor guides are
handwritten and may be added separately. Site search supports `/` to focus and
Escape to clear; category, type, tier, tag, and text filters combine.

For a browser check, install the optional tooling (not needed for normal builds):

```sh
pip install playwright
python -m playwright install chromium
python scripts/preview.py
```

`preview.py` starts its own local server, exercises desktop/mobile filters and
languages, and captures `docs-preview.png` at 1440×1000.

branch (or update workflow branch filters), and enable GitHub Pages with
GitHub Actions. The daily workflow needs repository Contents write permission.
Its generated commit triggers Pages through `workflow_run`, since a default
`GITHUB_TOKEN` push does not trigger another push workflow. No remote is required
for local development. Follow the [code of conduct](CODE_OF_CONDUCT.md).
