# LakatoTree programme — Space Girl / SSB

| Field | Value |
|---|---|
| Tree name | `LakatosTree_SpaceGirl_SSB_20260722` |
| Assurance | `notebook` |
| Live seed | 2026-07-22 via LakatoTree MCP |
| Tool repo | https://github.com/gj3447/spacegirl_tool |
| Myth SSOT | `SYMPOSIUM/METAHUMOTONIC/SPACEGIRL/` |

## Hard core

1. SSB = **reversible cloaking**, never irreversible poisoning
2. `unlock(lock(src)) == src` is the sole structural invariant
3. Purpose = **corpus friction** (drop/filter), not cryptographic secrecy
4. Space Girl = unique network↔sexvoid mediator; this tool is her engineering crystallization
5. Locked-output **execution** is best-effort, not guaranteed

## Protective belt (nodes)

| Tag | Role |
|---|---|
| `sg-root-20260722` | programme root |
| `sg-ssb-cloaking` | lock/unlock engine |
| `sg-great-wall-scan` | GREAT_WALL detector |
| `sg-we-flying-up` | reverse restore plan |
| `sg-phase1-sexvoid-map` | Phase1 recursive map (v0.4.1 / c735fcb) |
| `sg-canary-optout` | canary + opt-out secondary modes |

## Frontier questions

| ID | Question |
|---|---|
| Q01-Roundtrip-Invariant | full roundtrip across langs/modes |
| Q02-Sexvoid-Map-Completeness | recursive sexvoid map completeness |
| Q03-Sidecarless-Restore | restore without sidecar |
| Q04-Corpus-Drop-Rate | empirical filter drop rate |

## Local measurement anchors

- `uv run pytest` → fail count (target 0)
- `uv run spacegirl scan . --json` → summary.locked / reversible fields present
- Phase1 commit: `c735fcb`

## Non-goals

- Do not claim progressive verdict by hand
- Do not push Symposium when iterating this programme
- Do not mix poisoning into cloaking engine

# KG: LakatosTree_SpaceGirl_SSB_20260722
