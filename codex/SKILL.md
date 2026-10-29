---
name: ref2game
description: Build or refine 2D game assets, playable prototypes, or polished game slices from screenshots, gameplay video, or concept art. Preserve the requested visual style, gameplay constraints, and target engine; inspect the resulting assets and test playable outputs.
---

# ref2game: reference to playable 2D work

Turn a visual reference into the result the user requested. Choose the smallest workflow that delivers it. Keep source art, prompts and code editable, and distinguish visual quality from verified gameplay. Detailed references below are conditional recipes, not requirements to add features.

## Choose the scope

Infer the mode from the request and existing project. Ask only when a missing decision materially changes the result. Continue independent work while an answer is pending; do not repeatedly ask whether to finish already authorized work.

| Mode | Deliver | Required evidence |
|---|---|---|
| `assets` | Sprites, tiles, backgrounds or UI images with a manifest | Dimensions, alpha, palette/grid when applicable; visual inspection at intended display size |
| `prototype` | A playable core loop with the requested controls | A real frame and input actions with expected state changes; restart and other promised behavior |
| `slice` | The agreed polished scene with coherent art, applicable animation and sound | Prototype checks plus relevant visual, motion and performance checks; extracted build tested |

Assets-only work does not require a game server, hero, rig or playable scene. A prototype may use clearly labelled placeholders until its requested art is ready. Never describe placeholders as completed production art.

Preserve the user's target engine and existing project. The bundled setup, renderer, QA and packaging scripts support the bundled **WebGL2 browser template**. For Godot, Pyxel or another engine, reuse reference study, art and design principles, then use that engine's project/import/run/export workflow and validate there. Do not build an intermediate web game unless it serves the requested result. Native engine adapters are not bundled; do not claim an export is verified without running it.

## Study and acceptance contract

Inspect stills with `view_image`; for video, use `study.py probe` and a contact sheet when FFmpeg and SciPy are available. Read `references/study.md` and only the relevant sections of `styles.md` and `genres.md`.

Record a short `study/PLAN.md`:

- Mode, target engine, core action and controls, deliverables.
- `fidelity: style` for stylistic adaptation or `exact` for reproducing the reference composition. Resolve this from the user's wording. Exact mode requires a staged `match` frame.
- Invariants: camera, grid, character identity, layout, palette or other features that must survive edits; permitted changes.
- Asset order, intended display sizes and animation technique per moving object.
- Observable acceptance scenarios and applicable QA categories. Include failure/restart/pause/persistence only where the game supports or promises them.

Write the concise measured style bible in `art/style_bible.txt`. Use `compare.py` for crops, palette and layout differences when applicable. Its measurements guide inspection; they are not a universal similarity or quality score.

## Portable browser setup

`<skill>` is this folder; quote paths containing spaces. Use one Python interpreter with Pillow and NumPy throughout. `doctor.py` reports dependencies without installing anything. SciPy supports study/comparison; FFmpeg/ffprobe support video. Missing optional tools do not block unrelated work. Prefer bundled workspace runtimes when available, or a project-local environment.

```text
python "<skill>/scripts/doctor.py"
python "<skill>/scripts/setup.py" "<project>" --ref "<reference>" --genre side --mode prototype
```

`--genre side|top|blank` selects the starting browser template. `--mode assets` creates only art/study/configuration, with prepared images under `assets/textures`. Existing projects keep their settings and code. `--refresh-engine` intentionally replaces only gl.js and lib.js; use it only for a requested engine refresh after preserving changes.

From a playable project's root:

```text
node "<skill>/scripts/browser-check.mjs"
node "<skill>/scripts/serve.mjs"
```

The server binds loopback and prints its actual URL after binding a free port. Show it using `open_in_codex` when available. Keep the server process alive for the preview; do not imply its lifetime is permanent. Shell wrappers remain for older Unix workflows.

The browser tools load local Playwright, or the package directory set in `PLAYWRIGHT`. `REF2GAME_BROWSER` can select an installed browser executable; Windows can also use an installed Chrome/Edge when bundled Chromium is missing. Run the browser check before claiming readiness. See `references/validation.md` for commands and test contracts.

## Art workflow

Use the session's built-in imagegen for raster generation and creative edits. `gen.py` prepares requests and imports actual returned files; it does not generate. Read `references/generators.md` for tool arguments and `art.md` for asset guidance.

1. Inspect the reference and any edit target. Write the asset prompt, preserving the style bible and stated invariants.
2. `gen.py check`, then `gen.py prepare NAME art/prompts/NAME.txt` with role-labelled references as needed.
3. Call the available imagegen tool using its current schema. Use local reference paths or the smallest supported recent-image count containing every target, never both. Do not invent exact-size, seed or model parameters. Follow the tool's image-display instructions.
4. Inspect the returned image, then `gen.py import NAME <actual-returned-path>`. Use `--replace` only for an intended replacement; backups are retained.
5. Slice and prepare textures, then inspect them on their actual background at display size. Update texture/display-size mapping together when integrating into a live scene.

The first useful asset doubles as the capability check. Do not promise pricing, quotas, timing or generator availability. If generation is unavailable, report the limitation and continue useful authorized work without claiming completed art. Parallel generation is optional and only when the tool supports it.

Keep `art/gen` as prepared source truth and `art/raw` as untouched generator output; do not fix only derived textures. For pixel art, explicitly set target dimensions, palette and grid, then inspect the actual rendered frame. Alpha validation alone does not prove that an image looks correct.

## Build and animate proportionally

For the browser template, preserve the sim/scene contracts in `references/engine.md`: deterministic simulation, level data, rendering from time and state, and a replayable attract demonstration where useful. Shape controls and collision on placeholders before spending time polishing decorative systems.

Choose animation by style and purpose: sprite sheets for authored pixel poses, cut-out rigs for articulated art, procedural motion for suitable effects or segmented actors, and static art where appropriate. Read `animation.md` only for the selected technique. Joint traces and rig checks apply to rigs; they are not prerequisites for cards, icons or every NPC. Judge an action by readable intent and contact, not by the number of moving parts.

Use `gamefeel.md` and `effects.md` for systems the game actually needs. Preserve readability and user invariants when adding decoration, camera movement, particles or ambient life.

## Verify and iterate

Read `references/validation.md`. For playable browser projects:

1. Run `qa.mjs` on representative states; exact fidelity also requires `match`. Required categories are declared in `ref2game.json`. A pass with missing required coverage is invalid.
2. Run `livecheck.mjs --scenario <file>` or behavior `--assert` checks. A `--smoke` run proves only loading/input execution; `--eval` merely collects diagnostic values.
3. Inspect screenshots and, for animation, sampled cycle frames. Verify the defects the scripts cannot judge visually.
4. Review the applicable work at a useful gate, batching related assets. Use an independent critic subagent for substantial visual/gameplay reviews when delegation is available; otherwise label self-review. Critics are read-only reviewers. Collect their results before final delivery.

Use one review pass per meaningful gate by default and at most three rounds per subject within the authorized scope. Fix acceptance failures; do not stop unfinished work merely because a review round ended. If the agreed result is complete, deliver it with minor gaps disclosed. Ask only when further polish expands scope or requires a consequential unresolved choice. See `references/critics.md`.

After a reported defect, reproduce it, fix its source and add a focused regression check when useful. Store project-specific lessons in `study/PITFALLS.md`; do not silently change the installed skill during unrelated game work.

## Package and deliver

```text
python "<skill>/scripts/pack.py" --name my-game --zip
```

The packer preserves all generated sheets and a complete editable art/code project. It rejects unsafe names and preserves existing output unless `--replace` targets a marked ref2game build. See `references/delivery.md` for contents and extracted-build verification. For other engines use their export path.

Deliver the playable URL when applicable, actual files/archive, controls, verified scenarios, visual evidence and known gaps. Separate `passed`, `failed`, `not_applicable` and `not_tested`. Do not equate successful packaging, a screenshot, critic scores or syntax checking with functional acceptance. Video is optional, only when requested.

## Reference and tool routing

- Study/style/layout: `study.md`, `styles.md`, `genres.md`; `study.py`, `compare.py`, `sheet.py`.
- Generation and asset preparation: `generators.md`, `art.md`; `gen.py`, `slice.py`, `prep.py`, `variantfix.py`.
- Articulated animation: `animation.md`; `rigcut.py`, `partrig.py`, `jointr.py`, `softbones.py`.
- Browser simulation/rendering: `engine.md`, `effects.md`, `gamefeel.md`; `render.mjs`, project `live/tune.cjs`.
- Verification/delivery: `validation.md`, `critics.md`, `delivery.md`, relevant `pitfalls.md` entries; `qa.mjs`, `livecheck.mjs`, `pack.py`, `test_workflow.py`.
