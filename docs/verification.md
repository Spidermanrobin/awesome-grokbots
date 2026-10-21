# Initial build verification

Verified on 2026-10-21:

- 60 active entries: 41 bots, 12 skills/plugins/MCP, 7 guides.
- Every entry URL matches its attributed read-only reference data exactly.
- All 60 active URLs returned HTTP 200 in both the seed verification and the final dry sweep.
- One candidate guide returned 404 and was excluded. No active entry was retired.
- 55 CC0-1.0 rows and 5 attributed CC-BY-4.0 rows; all tiers are listed.
- Schema validation and deterministic generated-output checks passed.
- Ten regression tests passed, including exact circuit-breaker boundaries, no writes on a trip,
  dry-run behavior, retirement and picks cleanup, attribution, duplicate handling, and new locales.
- Playwright Chromium checks passed for search, combined filters, empty results, tags, sorting,
  all three languages, persisted locale, attribution display, and a simulated weekly selection.
- No browser page errors or horizontal overflow at 390, 768, or 1440 pixels.
- `docs-preview.png` is the actual local-site screenshot at 1440×1000.

Commands used:

```sh
.venv/bin/python scripts/validate.py
.venv/bin/python scripts/build.py
.venv/bin/python scripts/build.py --check
.venv/bin/python scripts/check_links.py --dry-run
.venv/bin/python -m unittest discover -s tests
PLAYWRIGHT_BROWSERS_PATH=/tmp/grok-playwright .venv/bin/python scripts/preview.py
```

The managed environment mounts the original `.git` directory read-only. Staging there
failed with `Unable to create .git/index.lock: Read-only file system`. The complete
project snapshot was therefore committed into a separate local Git object store under
`/tmp` and exported as `awesome-grok-bot.bundle` in the project root. The bundle is
self-contained and intentionally excluded from its own commit. No remote was added
and nothing was pushed. The original repository's HEAD and index remain unchanged.

Once the original `.git` is writable, the commit can be imported without adding a remote:

```sh
git bundle verify awesome-grok-bot.bundle
git fetch ./awesome-grok-bot.bundle master:refs/heads/built-catalog
git log --stat built-catalog
```

The maintainer can then select `built-catalog` as the working branch after accounting
for the existing working-tree files. The OWNER placeholders remain intentionally unset.
