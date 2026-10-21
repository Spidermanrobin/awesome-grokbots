# Maintenance notes

The editorial source is `data/`. Generated files must never be manually patched.
`web/` contains site code; `i18n/` contains UI strings and localized README prose.
Builds never use the current time, contact external services, or infer review tiers.
They derive dates and counts from source records and can be checked without writing.

The initial sweep checked 61 candidates with HTTP GET, a browser User-Agent, redirects,
and a 25-second timeout. Sixty returned HTTP 200. The `mrlynn/grok-bot-getting-started`
guide returned 404 and was excluded before publication. `seed-link-audit.json` records
all responses and acceptance decisions. It is an immutable historical audit, not an
input to the builder. `data/retired.yaml` starts empty because the rejected seed was
never published. Later 404/410s move there with the row's attribution intact.

Active inventory at seeding: 41 bots, 12 skills/plugins/MCP, 7 guides, 0 weekly picks.
Metadata licenses: 55 CC0-1.0, 5 CC-BY-4.0. All entries are listed. Bot content language
is unspecified (`und`) where the source gives no language declaration; translated
catalog reviews do not imply a localized bot interface.

The daily checker follows redirects using GET (HEAD behavior can differ). A response
below 400 counts as reachability, unless the server explicitly marks a challenge.
Only 404 and 410 can retire a resource. Every other unsuccessful response counts as
blocked or error; if their combined share exceeds 25%, the entire sweep aborts before
writing dates, catalog rows, picks, or a report. This is tested at the 25% boundary.
Redirects to login or generic landing pages may still respond 200; HTTP checks cannot
establish whether a bot works. Periodic manual reviews should catch semantic drift.

Retiring a picked entry also removes its ID from picks, so generation cannot leave
stale weekly links. Reinstatement requires a maintainer to move the row back to its
appropriate source file after a new successful check. The checker does not import
new entries, rewrite authors, promote tiers, or automatically revive retired entries.

GitHub deployment requires replacing the `OWNER` placeholders, selecting the real
default branch, and enabling Actions-based Pages. No deploy credentials, API keys,
analytics, external fonts, or third-party runtime scripts are needed. Browser testing
is optional tooling; the build itself needs only the three packages in requirements.txt.
