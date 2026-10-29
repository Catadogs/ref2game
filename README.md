# ref2game — Codex workflow fork

Turn screenshots, gameplay video and concept art into 2D game assets, playable prototypes or polished scenes.

This is a fork of [studioigor/ref2game](https://github.com/studioigor/ref2game). The original engine, artwork examples and skill are by **studioigor**, retained under the [MIT license](LICENSE). This fork modernizes the **Codex edition in `codex/`**. The Claude edition remains upstream's original workflow.

[Русский](README.ru.md) · [Change and validation details](FORK.md) · [Codex skill](codex/SKILL.md)

## Install in Codex

Ask your agent:

```text
Install the ref2game skill from https://github.com/Catadogs/ref2game using the codex/ folder.
```

Then invoke `$ref2game` with a reference and the requested result. For manual installation, copy the entire `codex/` directory to your skills directory as `ref2game`, preserving an existing installation first.

## What changed

- Separate **assets**, **prototype** and **slice** workflows; no compulsory game server for asset packs.
- Preserve the user's engine choice and distinguish stylistic adaptation from exact composition matching.
- Select sprite animation, articulated rigs or procedural motion according to the task.
- Portable Python setup and Node preview server; Windows paths with spaces work.
- Explicit QA coverage and real interaction assertions, including selected state fields across hot reload.
- Packaging preserves source sheets, prompts, configuration and editable code, with file checksums and guarded replacement.
- A regression suite exercises all three browser templates and an extracted playable archive.

## Runtime requirements

For the bundled browser workflow: Python 3.10+ with Pillow and NumPy, a maintained Node.js runtime, and Playwright. SciPy is needed for study/comparison tools; FFmpeg and ffprobe are needed for video. The tested environment used Python 3.12, Node 24.14.0, Playwright 1.62.1 and installed Chrome on Windows.

Use a project-local Python environment. `doctor.py` reports dependencies without installing them. To install the pinned browser tools, run `npm ci` from `codex/scripts`; Playwright's Chromium can be installed with `npx playwright install chromium`. An existing Playwright package can instead be selected with `PLAYWRIGHT`, and a browser executable with `REF2GAME_BROWSER`. Windows can fall back to installed Chrome/Edge.

```text
python codex/scripts/doctor.py
node codex/scripts/browser-check.mjs
python codex/scripts/setup.py "my-game" --genre blank --mode prototype
```

Run `serve.mjs` from the generated project directory, using the absolute path to the skill script. It prints the actual local preview URL. Use `--mode assets` to prepare an asset-only workspace.

## Tests

Run from a writable workspace; test artifacts are placed under its `work/` directory:

```text
python codex/scripts/test_workflow.py --browser
node codex/scripts/test-runtime.mjs
```

See [FORK.md](FORK.md) for verified results and limits. The bundled scripts target WebGL2; native Godot/Pyxel exporters are not included. No generated-art quality claim follows from the automated tests.

## Original project

The original reference-driven game workflow, examples and design are available from [studioigor/ref2game](https://github.com/studioigor/ref2game) and [@studioigor](https://www.youtube.com/@studioigor). Original examples remain in this repository. The `claude/` edition is retained without these Codex-specific changes.
