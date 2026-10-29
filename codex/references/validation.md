# Validation contracts

These scripts support the bundled browser runtime. Native engines need native import/run/export checks. Asset-only work needs asset inspection, not a mandatory browser scene.

## Dependencies and Windows

Use Python 3.10+ with Pillow and NumPy. `doctor.py` reports SciPy and video tools separately. Scripts never install dependencies globally. Setup preserves existing code, references are changed only when explicitly supplied. Node must support the JavaScript used by the tools; use the available maintained runtime and record its version with the test result.

Browser commands import `runtime.mjs`, which resolves Playwright as a package, avoiding URL-to-path conversion errors. Set `PLAYWRIGHT` to an existing package directory when it is outside scripts/node_modules. Set `REF2GAME_BROWSER` to a specific browser executable when needed. Windows falls back to installed Chrome/Edge if the Playwright Chromium executable is absent. Verify with `browser-check.mjs`; this is not proof of GPU capability in a game.

`serve.mjs` uses loopback, a free port by default, and checks requested paths remain inside the served directory. An explicitly requested occupied port fails clearly. Close the server process after the preview is no longer needed.

## QA scope

Example project settings:

```json
{
  "mode": "slice",
  "fidelity": "exact",
  "qa": {
    "required": ["states", "ui", "anchors"],
    "not_applicable": ["rig"]
  }
}
```

`states` is always required by browser QA; `exact` also requires a `match` state. Other categories are `ui`, `anchors`, `motion`, `rig`, `anim`. Set requirements based on the actual scene, not a generic maximum checklist. `not_applicable` is an explicit design decision; missing instrumentation is `not_tested`, not proof a check is inapplicable. Required and inapplicable categories cannot overlap.

`SCENE.QA()` needs at least one named state with finite `state.t`; names must be unique filesystem-safe identifiers. Include worst-case HUD data. Cycle, loop and transition sequences need multiple frames. See engine.md for full trace shapes and animation.md for rig-specific measurements.

```text
node "<skill>/scripts/qa.mjs"
node "<skill>/scripts/qa.mjs" --only ui --require ui
```

`--require` adds requirements, never removes configured ones. Restricting `--only` cannot silently bypass required coverage. The JSON report includes counts, warnings, failures and coverage statuses. A global failure conservatively marks performed categories failed; consult individual messages for the cause. Optional uninstrumented systems remain visibly not tested. Review warnings even when the exit status is zero.

## Interaction assertions

`livecheck.mjs` waits for `__ready` and sizes its viewport from the game's canvas. It starts with cleared session storage. Scenarios execute sequential actions and wait for expected conditions to become true.

```json
{
  "steps": [
    {"click": [560, 420]},
    {"expect": "SCENE.state.got[0] >= 0", "label": "click collects the first item"},
    {"key": "KeyR"},
    {"expect": "SCENE.state.got.every(x => x === -1)", "label": "restart resets collection"}
  ]
}
```

This example applies to the blank template; author expectations for the actual game. Supported steps: `key` plus optional `action` (`press`, `down`, `up`), `click`, `move`, `down` coordinate pairs in game pixels, `up: true`, `wheel` signed units, `wait` milliseconds, and `expect` JavaScript with optional `label`. Use local trusted test files: expressions execute in the page.

```text
node "<skill>/scripts/livecheck.mjs" --scenario study/playcheck.json
node "<skill>/scripts/livecheck.mjs" --keys "ArrowRight:down@0,ArrowRight:up@1" --assert "SCENE.state.x > 100"
node "<skill>/scripts/livecheck.mjs" --smoke
```

An assertion must return boolean `true` within the timeout; `false` or evaluation failure fails the run. No assertions fails by default. `--smoke` explicitly permits a load-only run and leaves functional status `not_tested`. `--eval` is diagnostic and does not certify behavior. Use `--timeout 5000` to change assertion wait time.

For hot reload use `--reload --reload-fields got,score` with actual stable state fields. The check pauses through the UI, changes sim.js's timestamp, waits for a new document and compares the fields exactly. It needs the current template's read-only `__REF2GAME_TEST__.snapshot()` hook and `__reloadWatchReady`. It deliberately fails on missing fields/hooks. This changes the file timestamp, not contents. Do not run against a packed static build, which disables reload.

FPS and p95 frame interval are reported with browser version. `--minfps` adds an explicit performance threshold; it is not a substitute for behavior assertions. A passing browser scenario does not establish mobile input support unless that input was tested.

## Skill regression suite

From a workspace (test artifacts are written under its work/ref2game-tests directory):

```text
python "<skill>/scripts/test_workflow.py"
python "<skill>/scripts/test_workflow.py" --browser
node "<skill>/scripts/test-runtime.mjs"
```

The core suite checks idempotence, asset-only scope, archive completeness, path rejection and output preservation. Browser checks cover the three templates, empty/missing QA coverage, false assertions, collection/pause/restart, hot reload and an extracted playable archive. It uses an available real browser; it does not generate images or certify artistic quality.
