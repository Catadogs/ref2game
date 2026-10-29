# Codex modernization and validation

Updated: 2026-10-29. Upstream: [studioigor/ref2game](https://github.com/studioigor/ref2game).

## Scope

Only the Codex skill and repository documentation are modernized. Original author attribution, MIT license, examples and Claude edition are retained.

The skill entrypoint decreased from 2,793 to 1,416 whitespace-delimited words. Conditional workflows replace universal rig and exact-match requirements. The browser runtime shares portable dependency resolution and a bounded localhost server. QA distinguishes required coverage, skipped work and explicit non-applicability. Behavior assertions and reload-state verification supplement frame inspection.

The packer preserves all generated source sheets, editable art/code, requests and prompts. Outputs are prepared in a temporary child directory before replacement. Unsafe output names, source-directory output locations and unmarked existing directories are rejected. Checksums describe the archive contents.

## Verified locally

Windows, Python 3.12, Node.js 24.14.0, Playwright 1.62.1 and installed Chrome 156.0.8078.48:

- **13 workflow tests passed**, covering idempotent setup, assets-only preparation/packing, source and checksum preservation, unsafe names, output boundaries, existing-output preservation, failed-build preservation, all three templates, gameplay/reload/extracted-build scenarios, empty and missing QA coverage, false assertions, explicit smoke behavior, and canvas-size checks.
- **6 server checks passed:** GET, HEAD, missing files, encoded traversal, unsupported methods and an occupied port.
- All 16 JavaScript/MJS/CJS files passed syntax checking; Python scripts passed syntax parsing.
- The skill structure validator passed.
- An extracted-build frame was visually inspected after collecting an item; the counter displayed 01.

These are local results, not a claim of hosted CI execution. Reproduce with `scripts/test_workflow.py --browser` and `scripts/test-runtime.mjs` as documented in the README. Browser package/executable availability must be configured in the target environment.

## Limits and compatibility

New image generation, all articulated rig combinations, native engine exports, macOS and Linux execution were not exercised in this validation. Browser smoke results alone do not certify gameplay or artistic quality.

`livecheck.mjs` now requires behavior assertions unless `--smoke` is explicit. `--eval` remains diagnostic. Reload checks require selected stable fields and the current template hooks. Packaging replacement requires `--replace` and a marked previous build; old unmarked output is preserved. See `codex/references/validation.md` and `codex/references/delivery.md` for the current contracts.
